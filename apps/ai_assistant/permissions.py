"""ai-assistant permissions — 写操作权限检查。

所有写操作（创建/更新/删除）必须通过 check_* 函数验证权限。
读操作（列表/详情）不需要权限检查。
"""

from django.db.models import Q

from apps.ai_assistant.models import AIAgent, AIConversation


def _same_user(record_owner_id, user_id: str) -> bool:
    """Legacy rows with null owner are shared until explicitly assigned."""
    if record_owner_id is None:
        return True
    return str(record_owner_id) == str(user_id)


def check_agent_owner(user_id: str, agent_id: int) -> bool:
    """检查用户是否拥有该 Agent。"""
    if not user_id:
        return False
    agent = AIAgent.objects.filter(id=agent_id).only("id", "owner_id").first()
    if not agent:
        return False
    return _same_user(agent.owner_id, user_id)


def check_conversation_access(user_id: str, conv_id: int) -> bool:
    """检查用户是否有权访问该对话。"""
    if not user_id:
        return False
    conv = (
        AIConversation.objects.filter(id=conv_id)
        .select_related("agent")
        .only("id", "owner_id", "agent__owner_id")
        .first()
    )
    if not conv:
        return False
    if not _same_user(conv.owner_id, user_id):
        return False
    return _same_user(conv.agent.owner_id, user_id)


def check_can_create_agent(user_id: str) -> bool:
    """检查用户是否可以创建 Agent。"""
    return bool(user_id)


def check_can_delete_agent(user_id: str, agent_id: int) -> bool:
    """检查用户是否可以删除 Agent。"""
    return check_agent_owner(user_id, agent_id)


def check_can_update_agent(user_id: str, agent_id: int) -> bool:
    """检查用户是否可以更新 Agent 配置。"""
    return check_agent_owner(user_id, agent_id)


def filter_agents_for_user(queryset, user_id: str | None):
    """Scope agent list to owned + legacy shared rows."""
    if not user_id:
        return queryset.none()
    return queryset.filter(Q(owner_id=user_id) | Q(owner_id__isnull=True))


def filter_conversations_for_user(queryset, user_id: str | None):
    """Scope conversation list to owned + legacy shared rows."""
    if not user_id:
        return queryset.none()
    return queryset.filter(Q(owner_id=user_id) | Q(owner_id__isnull=True))
