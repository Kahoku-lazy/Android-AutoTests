from __future__ import annotations

KEY_BY_PROVIDER = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "openai": "OPENAI_API_KEY",
}

API_PROTOCOLS = ("deepseek", "dashscope", "openai")

_DEFAULT_BASE = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://test-llm.lanjingerp.com/v1",
}


def expected_key(provider: str) -> str:
    key = KEY_BY_PROVIDER.get(str(provider or "").strip())
    if not key:
        raise ValueError("厂商只允许 deepseek、dashscope、openai")
    return key


def models_url(provider: str, base_url: str = "") -> str:
    del provider
    raw = str(base_url or "").strip().rstrip("/")
    if not raw:
        return ""
    if raw.endswith("/models"):
        return raw
    return f"{raw}/models"
