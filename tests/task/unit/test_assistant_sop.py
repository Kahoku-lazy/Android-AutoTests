"""名片绑定 SOP：里程碑 YAML 接受与拒绝，解析失败不开始运行。"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant import api as assistant_api
from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.task_runner import run_task_async
from backend.apps.task_list.views import AgentTaskListAPIView, TaskSubmitAPIView
from backend.models.constants import TaskKind

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.unit]

MILESTONE = """
name: 检查桌面
steps:
  - subject: 回到桌面
    description: 停在桌面
  - subject: 打开设置
    description: 设置页可见
executor: 不该生效
""".strip()

CASE_TEXT = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
""".strip()


def _user():
    return get_user_model().objects.create_user(username=f"sop-user-{get_user_model().objects.count()}", password="pass")


def _card(suffix: str, prompt: str) -> AIAssistant:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=f"deepseek-{suffix}",
    )
    role = AIRole.objects.create(
        role_id=f"20261117{suffix}",
        name=f"配置{suffix}",
        model_config=config,
        system_prompt=prompt,
    )
    return AIAssistant.objects.create(
        assistant_id=f"20261117_{suffix}",
        display_name=f"助手{suffix}",
        marker="teal",
        role_id=role.role_id,
    )


def _submit(user, data: dict, files: dict):
    factory = APIRequestFactory()
    request = factory.post("/api/tasks/submit/", data, format="multipart")
    request.FILES.update(files)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


def test_accepts_milestone_and_ignores_role_fields(monkeypatch):
    """合法里程碑可以提交；YAML 里的角色字段不进入工作流记录。"""
    monkeypatch.setattr(api, "dispatch_device", lambda serial: None)
    executor = _card("EX1", "执行提示词")
    verifier = _card("VF1", "验收提示词")
    workflow = assistant_api.create_sop_workflow("桌面", executor.assistant_id, verifier.assistant_id)
    before = AISopWorkflow.objects.count()

    response = _submit(
        _user(),
        {"title": "跑一次", "workflow_id": workflow.id, "device_serial": "RF8N21MSW7A"},
        {"config": SimpleUploadedFile("steps.yaml", MILESTONE.encode("utf-8"))},
    )

    assert response.status_code == 200
    task = Task.objects.get(id=response.data["id"])
    assert task.task_kind == TaskKind.ASSISTANT_SOP
    assert task.device_serial == "RF8N21MSW7A"
    assert AISopWorkflow.objects.count() == before
    assert AISopWorkflow.objects.get(pk=workflow.id).executor_assistant_id == executor.assistant_id


