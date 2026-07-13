"""ai-assistant serializers — 输入校验与输出格式化。"""
import json

from agentscope_service.provider_registry import VALID_PROVIDERS, validate_base_url


def _first_error(errors: dict) -> str:
    if not errors:
        return "validation failed"
    return "; ".join(f"{k}: {v}" for k, v in errors.items())


def validate_agent_input(data: dict, *, require_api_key: bool = False) -> tuple:
    """校验 Agent 创建/更新输入。返回 (is_valid, errors, cleaned_data)。"""
    errors = {}
    cleaned = dict(data)

    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Agent 名称不能为空"
    else:
        cleaned["name"] = name

    provider = (data.get("model_provider") or "dashscope").strip()
    if provider not in VALID_PROVIDERS:
        errors["model_provider"] = f"不支持的模型提供商: {provider}"
    else:
        cleaned["model_provider"] = provider

    base_url = (data.get("base_url") or "").strip()
    if base_url:
        ok, msg = validate_base_url(provider, base_url)
        if not ok:
            errors["base_url"] = msg
        else:
            cleaned["base_url"] = base_url.rstrip("/")

    if require_api_key and not (data.get("api_key") or "").strip():
        errors["api_key"] = "API Key 不能为空"

    try:
        temperature = float(data.get("temperature", 0.7))
        if not (0 <= temperature <= 2):
            errors["temperature"] = "温度必须在 0-2 之间"
        cleaned["temperature"] = temperature
    except (TypeError, ValueError):
        errors["temperature"] = "温度必须是数字"

    try:
        max_tokens = int(data.get("max_tokens", 4096))
        if not (1 <= max_tokens <= 128000):
            errors["max_tokens"] = "max_tokens 必须在 1-128000 之间"
        cleaned["max_tokens"] = max_tokens
    except (TypeError, ValueError):
        errors["max_tokens"] = "max_tokens 必须是整数"

    return (len(errors) == 0, errors, cleaned)


def validate_message_input(data: dict) -> tuple:
    """校验消息发送输入（save-message 等）。"""
    errors = {}
    role = data.get("role", "assistant")
    content = (data.get("content") or "").strip()
    blocks = data.get("blocks") or []

    if role not in ("user", "assistant", "system"):
        errors["role"] = "无效的角色类型"
    elif role == "user" and not content:
        errors["content"] = "消息内容不能为空"
    elif role == "assistant" and not content and not blocks:
        errors["content"] = "assistant 消息需要 content 或 blocks"

    return (len(errors) == 0, errors, data)


def validate_send_message_input(data: dict) -> tuple:
    """校验 /send 端点输入。"""
    errors = {}
    if not (data.get("message") or "").strip():
        errors["message"] = "消息内容不能为空"
    cleaned = {"message": (data.get("message") or "").strip()}
    return (len(errors) == 0, errors, cleaned)


def validate_conversation_input(data: dict) -> tuple:
    """校验对话创建输入。"""
    errors = {}
    title = (data.get("title") or "新对话").strip() or "新对话"
    cleaned = dict(data)
    cleaned["title"] = title[:500]
    return (len(errors) == 0, errors, cleaned)


def validate_rename_input(data: dict) -> tuple:
    """校验对话重命名输入。"""
    errors = {}
    title = (data.get("title") or "").strip()
    if not title:
        errors["title"] = "标题不能为空"
    return (len(errors) == 0, errors, {"title": title[:500]})


def validate_model_detect_input(data: dict) -> tuple:
    """校验模型探测 POST 输入。"""
    errors = {}
    provider = (data.get("model_provider") or "").strip()
    if provider and provider not in VALID_PROVIDERS:
        errors["model_provider"] = f"不支持的模型提供商: {provider}"

    base_url = (data.get("base_url") or "").strip()
    if base_url and provider:
        ok, msg = validate_base_url(provider, base_url)
        if not ok:
            errors["base_url"] = msg

    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        errors["api_key"] = "API Key 不能为空"

    return (len(errors) == 0, errors, data)


def format_agent_response(agent) -> dict:
    """格式化 Agent 响应（脱敏 api_key）。"""
    from .api import mask_key, decrypt_key

    return {
        "id": agent.id,
        "name": agent.name,
        "avatar": agent.avatar,
        "tags": agent.tags,
        "description": agent.description,
        "model_provider": agent.model_provider,
        "model_name": agent.model_name,
        "api_key": mask_key(decrypt_key(agent.api_key) if agent.api_key else ""),
        "base_url": agent.base_url,
        "system_prompt": agent.system_prompt,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "max_iters": agent.max_iters,
        "memory_mode": agent.memory_mode,
        "status": agent.status,
        "is_connected": agent.is_connected,
        "agent_scope_id": agent.agent_scope_id,
        "owner_id": agent.owner_id,
        "last_checked_at": agent.last_checked_at.isoformat() if agent.last_checked_at else None,
    }


def format_conversation_response(conv) -> dict:
    """格式化对话响应。"""
    return {
        "id": conv.id,
        "agent_id": conv.agent_id,
        "title": conv.title,
        "status": conv.status,
        "agent_scope_session_id": conv.agent_scope_session_id,
        "owner_id": conv.owner_id,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


def format_message_response(msg) -> dict:
    """格式化消息响应。"""
    blocks = None
    if msg.blocks:
        try:
            blocks = json.loads(msg.blocks)
        except (json.JSONDecodeError, TypeError):
            blocks = msg.blocks

    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "content": msg.content,
        "blocks": blocks,
        "reason": msg.reason,
        "tokens": msg.tokens,
        "input_tokens": msg.input_tokens,
        "model_name": msg.model_name,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
