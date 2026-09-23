"""任务标题 / 附件规划 JSON / 按设备调度（spec: ai-task-title-attach-dispatch）。"""

from __future__ import annotations

import json

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ai_assistant import api, engine_adapter
from apps.ai_assistant.kb_files import KbFileError, parse_task_attachment_bytes
from apps.ai_assistant.models import AIAgent
from apps.ai_assistant.serializers import TaskSubmitInputSerializer
from models.constants import AgentStatus, TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]


def _role_cfg() -> dict:
    return {
        "provider": "deepseek",
        "model_name": "deepseek-v4-flash",
        "api_key": api.encrypt_key("sk-test"),
        "base_url": "",
    }


@pytest.fixture
def platform_agent(db):
    return AIAgent.objects.create(
        name="platform",
        status=AgentStatus.ACTIVE,
        route_configs={
            "device_control": {
                "planner": _role_cfg(),
                "executor": _role_cfg(),
                "verifier": _role_cfg(),
            }
        },
        max_loops=3,
    )


def test_build_planner_user_input_keys_and_empty_attachment():
    task = SimpleNamespace(
        title="校准色温",
        goal="拖动滑块到最左",
        attachment="",
        device_serial="SER-1",
    )
    payload = json.loads(api.build_planner_user_input(task))
    assert set(payload) == {"任务标题", "任务目标", "附件文本内容", "设备ID"}
    assert payload["任务标题"] == "校准色温"
    assert payload["任务目标"] == "拖动滑块到最左"
    assert payload["附件文本内容"] == ""
    assert payload["设备ID"] == "SER-1"


def test_build_request_embeds_planner_json():
    task = SimpleNamespace(
        title="进详情",
        goal="打开应用",
        attachment="## 页",
        device_serial="SER-X",
        id=9,
    )
    agent = SimpleNamespace(
        route_configs={
            engine_adapter.ROUTE_KEY: {
                role: {
                    "provider": "deepseek",
                    "model_name": "m",
                    "api_key": api.encrypt_key("sk"),
                    "base_url": "",
                }
                for role in engine_adapter.ROUTE_ROLES
            }
        },
        max_loops=3,
        owner_id="1",
        enable_skills=False,
        prompt_planner="## p",
        prompt_executor="## e",
        prompt_verifier="## v",
    )
    req = engine_adapter.build_request(task, agent)
    data = json.loads(req.goal)
    assert data["任务标题"] == "进详情"
    assert data["附件文本内容"] == "## 页"
    assert data["设备ID"] == "SER-X"
    assert req.device_serial == "SER-X"


def test_submit_serializer_requires_title():
    ser = TaskSubmitInputSerializer(data={"goal": "做点事"})
    assert not ser.is_valid()
    assert "title" in ser.errors


def test_submit_serializer_rejects_bad_ext():
    f = SimpleUploadedFile("a.xlsx", b"x", content_type="application/vnd.ms-excel")
    ser = TaskSubmitInputSerializer(
        data={"title": "t", "goal": "g", "attachment": f},
    )
    assert not ser.is_valid()
    assert "attachment" in ser.errors


def test_parse_task_attachment_rejects_ext():
    with pytest.raises(KbFileError, match="docx"):
        parse_task_attachment_bytes("a.txt", b"hello")


def test_dispatch_same_serial_queues(platform_agent):
    a = api.create_task(
        platform_agent, title="a", goal="g1", device_serial="DEV-A", device_label="PhoneA"
    )
    with patch("apps.ai_assistant.task_runner.spawn_task_thread") as spawn:
        started = api.dispatch_device("DEV-A")
        assert started is not None
        assert started.id == a.id
        a.refresh_from_db()
        assert a.status == TaskStatus.RUNNING
        spawn.assert_called_once_with(a.id, platform_agent.id)

        b = api.create_task(platform_agent, title="b", goal="g2", device_serial="DEV-A")
        second = api.dispatch_device("DEV-A")
        assert second is None
        b.refresh_from_db()
        assert b.status == TaskStatus.PENDING


def test_dispatch_different_serial_parallel(platform_agent):
    with patch("apps.ai_assistant.task_runner.spawn_task_thread"):
        t1 = api.create_task(platform_agent, title="a", goal="g", device_serial="DEV-A")
        t2 = api.create_task(platform_agent, title="b", goal="g", device_serial="DEV-B")
        assert api.dispatch_device("DEV-A").id == t1.id
        assert api.dispatch_device("DEV-B").id == t2.id
        t1.refresh_from_db()
        t2.refresh_from_db()
        assert t1.status == TaskStatus.RUNNING
        assert t2.status == TaskStatus.RUNNING


