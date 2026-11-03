"""
文件名: ➡️ fallback.py 🏁
路径: ➡️ engines/agents/models/fallback.py 🏁
模块功能：➡️ 备用聊天模型：按 AGENT_FALLBACK_* 造一个已建好的模型实例 🏁
Python 调试：➡️ python -m engines.agents.models.fallback 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. FallbackModelSettings / load_fallback_settings: 从 AGENT_FALLBACK_* 读备用模型连接参数
2. build_fallback_chat_model: 以角色主模型为底，造出备用模型；未配置模型名时返回 None
3. 重试与退避策略不在这里：本模块只管「备用模型长什么样」，不管「什么时候切」
🏁
关联模块：➡️
1. engines.agents.models.loader: 导入 load_model_config，取主模型的 vision / stream / 默认密钥地址
2. engines.agents.models.chat_model: 导入 ChatModelFactory，建备用模型
3. engines.agents.models.types: 导入 ModelConfig，备用模型的连接参数
🏁
测试：➡️
1. tests/graybox/unit/test_model_retry_middleware.py: 备用模型环境变量解析与未配置时的空返回
🏁
"""

from __future__ import annotations

import os

from dataclasses import dataclass, field

from agentscope.model import ChatModelBase
from pydantic import SecretStr

from .chat_model import ChatModelFactory
from .loader import load_model_config
from .types import ModelConfig

FALLBACK_MODEL_ENV = "AGENT_FALLBACK_MODEL"
"""备用模型名；空表示不启用回退。"""

FALLBACK_PROVIDER_ENV = "AGENT_FALLBACK_PROVIDER"
FALLBACK_BASE_URL_ENV = "AGENT_FALLBACK_BASE_URL"
FALLBACK_API_KEY_ENV = "AGENT_FALLBACK_API_KEY"

__all__ = [
    "FALLBACK_API_KEY_ENV",
    "FALLBACK_BASE_URL_ENV",
    "FALLBACK_MODEL_ENV",
    "FALLBACK_PROVIDER_ENV",
    "FallbackModelSettings",
    "build_fallback_chat_model",
    "load_fallback_settings",
]


@dataclass(frozen=True)
class FallbackModelSettings:
    """
    备用模型的连接参数，全部来自环境变量。

    Attributes:
        model_name: 备用模型名；空串表示不启用回退。
        provider: 备用模型 provider；空串表示沿用主模型。
        base_url: 备用模型 base_url；空串表示沿用主模型。
        api_key: 备用模型密钥；空串表示沿用主模型。
    """

    model_name: str = ""
    provider: str = ""
    base_url: str = ""
    api_key: str = field(default="", repr=False)

    @property
    def enabled(self) -> bool:
        """是否配置了备用模型名。

        Returns:
            配了模型名返回 True。
        """
        return bool(self.model_name)


def load_fallback_settings() -> FallbackModelSettings:
    """从环境变量读备用模型参数；非法或缺失一律回落空串。

    Returns:
        本次运行的备用模型参数；默认不启用回退。
    """
    return FallbackModelSettings(
        model_name=os.environ.get(FALLBACK_MODEL_ENV, "").strip(),
        provider=os.environ.get(FALLBACK_PROVIDER_ENV, "").strip(),
        base_url=os.environ.get(FALLBACK_BASE_URL_ENV, "").strip(),
        api_key=os.environ.get(FALLBACK_API_KEY_ENV, "").strip(),
    )


def build_fallback_chat_model(
    config_key: str,
    settings: FallbackModelSettings | None = None,
) -> ChatModelBase | None:
    """以角色主模型的 vision / stream 与默认密钥地址为底，造出备用聊天模型。

    Args:
        config_key: 角色键，用来取主模型的连接参数。
        settings: 备用模型参数；None 表示现读环境变量。

    Returns:
        已建好的备用模型；未配置模型名时返回 None。

    Raises:
        ValueError: 主模型节缺失，或缺 API 密钥环境变量。
    """
    resolved = settings if settings is not None else load_fallback_settings()
    if not resolved.enabled:
        return None
    primary = load_model_config(config_key)
    api_key: str | SecretStr = primary.api_key
    if isinstance(api_key, SecretStr):
        api_key = api_key.get_secret_value()
    fallback = ModelConfig(
        provider=resolved.provider or primary.provider,
        model_name=resolved.model_name,
        api_key=resolved.api_key or api_key,
        base_url=resolved.base_url or primary.base_url,
        vision=primary.vision,
        stream=primary.stream,
    )
    return ChatModelFactory(fallback).create()
