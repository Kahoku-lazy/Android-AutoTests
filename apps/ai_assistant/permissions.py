"""ai-assistant permissions — 写操作权限检查。

所有写操作（创建/更新/删除）必须通过 check_* 函数验证权限。
读操作（列表/详情）不需要权限检查（共享智能体对普通用户可见）。

filter_agents_for_user 已移入 api.py（跨 App 合法通道），此处 re-export 保
本 App 内部兼容。
"""

from django.contrib.auth import get_user_model

from apps.ai_assistant.api import filter_agents_for_user  # noqa: F401
from apps.ai_assistant.models import AIAgent, AIConversation

User = get_user_model()


def _same_user(record_owner_id, user_id: str) -> bool:
    """Check ownership. Null-owner records are considered unowned — no access."""
    if record_owner_id is None:
        return False
    return str(record_owner_id) == str(user_id)


def _is_superuser(user_id) -> bool:
    """按 user_id 判定是否为超级管理员。"""
    if not user_id:
        return False
    try:
        return User.objects.filter(pk=int(user_id), is_superuser=True).exists()
    except (ValueError, TypeError):
        return False


def _owner_is_superuser(owner_id) -> bool:
    """判定某个 owner 是否为超级管理员（用于共享智能体可见性）。"""
    if not owner_id:
        return False
    try:
        return User.objects.filter(pk=int(owner_id), is_superuser=True).exists()
    except (ValueError, TypeError):
        return False


def check_agent_owner(user_id: str, agent_id: int) -> bool:
    """检查用户是否拥有该 Agent。"""
    if not user_id:
        return False
    agent = AIAgent.objects.filter(id=agent_id).only("id", "owner_id").first()
    if not agent:
        return False
    return _same_user(agent.owner_id, user_id)


def check_agent_visible(user_id: str, agent_id: int) -> bool:
    """检查用户是否可见该 Agent（owner 或超级管理员拥有的共享智能体）。"""
    if not user_id:
        return False
    agent = AIAgent.objects.filter(id=agent_id).only("id", "owner_id").first()
    if not agent:
        return False
    if _same_user(agent.owner_id, user_id):
        return True
    return _owner_is_superuser(agent.owner_id)


def check_conversation_access(user_id: str, conv_id: int) -> bool:
    """检查用户是否有权访问该对话（对话 owner 即可，不要求同时拥有 agent）。"""
    if not user_id:
        return False
    conv = AIConversation.objects.filter(id=conv_id).only("id", "owner_id").first()
    if not conv:
        return False
    return _same_user(conv.owner_id, user_id)


def check_can_create_agent(user_id: str) -> bool:
    """仅超级管理员可创建 Agent。"""
    return _is_superuser(user_id)


def check_can_delete_agent(user_id: str, agent_id: int) -> bool:
    """仅超级管理员可删除 Agent。"""
    return _is_superuser(user_id)


def check_can_update_agent(user_id: str, agent_id: int) -> bool:
    """仅超级管理员可更新 Agent 配置。"""
    return _is_superuser(user_id)


def filter_conversations_for_user(queryset, user_id: str | None):
    """Scope conversation list to user-owned rows only."""
    if not user_id:
        return queryset.none()
    return queryset.filter(owner_id=user_id)
