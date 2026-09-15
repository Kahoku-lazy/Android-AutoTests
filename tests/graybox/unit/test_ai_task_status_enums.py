"""D4-1 不变量：ai_assistant 状态字面量收敛到 `models/` 枚举后，成员写库必须等价于写取值串。

与设备域同一手法（见 `test_device_enum_literals.py`）：本 App 的 `AIAgent.status` /
`AITask.status` / `AIMessage.role` 是前端轮询与消息渲染的依据，写库值必须仍是
`"active"` / `"running"` 这类取值串，而不是 `"TaskStatus.RUNNING"` 这类限定名。
"""

from __future__ import annotations

import pytest

from apps.ai_assistant.models import AIAgent, AIConversation, AIMessage, AITask
from models.constants import AgentStatus, MessageRole, TaskStatus

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
    """`AITask.status`：`start_task` / `finalize_task` 的真实写形状（`update_fields`）。"""
    agent = AIAgent.objects.create(name="enum-agent-2")
    task = AITask.objects.create(agent=agent, title="t", status=TaskStatus.PENDING)
    assert AITask.objects.get(id=task.id).status == "pending"

    task.status = TaskStatus.RUNNING
    task.save(update_fields=["status"])
    assert AITask.objects.get(id=task.id).status == "running"

    task.status = TaskStatus.FAILED
    task.save(update_fields=["status"])
    refreshed = AITask.objects.get(id=task.id)
    assert refreshed.status == "failed"
    assert "TaskStatus" not in refreshed.status


def test_message_role_round_trip_and_filter():
    """`AIMessage.role`：枚举写入 → 读回取值串；按成员过滤命中。"""
    agent = AIAgent.objects.create(name="enum-agent-3")
    conversation = AIConversation.objects.create(agent=agent)
    AIMessage.objects.create(conversation=conversation, role=MessageRole.ASSISTANT, content="hi")

    message = AIMessage.objects.get(conversation=conversation)
    assert message.role == "assistant"
    assert "MessageRole" not in message.role
    assert AIMessage.objects.filter(role=MessageRole.ASSISTANT).count() == 1
    assert AIMessage.objects.filter(role=MessageRole.USER).count() == 0


def test_serializer_role_whitelist_matches_enum_members():
    """serializers 的 role 白名单已改为枚举元组，必须与 `MessageRole` 成员同集合。"""
    assert {m.value for m in MessageRole} == {"user", "assistant", "system"}


def test_task_status_members_cover_polling_states():
    """前端轮询依赖的四个任务态必须是 `TaskStatus` 的成员。"""
    assert {m.value for m in TaskStatus} == {"pending", "running", "completed", "failed"}
