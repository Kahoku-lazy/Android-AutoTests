"""ai-assistant serializers — 输入校验与输出格式化。"""
import json


def validate_agent_input(data: dict) -> tuple:
    """校验 Agent 创建/更新输入。返回 (is_valid, errors, cleaned_data)。"""
    errors = {}

    if not data.get("name", "").strip():
        errors["name"] = "Agent 名称不能为空"

    provider = data.get("model_provider", "dashscope")
    valid_providers = {"dashscope", "openai", "anthropic", "custom"}
    if provider not in valid_providers:
        errors["provider"] = f"不支持的模型提供商: {provider}"

    temperature = data.get("temperature", 0.7)
    if not (0 <= float(temperature) <= 2):
        errors["temperature"] = "温度必须在 0-2 之间"

    max_tokens = data.get("max_tokens", 4096)
    if not (1 <= int(max_tokens) <= 128000):
        errors["max_tokens"] = "max_tokens 必须在 1-128000 之间"

    return (len(errors) == 0, errors, data)


def validate_message_input(data: dict) -> tuple:
    """校验消息发送输入。"""
    errors = {}

    if not data.get("content", "").strip():
        errors["content"] = "消息内容不能为空"

    role = data.get("role", "user")
    if role not in ("user", "assistant", "system"):
        errors["role"] = "无效的角色类型"

    return (len(errors) == 0, errors, data)


def validate_conversation_input(data: dict) -> tuple:
    """校验对话创建输入。"""
    errors = {}

    if not data.get("agent_id"):
        errors["agent_id"] = "必须指定 Agent"

    return (len(errors) == 0, errors, data)


def format_agent_response(agent) -> dict:
    """格式化 Agent 响应（脱敏 api_key）。"""
    from .api import mask_key

    return {
        "id": agent.id,
        "name": agent.name,
        "avatar": agent.avatar,
        "tags": agent.tags,
        "description": agent.description,
        "model_provider": agent.model_provider,
        "model_name": agent.model_name,
        "api_key": mask_key(agent.api_key) if agent.api_key else "",
        "base_url": agent.base_url,
        "system_prompt": agent.system_prompt,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "max_iters": agent.max_iters,
        "memory_mode": agent.memory_mode,
        "status": agent.status,
        "is_connected": agent.is_connected,
        "agent_scope_id": agent.agent_scope_id,
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
