"""ai-assistant permissions — 写操作权限检查。

所有写操作（创建/更新/删除）必须通过 check_* 函数验证权限。
读操作（列表/详情）不需要权限检查。
"""
from apps.ai_assistant.models import AIAgent, AIConversation


def check_agent_owner(user_id: str, agent_id: int) -> bool:
    """检查用户是否拥有该 Agent。

    当前项目为单用户模式，所有登录用户都有权限。
    多用户扩展时在此添加 owner 字段检查。
    """
    if not user_id:
        return False
    agent = AIAgent.objects.filter(id=agent_id).first()
    return agent is not None


def check_conversation_access(user_id: str, conv_id: int) -> bool:
    """检查用户是否有权访问该对话。

    当前项目为单用户模式，所有登录用户都有权限。
    多用户扩展时在此添加 owner 字段检查。
    """
    if not user_id:
        return False
    conv = AIConversation.objects.filter(id=conv_id).first()
    return conv is not None


def check_can_create_agent(user_id: str) -> bool:
    """检查用户是否可以创建 Agent。"""
    return bool(user_id)


def check_can_delete_agent(user_id: str, agent_id: int) -> bool:
    """检查用户是否可以删除 Agent。"""
    return check_agent_owner(user_id, agent_id)


def check_can_update_agent(user_id: str, agent_id: int) -> bool:
    """检查用户是否可以更新 Agent 配置。"""
    return check_agent_owner(user_id, agent_id)
