"""ai-assistant API — 跨模块调用的公共接口。

遵循防火墙 #2：所有跨模块写操作必须通过本文件的函数。
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet
from django.conf import settings

from apps.ai_assistant.models import AIAgent, AIConversation, AIMessage

logger = logging.getLogger("ai_assistant")


__all__ = [
    # Agent 操作
    "get_agent",
    "get_agent_by_scope_id",
    "list_active_agents",
    # 对话操作
    "get_conversation",
    "get_or_create_conversation",
    # 消息操作
    "save_message",
    # 加密工具
    "encrypt_key",
    "decrypt_key",
    "mask_key",
    # 跨模块接口（供 evaluator 等使用）
    "get_provider_config",
    "search_knowledge",
]


# ── Agent 查询（只读）──


def get_agent(agent_id: int):
    """根据主键获取 Agent。"""
    try:
        return AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return None


def get_agent_by_scope_id(scope_id: str):
    """根据 AgentScope 注册 ID 获取 Agent。"""
    try:
        return AIAgent.objects.get(agent_scope_id=scope_id)
    except (AIAgent.DoesNotExist, AIAgent.MultipleObjectsReturned):
        return None


def list_active_agents():
    """获取所有活跃的 Agent。"""
    return list(
        AIAgent.objects.filter(status="active").values("id", "name", "model_provider", "model_name")
    )


# ── 对话操作 ──


def get_conversation(conv_id: int):
    """根据主键获取对话。"""
    try:
        return AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return None


def get_or_create_conversation(agent: AIAgent, title: str = "新对话"):
    """获取或创建对话。返回 (conversation, created)。"""
    return AIConversation.objects.get_or_create(
        agent=agent,
        title=title,
        defaults={"status": "active"},
    )


# ── 消息操作 ──


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    blocks: str = "",
    reason: str = "normal",
    tokens: int = 0,
    input_tokens: int = 0,
    model_name: str = "",
    flow: str = "",
) -> AIMessage:
    """保存一条对话消息到数据库。"""
    return AIMessage.objects.create(
        conversation_id=conversation_id,
        role=role,
        content=content,
        blocks=blocks,
        reason=reason,
        tokens=tokens,
        input_tokens=input_tokens,
        model_name=model_name,
        flow=flow if flow in ("sse", "fallback") else "",
    )


# ── 加密工具（与 views.py 共享实现）──


def _get_cipher() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(plain: str) -> str:
    """加密 API Key。"""
    if not plain:
        return ""
    return _get_cipher().encrypt(plain.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    """解密 API Key。解密失败时返回空字符串而非崩溃。"""
    if not encrypted:
        return ""
    try:
        return _get_cipher().decrypt(encrypted.encode()).decode()
    except Exception:
        logger.exception("API key decryption failed — key may be corrupted or SECRET_KEY rotated")
        return ""


def mask_key(key: str) -> str:
    """脱敏显示 API Key：保留前 3 位 + *** + 后 4 位。"""
    if not key or len(key) < 8:
        return "***"
    return key[:3] + "***" + key[-4:]


# ── 跨模块接口（供 evaluator 等使用，避免直接导入 agent_scope 内部模块）──


def get_provider_config(provider: str, base_url: str = "", model_name: str = "") -> dict:
    """获取模型 provider 的 API 配置（base_url + api_key 模式）。
    供 evaluator 等跨模块调用，避免直接导入 agent_scope.provider_registry。
    """
    from apps.ai_assistant.agent_scope.provider_registry import get_provider_config as _get

    return _get(provider, base_url, model_name)


def search_knowledge(query: str, top_k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """搜索知识库。供 evaluator 等跨模块调用。"""
    from apps.ai_assistant.agent_scope.rag_service import search

    return search(query, top_k=top_k, sources=sources)


def get_kb_doc_count() -> int:
    """获取知识库文档总数。供 evaluator 等跨模块调用。"""
    from apps.ai_assistant.agent_scope.rag_service import _get_collection

    return _get_collection().count()
