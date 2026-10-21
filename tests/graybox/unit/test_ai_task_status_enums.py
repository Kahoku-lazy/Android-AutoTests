"""D4-1 不变量：ai_assistant 状态字面量收敛到 `models/` 枚举后，成员写库必须等价于写取值串。

与设备域同一手法（见 `test_device_enum_literals.py`）：本 App 的 `AIAgent.status` /
`Task.status` 是前端轮询的依据，写库值必须仍是
`"active"` / `"running"` 这类取值串，而不是 `"TaskStatus.RUNNING"` 这类限定名。
"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task
from backend.models.constants import AgentStatus, MessageRole, TaskStatus

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_agent_status_round_trip_and_filter():
    """`AIAgent.status`：枚举写入 → 读回取值串；按成员 / 按字面量过滤命中同一行。"""
    AIAgent.objects.create(name="enum-agent", status=AgentStatus.ACTIVE)

    agent = AIAgent.objects.get(name="enum-agent")
    assert agent.status == "active"
    assert "AgentStatus" not in agent.status
    assert AIAgent.objects.filter(status=AgentStatus.ACTIVE).count() == 1
    assert AIAgent.objects.filter(status="active").count() == 1


def test_task_status_round_trip_through_update_fields():
    """`Task.status`：`start_task` / `finalize_task` 的真实写形状（`update_fields`）。"""
    agent = AIAgent.objects.create(name="enum-agent-2")
    task = Task.objects.create(agent=agent, title="t", status=TaskStatus.PENDING)
    assert Task.objects.get(id=task.id).status == "pending"

    task.status = TaskStatus.RUNNING
    task.save(update_fields=["status"])
    assert Task.objects.get(id=task.id).status == "running"

    task.status = TaskStatus.FAILED
    task.save(update_fields=["status"])
    refreshed = Task.objects.get(id=task.id)
    assert refreshed.status == "failed"
    assert "TaskStatus" not in refreshed.status


def test_serializer_role_whitelist_matches_enum_members():
    """serializers 的 role 白名单已改为枚举元组，必须与 `MessageRole` 成员同集合。"""
    assert {m.value for m in MessageRole} == {"user", "assistant", "system"}


def test_task_status_members_cover_polling_states():
    """前端轮询依赖的任务态必须是 `TaskStatus` 的成员，含用户关闭与重启中断。"""
    assert {m.value for m in TaskStatus} == {
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        "interrupted",
    }
