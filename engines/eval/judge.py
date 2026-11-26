from __future__ import annotations

import os

from pathlib import Path
from typing import Any

from dotenv import dotenv_values

__all__ = ["DEFAULT_BASE_URLS", "build_judge", "read_secret"]

DEFAULT_BASE_URLS = {
    "deepseek": "https://api.deepseek.com",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
_ENV = dotenv_values(_ENV_PATH) if _ENV_PATH.exists() else {}


def read_secret(name: str) -> str:
    return str(_ENV.get(name) or os.environ.get(name, ""))


def _enable_offline() -> None:
    os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def build_judge(
    *,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
) -> Any:
    _enable_offline()
    key = read_secret(api_key_env)
    if not key:
        raise ValueError(f"没有配置判分模型密钥 {api_key_env}")
    endpoint = base_url or DEFAULT_BASE_URLS.get(provider, "")
    if provider == "deepseek":
        from deepeval.models import DeepSeekModel

        return DeepSeekModel(model=model_name, api_key=key, temperature=0)
    if provider in {"dashscope", "openai"}:
        from deepeval.models import OpenAIModel

        if not endpoint:
            raise ValueError(f"{provider} 的 base_url 不能为空")
        return OpenAIModel(
            model=model_name,
            api_key=key,
            base_url=endpoint,
            temperature=0,
            cost_per_input_token=0,
            cost_per_output_token=0,
        )
    raise ValueError(f"不支持的 provider {provider!r}")
