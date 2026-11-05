"""用例编写任务的后台执行：产物映射、入库来源与失败兜底。"""

from __future__ import annotations

import threading

from types import SimpleNamespace

import pytest

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.case_manager.models import TestDefinition as Definition
from backend.apps.task_list import api, task_runner
from backend.models.constants import TaskKind
from engines.agents.workflow.case_artifact import (
    Artifact,
    ArtifactCase,
    ArtifactScenario,
    ArtifactState,
    ArtifactStep,
    ArtifactTransition,
)
from engines.agents.workflow.case_artifact_facts import FactReport

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _artifact() -> Artifact:
    """一份可入库的最小产物。"""
    return Artifact(
        states=(
            ArtifactState("S1", "待机", True, "截图：模式灯灭", "设备待机"),
            ArtifactState("S2", "运行态", True, "截图：模式灯亮", "单击 POWER 后进入运行态"),
        ),
        transitions=(
            ArtifactTransition("T1", "S1", "S2", "单击 POWER", "", "", "单击 POWER 后进入运行态"),
        ),
        scenarios=(
            ArtifactScenario(
                "SC-001", "开灯", ("S1", "S2"), ("T1",), "主流程", "单击 POWER 后进入运行态"
            ),
        ),
        cases=(
            ArtifactCase(
                "TC-001",
                "单击开机",
                "SC-001",
                "S1",
                (ArtifactStep("单击 POWER", "S2", ""),),
                (),
                ("场景法",),
                "P1",
                "单击 POWER 后进入运行态",
            ),
        ),
        diagram="stateDiagram-v2",
        report="状态 2 / 迁移 1 / 场景 1 / 用例 1",
    )


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
    assert result["artifact"]["cases"] == []
    assert result["facts"] == {"blocking": [], "warnings": []}


def test_run_case_authoring_honours_preset_cancel_event():
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent)
    event = threading.Event()
    event.set()
    result = task_runner._run_case_authoring(task, event)
    assert result["status"] == "cancelled"
    assert result["passed"] is False


def test_run_case_authoring_maps_artifact_result(monkeypatch):
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent, created_by="7")
    api.add_task_attachment(
        task, kind="document", filename="prd.md", body="单击 POWER 后进入运行态", sort_order=0
    )

    captured: dict[str, str] = {}
    fake_result = SimpleNamespace(
        passed=True,
        phase="completed",
        artifact=_artifact(),
        facts=FactReport(),
        document="# 测试用例\n## 三、测试用例\n| TC-001 |",
        verdicts=((True, "通过", "case_verifier_role"),),
        reason="",
        max_output_tokens=321,
    )

    async def fake_run(requirement, project_code="", version=""):
        captured["input"] = requirement
        captured["project"] = project_code
        return fake_result

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        "engines.agents.workflow.case_goal_workflow.run_case_authoring_artifact",
        fake_run,
    )

    result = task_runner._run_case_authoring(task)

    assert result["status"] == "success"
    assert result["passed"] is True
    assert result["artifact"]["counts"] == {
        "states": 2,
        "transitions": 1,
        "scenarios": 1,
        "cases": 1,
    }
    assert result["artifact"]["diagram"] == "stateDiagram-v2"
    assert result["case_import"]["status"] == "imported"
    assert result["case_import"]["path"].startswith("/cases/projects/")
    assert Definition.objects.filter(source_task_id=str(task.id)).count() == 1
    assert result["verdicts"] == [
        {"passed": True, "message": "通过", "verifier": "case_verifier_role"}
    ]
    assert "modules" not in result
    assert "truncated" not in result
    assert "单击 POWER 后进入运行态" in captured["input"]
    assert captured["project"] == "H717D"


def test_imported_steps_assert_state_names(monkeypatch):
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent, created_by="7")

    result = task_runner._import_case_artifact(task, SimpleNamespace(artifact=_artifact()))

    assert result["status"] == "imported"
    step = Definition.objects.get(source_task_id=str(task.id)).steps.first()
    assert step.action == "单击 POWER"
    assert step.assertion == "运行态"


def test_import_failure_is_reported_without_failing_task(monkeypatch):
    agent = AIAgent.objects.create(name="Agent-02", task_kind=TaskKind.CASE_AUTHORING)
    task = _task(agent, created_by="7")

    def _boom(**_kwargs):
        raise RuntimeError("数据库不可用")

    monkeypatch.setattr("backend.apps.case_manager.api.import_case_rows", _boom)
    result = task_runner._import_case_artifact(task, SimpleNamespace(artifact=_artifact()))

    assert result["status"] == "failed"
    assert result["path"] == ""
    assert "数据库不可用" in result["message"]
