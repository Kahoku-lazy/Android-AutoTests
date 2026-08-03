"""ai-assistant serializers — 输入校验与输出格式化。"""

import json

from apps.ai_assistant.agent_scope.provider_registry import VALID_PROVIDERS, validate_base_url


def _first_error(errors: dict) -> str:
    if not errors:
        return "validation failed"
    return "; ".join(f"{k}: {v}" for k, v in errors.items())


def validate_agent_input(data: dict, *, require_api_key: bool = False) -> tuple:
    """校验 Agent 创建/更新输入。返回 (is_valid, errors, cleaned_data)。"""
    errors = {}
    cleaned = dict(data)

    # name is required for both creation and updates
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

    # Validate generate_kwargs is valid JSON if provided
    gk = (data.get("generate_kwargs") or "{}").strip()
    if gk and gk != "{}":
        try:
            json.loads(gk)
        except (json.JSONDecodeError, TypeError):
            errors["generate_kwargs"] = "generate_kwargs 必须是合法的 JSON 字符串"

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
