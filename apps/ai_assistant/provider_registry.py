"""Unified LLM provider → base URL mapping.

Migrated from agentscope_service/provider_registry.py.
Owned by Django — importable by both Django views and AgentScope (via system_prompt).
"""

from urllib.parse import urlparse

from django.conf import settings

# provider → 默认 base_url（唯一真相源；调用方传入的自定义 base_url 覆盖此值）
PROVIDER_DEFAULTS = {
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "custom": "",
}

VALID_PROVIDERS = frozenset(PROVIDER_DEFAULTS)

_PROVIDER_HOSTS = {
    "dashscope": {"dashscope.aliyuncs.com"},
    "openai": {"api.openai.com"},
    "anthropic": {"api.anthropic.com"},
    "deepseek": {"api.deepseek.com"},
    "gemini": {"generativelanguage.googleapis.com"},
}

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def get_provider_config(provider: str, base_url_override: str = "") -> dict:
    """解析某 provider 的 base_url：自定义值优先，否则用 PROVIDER_DEFAULTS 默认值。"""
    default_base_url = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    override = (base_url_override or "").strip().rstrip("/")
    return {"base_url": (override or default_base_url).rstrip("/")}


def validate_base_url(provider: str, base_url: str) -> tuple[bool, str]:
    """Validate a user-supplied base_url. Empty string is allowed (uses default)."""
    if not base_url or not str(base_url).strip():
        return True, ""

    raw = str(base_url).strip().rstrip("/")
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()

    if scheme not in ("https", "http"):
        return False, "base_url 必须使用 http 或 https"
    if not host:
        return False, "base_url 无效"
    if scheme == "http" and not getattr(settings, "DEBUG", True):
        return False, "生产环境 base_url 必须使用 https"
    if host in _BLOCKED_HOSTS:
        return False, "base_url 不允许指向本机地址"

    if provider == "custom":
        return True, ""

    allowed = _PROVIDER_HOSTS.get(provider, set())
    if allowed and host not in allowed:
        return False, f"base_url 主机不在 {provider} 提供商白名单内"

    return True, ""