def test_finalize_starts_next_pending(platform_agent):
    with patch("apps.ai_assistant.task_runner.spawn_task_thread") as spawn:
        first = api.create_task(platform_agent, title="1", goal="g", device_serial="DEV-A")
        second = api.create_task(platform_agent, title="2", goal="g", device_serial="DEV-A")
        api.dispatch_device("DEV-A")
        first.refresh_from_db()
        assert first.status == TaskStatus.RUNNING
        spawn.reset_mock()

        api.finalize_task(first, status=TaskStatus.COMPLETED, result="ok")
        second.refresh_from_db()
        assert second.status == TaskStatus.RUNNING
        spawn.assert_called_once_with(second.id, platform_agent.id)


def test_recover_orphaned_then_dispatch_pending(platform_agent):
    running = api.create_task(platform_agent, title="r", goal="g", device_serial="DEV-A")
    pending = api.create_task(platform_agent, title="p", goal="g", device_serial="DEV-A")
    api.start_task(running)
    with patch("apps.ai_assistant.task_runner.spawn_task_thread") as spawn:
        n = api.recover_orphaned_tasks()
        assert n == 1
        running.refresh_from_db()
        pending.refresh_from_db()
        assert running.status == TaskStatus.FAILED
        assert pending.status == TaskStatus.RUNNING
        spawn.assert_called_once_with(pending.id, platform_agent.id)


def test_serialize_row_includes_device_label(platform_agent):
    task = api.create_task(
        platform_agent,
        title="标题",
        goal="目标全文不应作为唯一展示源",
        device_serial="SER",
        device_label="Pixel",
    )
    row = api.serialize_agent_task_row(task)
    assert row["title"] == "标题"
    assert row["device_label"] == "Pixel"
    assert row["device_serial"] == "SER"
    assert "created_at" in row
    assert "status" in row
    assert row["started_at"] == ""
    assert row["finished_at"] == ""
    assert row["deepseek_cost"] == 0.0

    task.input_tokens = 1000
    task.output_tokens = 100
    task.save(update_fields=["input_tokens", "output_tokens"])
    billed = api.serialize_agent_task_row(task)
    assert isinstance(billed["deepseek_cost"], float)
    assert billed["deepseek_cost"] > 0


# ── 入模可观察性：详情可见规划输入与附件正文，列表只给附件名 ──


def _agent_stub() -> SimpleNamespace:
    """带三角色线路与系统提示词的智能体桩（供 build_request 派生规划输入）。"""
    return SimpleNamespace(
        route_configs={
            engine_adapter.ROUTE_KEY: {
                role: {
                    "provider": "deepseek",
                    "model_name": "m",
                    "api_key": api.encrypt_key("sk"),
                    "base_url": "",
                }
                for role in engine_adapter.ROUTE_ROLES
            }
        },
        max_loops=3,
        owner_id="1",
        enable_skills=False,
        prompt_planner="## p",
        prompt_executor="## e",
        prompt_verifier="## v",
    )


def test_detail_exposes_planner_input_and_attachment(platform_agent):
    task = api.create_task(
        platform_agent,
        title="校准色温",
        goal="拖动滑块到最左",
        attachment="## 第 1 页\n\n关掉自动亮度",
        attachment_filename="steps.pdf",
        device_serial="SER-1",
    )
    detail = api.serialize_agent_task_detail(task)
    payload = json.loads(detail["planner_input"])
    assert set(payload) == {"任务标题", "任务目标", "附件文本内容", "设备ID"}
    assert payload["附件文本内容"] == "## 第 1 页\n\n关掉自动亮度"
    assert detail["attachment"] == payload["附件文本内容"]
    assert detail["attachment_filename"] == "steps.pdf"


def test_detail_empty_attachment_is_blank_string(platform_agent):
    task = api.create_task(platform_agent, title="t", goal="g", device_serial="SER-1")
    detail = api.serialize_agent_task_detail(task)
    payload = json.loads(detail["planner_input"])
    assert payload["附件文本内容"] == ""
    assert detail["attachment"] == ""
    assert detail["attachment_filename"] == ""


def test_row_exposes_attachment_filename_without_body(platform_agent):
    task = api.create_task(
        platform_agent,
        title="t",
        goal="g",
        attachment="## 正文\n\n不应出现在列表行",
        attachment_filename="a.docx",
        device_serial="SER",
    )
    row = api.serialize_agent_task_row(task)
    assert row["attachment_filename"] == "a.docx"
    assert "attachment" not in row


def test_detail_planner_input_matches_engine_request(platform_agent):
    """展示值与实际入模值必须逐字一致（同一派生函数，无第二份实现）。"""
    task = api.create_task(
        platform_agent,
        title="进详情",
        goal="打开应用",
        attachment="## 页",
        attachment_filename="p.pdf",
        device_serial="SER-X",
    )
    req = engine_adapter.build_request(task, _agent_stub())
    assert api.serialize_agent_task_detail(task)["planner_input"] == req.goal
