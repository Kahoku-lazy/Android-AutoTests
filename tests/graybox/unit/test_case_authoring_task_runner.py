"""用例编写任务的后台执行：文档拼装、工作流结果映射与失败兜底。"""

from __future__ import annotations

import threading

from types import SimpleNamespace

import pytest

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.case_manager.models import TestDefinition as Definition
from backend.apps.task_list import api, task_runner
from backend.models.constants import TaskKind

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

CASE_DOCUMENT = """## 模块：按键（BTN）· 验收 PASS

## 一、需求原子表

| 原子ID | 来源章节 | 需求原子 | 类型 | 用户可感知 | 物理依赖 | 备注 |
|:--:|:--:|------|:--:|:--:|:--:|------|
| REQ-001 | 1 | 待机单击 POWER 开机 | 按键 | ✅ | 无 | |

## 四、测试用例

### 4.1 按键

| 用例编号 | 测试标题 | 追溯ID | 方法 | 复杂度 | 优先级 | 前置条件 | 测试步骤 | 预期结果 | 量化指标 | 校验要点 | 状态 | 执行记录 |
|------|------|:--:|:--:|:--:|:--:|------|------|------|:--:|------|:--:|:--:|
| TC-H717D-BTN-V1-001 | 待机开机 | REQ-001 | 场景流+边界值 | L1 | P1 | 设备待机 | 1) 单击 POWER<br>2) 等待 3s | 1) 模式灯亮<br>2) 3s 后熄灭 | ≤3s | 看灯态 | NOT_RUN | {} |
"""


def _task(agent: AIAgent, *, created_by: str = ""):
    return api.create_task(
        agent,
        title="H717D 家电用例",
        goal="",
        task_kind=TaskKind.CASE_AUTHORING,
        created_by=created_by,
    )


def test_run_case_authoring_without_document_fails_fast():
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent)
    result = task_runner._run_case_authoring(task)
    assert result["status"] == "fail"
    assert result["passed"] is False
    assert result["case_import"]["status"] == "skipped"
    assert "需求文档" in result["reason"]


def test_run_case_authoring_honours_preset_cancel_event():
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent)
    event = threading.Event()
    event.set()
    result = task_runner._run_case_authoring(task, event)
    assert result["status"] == "cancelled"
    assert result["passed"] is False


def test_run_case_authoring_maps_workflow_result(monkeypatch):
    monkeypatch.setenv("CASE_AUTHORING_ENGINE", "sop")
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent, created_by="7")
    api.add_task_attachment(
        task, kind="document", filename="prd.md", body="待机下开机", sort_order=0
    )

    captured: dict[str, str] = {}
    fake_result = SimpleNamespace(
        passed=True,
        phase="completed",
        document=CASE_DOCUMENT,
        verdicts=((True, "通过", "case_verifier_role"),),
        truncated=False,
        max_output_tokens=100,
        modules=(),
    )
    fake_modules = (
        SimpleNamespace(
            key="ALL",
            name="全部需求",
            start_line=1,
            end_line=1,
            text="待机下开机",
        ),
    )

    class FakeWorkflow:
        def __init__(self, writer, verifier):
            self.writer = writer
            self.verifier = verifier

        async def run(self, run_input):
            captured["input"] = run_input
            return fake_result

    async def fake_plan(*args, **kwargs):
        return fake_modules

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        "engines.agents.workflow.case_authoring_workflow.plan_case_modules", fake_plan
    )
    monkeypatch.setattr(
        "engines.agents.workflow.case_authoring_workflow.CaseAuthoringWorkflow",
        FakeWorkflow,
    )

    result = task_runner._run_case_authoring(task)

    assert result["status"] == "success"
    assert result["passed"] is True
    assert result["document"] == CASE_DOCUMENT
    assert result["case_import"]["status"] == "imported"
    assert result["case_import"]["path"].startswith("/cases/projects/")
    assert Definition.objects.filter(source_task_id=str(task.id)).count() == 1
    assert result["verdicts"] == [
        {"passed": True, "message": "通过", "verifier": "case_verifier_role"}
    ]
    assert result["modules"] == [
        {
            "key": "ALL",
            "name": "全部需求",
            "start_line": 1,
            "end_line": 1,
            "passed": True,
            "truncated": False,
            "document_length": len(CASE_DOCUMENT),
            "message": "通过",
        }
    ]
    assert result["truncated"] is False
    assert "## prd.md\n待机下开机" in captured["input"]
    assert "H717D" in captured["input"]


def test_import_failure_is_reported_without_failing_task(monkeypatch):
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent, created_by="7")

    def _boom(**_kwargs):
        raise RuntimeError("数据库不可用")

    monkeypatch.setattr("backend.apps.case_manager.api.import_case_rows", _boom)
    result = task_runner._import_case_document(task, CASE_DOCUMENT)

    assert result["status"] == "failed"
    assert result["path"] == ""
    assert "数据库不可用" in result["message"]
