"""Unified LLM provider → base URL / credential mapping."""
from urllib.parse import urlparse

from django.conf import settings

PROVIDER_DEFAULTS = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "credential": "dashscope_credential",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "credential": "openai_credential",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "credential": "openai_credential",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "credential": "openai_credential",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "credential": "openai_credential",
    },
    "custom": {
        "base_url": "",
        "credential": "openai_credential",
    },
}

VALID_PROVIDERS = frozenset(PROVIDER_DEFAULTS.keys())

# Host allowlist per provider (custom uses HTTPS + no-localhost rules only)
_PROVIDER_HOSTS = {
    "dashscope": {"dashscope.aliyuncs.com"},
    "openai": {"api.openai.com"},
    "anthropic": {"api.anthropic.com"},
    "deepseek": {"api.deepseek.com"},
    "gemini": {"generativelanguage.googleapis.com"},
}

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def get_provider_config(provider: str, base_url_override: str = "") -> dict:
    """Resolve base_url and AgentScope credential type for a provider."""
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    override = (base_url_override or "").strip().rstrip("/")
    base_url = override or defaults.get("base_url", "")
    return {
        "base_url": base_url.rstrip("/"),
        "credential_type": defaults.get("credential", "openai_credential"),
    }


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
