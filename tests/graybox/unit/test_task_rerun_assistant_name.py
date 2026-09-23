"""失败任务克隆重跑 + 列表助手名（实时取线路 name）。"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.ai_assistant import api
from apps.ai_assistant.models import AIAgent
from models.constants import AgentStatus, TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]


def _role_cfg() -> dict:
    return {
        "provider": "deepseek",
        "model_name": "m1",
        "api_key": api.encrypt_key("sk-test"),
        "base_url": "",
    }


@pytest.fixture
def platform_agent(db):
    return AIAgent.objects.create(
        name="平台智能体",
        status=AgentStatus.ACTIVE,
        route_configs={
            "device_control": {
                "name": "UI 视觉自动化",
                "planner": _role_cfg(),
                "executor": _role_cfg(),
                "verifier": _role_cfg(),
            }
        },
        max_loops=3,
    )


def test_rerun_task_clones_without_mutating_original(platform_agent):
    original = api.create_task(
        platform_agent,
        title="点击音乐",
        goal="进入音乐模式",
        attachment="# md",
        attachment_filename="a.pdf",
        device_serial="SER1",
        device_label="SM-S9010",
    )
    api.finalize_task(original, status=TaskStatus.FAILED, result="执行异常: 402")
    original.refresh_from_db()
    assert original.status == TaskStatus.FAILED

    with patch("apps.ai_assistant.api.dispatch_device"):
        cloned = api.rerun_task(original)

    original.refresh_from_db()
    assert original.status == TaskStatus.FAILED
    assert original.result == "执行异常: 402"
    assert cloned.id != original.id
    assert cloned.status == TaskStatus.PENDING
    assert cloned.title == original.title
    assert cloned.goal == original.goal
    assert cloned.attachment == original.attachment
    assert cloned.attachment_filename == original.attachment_filename
    assert cloned.device_serial == original.device_serial
    assert cloned.device_label == original.device_label
    assert cloned.agent_id == original.agent_id


def test_serialize_assistant_name_from_route_and_follows_rename(platform_agent):
    task = api.create_task(
        platform_agent,
        title="t",
        goal="g",
        device_serial="S",
    )
    row = api.serialize_agent_task_row(task)
    assert row["assistant_name"] == "UI 视觉自动化"

    configs = dict(platform_agent.route_configs or {})
    dc = dict(configs.get("device_control") or {})
    dc["name"] = "新助手名"
    configs["device_control"] = dc
    platform_agent.route_configs = configs
    platform_agent.save(update_fields=["route_configs"])

    task.refresh_from_db()
    # 重新挂载 agent，避免缓存旧 route_configs
    task = type(task).objects.select_related("agent").get(id=task.id)
    row2 = api.serialize_agent_task_row(task)
    assert row2["assistant_name"] == "新助手名"


def test_resolve_assistant_name_falls_back_to_agent_name():
    agent = AIAgent.objects.create(
        name="仅智能体名",
        status=AgentStatus.ACTIVE,
        route_configs={"device_control": {"name": "", "planner": _role_cfg()}},
    )
    assert api.resolve_assistant_name(agent) == "仅智能体名"