def test_same_device_queues_and_other_device_runs(monkeypatch):
    """同一地址第二条排队；不同地址可以同时 running。"""
    monkeypatch.setattr("backend.apps.task_list.task_runner.spawn_task_thread", lambda *args: None)
    first = api.create_task(
        title="甲", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    second = api.create_task(
        title="乙", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    other = api.create_task(
        title="丙", goal="", device_serial="PHONE-B", task_kind=TaskKind.ASSISTANT_SOP
    )

    assert api.dispatch_device("PHONE-A").id == first.id
    assert api.dispatch_device("PHONE-A") is None
    assert api.dispatch_device("PHONE-B").id == other.id
    second.refresh_from_db()
    other.refresh_from_db()
    assert second.status == "pending"
    assert other.status == "running"


def test_finished_task_starts_earliest_pending(monkeypatch):
    """前序结束后，同一地址最早的 pending 被拉起。"""
    with patch("backend.apps.task_list.task_runner.spawn_task_thread") as spawn:
        first = api.create_task(
            title="甲", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
        )
        second = api.create_task(
            title="乙", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
        )
        api.dispatch_device("PHONE-A")
        spawn.reset_mock()

        api.finalize_task(first, status="failed", result="未通过")

        second.refresh_from_db()
        assert second.status == "running"
        spawn.assert_called_once_with(second.id, 0)


def test_delete_queued_task_starts_the_next(monkeypatch):
    """删除挡住队列的任务后，同地址最早 pending 被拉起。"""
    monkeypatch.setattr("backend.apps.task_list.task_runner.spawn_task_thread", lambda *args: None)
    monkeypatch.setattr("backend.apps.task_list.media_storage.get_media_storage", lambda: type("S", (), {"delete_task": lambda self, task_id: None})())
    blocker = api.create_task(
        title="挡住", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    waiting = api.create_task(
        title="等待", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    api.start_task(blocker)

    api.delete_task(blocker)

    waiting.refresh_from_db()
    assert waiting.status == "running"


def test_drain_logs_refused_dispatch(caplog):
    """排空期间不派发，并记下任务编号与设备地址。"""
    task = api.create_task(
        title="排空", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    api.begin_drain()

    assert api.dispatch_device("PHONE-A") is None

    task.refresh_from_db()
    assert task.status == "pending"
    assert f"task_id={task.id}" in caplog.text
    assert "PHONE-A" in caplog.text


def test_task_list_returns_only_workflow_rows():
    """列表只返回工作流记录，并带现存工作流名称。"""
    executor = _card("EX9", "提示词")
    workflow = assistant_api.create_sop_workflow("灯带检查", executor.assistant_id, executor.assistant_id)
    workflow_task = api.create_task(
        title="工作流", goal="", device_serial="PHONE-A", task_kind=TaskKind.ASSISTANT_SOP
    )
    workflow_task.result = api.dump_task_run_payload({"workflow_id": workflow.id})
    workflow_task.save(update_fields=["result"])
    api.create_task(title="设备", goal="", device_serial="PHONE-B", task_kind=TaskKind.DEVICE_CONTROL)
    user = _user()
    request = APIRequestFactory().get("/api/tasks/", {"workflow_id": workflow.id, "status": "pending"})
    request.user_id = str(user.id)
    force_authenticate(request, user=user)

    response = AgentTaskListAPIView.as_view()(request)

    assert response.status_code == 200
    assert [row["id"] for row in response.data["tasks"]] == [workflow_task.id]
    assert response.data["tasks"][0]["workflow_name"] == "灯带检查"
    assert response.data["workflows"] == [{"id": workflow.id, "name": "灯带检查"}]


def test_submit_without_workflow_is_rejected():
    """任务清单不再接收设备执行或用例编写创建。"""
    response = _submit(
        _user(),
        {"title": "旧入口", "device_serial": "PHONE-A"},
        {"config": SimpleUploadedFile("steps.yaml", MILESTONE.encode("utf-8"))},
    )

    assert response.status_code == 400
    assert Task.objects.count() == 0


def test_rejects_workflow_without_device():
    """工作流没有设备时拒绝，并且不建任务。"""
    executor = _card("EX0", "提示词")
    workflow = assistant_api.create_sop_workflow("缺设备", executor.assistant_id, executor.assistant_id)

    response = _submit(
        _user(),
        {"title": "空设备", "workflow_id": workflow.id, "device_serial": ""},
        {"config": SimpleUploadedFile("steps.yaml", MILESTONE.encode("utf-8"))},
    )

    assert response.status_code == 400
    assert "设备" in str(response.data)
    assert Task.objects.count() == 0


def test_rejects_case_yaml_and_missing_subject():
    """用例格式与缺字段都拒绝，并且不建任务。"""
    executor = _card("EX2", "提示词")
    workflow = assistant_api.create_sop_workflow("拒绝", executor.assistant_id, executor.assistant_id)

    case_response = _submit(
        _user(),
        {"title": "用例", "workflow_id": workflow.id, "device_serial": "RF8N21MSW7A"},
        {"config": SimpleUploadedFile("case.yaml", CASE_TEXT.encode("utf-8"))},
    )
    missing = MILESTONE.replace("description: 停在桌面", "note: 没有描述")
    missing_response = _submit(
        _user(),
        {"title": "缺字段", "workflow_id": workflow.id, "device_serial": "RF8N21MSW7A"},
        {"config": SimpleUploadedFile("bad.yaml", missing.encode("utf-8"))},
    )

    assert case_response.status_code == 400
    assert "里程碑" in str(case_response.data)
    assert missing_response.status_code == 400
    assert Task.objects.count() == 0


def test_resolve_failure_does_not_start_the_run(monkeypatch):
    """解析失败写成任务失败，并且不调用运行函数。"""
    called = {"run": 0}

    async def fake_run(*args, **kwargs):
        called["run"] += 1

    monkeypatch.setattr(
        "engines.backend_bridge.workflow.bound_sop.run_bound_sop",
        fake_run,
    )
    monkeypatch.setattr("backend.apps.task_list.task_runner.release_device_now", lambda *args: None)
    monkeypatch.setattr("engines.backend_bridge.workflow.cancel.bind_cancel", lambda task_id: None)
    monkeypatch.setattr("engines.backend_bridge.workflow.cancel.clear_cancel", lambda task_id: None)
    card = _card("EX3", "提示词")
    workflow = assistant_api.create_sop_workflow("将缺失", card.assistant_id, card.assistant_id)
    task = api.create_task(title="失败", goal="", task_kind=TaskKind.ASSISTANT_SOP)
    task.result = api.dump_task_run_payload({"workflow_id": workflow.id})
    task.save(update_fields=["result"])
    card.delete()

    run_task_async(task.id, 0)

    task.refresh_from_db()
    assert task.status == "failed"
    assert "名片不存在" in task.result
    assert called["run"] == 0


def test_detail_keeps_used_card_ids_without_copying_workflow():
    """任务详情含本次使用的两个编号，运行不增加工作流副本。"""
    before = AISopWorkflow.objects.count()
    task = api.create_task(title="详情", goal="", task_kind=TaskKind.ASSISTANT_SOP)
    task.result = api.dump_task_run_payload(
        {
            "executor_assistant_id": "20261117_EX1",
            "verifier_assistant_id": "20261117_VF1",
            "executor_run_name": "执行",
            "verifier_run_name": "验收",
        }
    )
    task.save(update_fields=["result"])

    detail = api.serialize_agent_task_detail(task)

    assert detail["executor_assistant_id"] == "20261117_EX1"
    assert detail["verifier_assistant_id"] == "20261117_VF1"
    assert detail["executor_run_name"] == "执行"
    assert AISopWorkflow.objects.count() == before


def test_task_cost_is_ledger_sum_and_skips_unpriced(monkeypatch):
    """任务费用等于账本已计价行之和；未计价行不进合计。"""
    from datetime import datetime

    from backend.apps.usage_ledger.api import record_usage

    peak = datetime(2026, 10, 8, 10, 0, 0)
    idle = datetime(2026, 10, 10, 10, 0, 0)
    record_usage(
        event_id="task:9:1",
        provider="deepseek",
        model="deepseek-flash",
        occurred_at=peak,
        input_tokens=1_000_000,
        source="task",
        execution_id="9",
    )
    record_usage(
        event_id="task:9:2",
        provider="deepseek",
        model="deepseek-flash",
        occurred_at=idle,
        input_tokens=1_000_000,
        source="task",
        execution_id="9",
    )
    record_usage(
        event_id="task:9:3",
        provider="other",
        model="",
        occurred_at=idle,
        input_tokens=1_000_000,
        source="task",
        execution_id="9",
    )

    costs, notes = api.summarize_ledger_cost(9)

    assert costs["cost_total"] == Decimal("3.00000000")
    assert notes
