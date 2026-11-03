"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/models/__init__.py 🏁
模块功能：➡️ 模型唯一对外门面：其它模块只从这里取模型实例，不碰模型配置 🏁
Python 调试：➡️ python -m engines.agents.models 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. get_chat_model / get_fallback_chat_model: 按角色键取聊天模型与备用模型
2. get_realtime_model: 取 Omni 实时语音模型（按角色键补参数，或全部显式传）
3. get_embedding_model / get_tts_model: 取嵌入模型与语音合成模型
4. get_text / get_realtime / get_embedding / model_supports_image / DeepSeekModelConfig: 只读模型目录
5. 子模块不对外：包外 MUST NOT import `models.<子模块>`，由 test_models_public_surface 守卫
🏁
关联模块：➡️
1. engines.agents.models.catalog: 导入目录访问与能力查询
2. engines.agents.models.chat_model: 导入 ChatModelFactory，建聊天模型
3. engines.agents.models.fallback: 导入 build_fallback_chat_model，建备用模型
4. engines.agents.models.loader: 导入连接参数装载
5. engines.agents.models.embedding_model: 导入 build_embedding_model
6. engines.agents.models.tts_model: 导入 build_tts_model
7. engines.agents.models.realtime_model: 导入 build_realtime_model
🏁
测试：➡️
1. tests/graybox/unit/test_models_public_surface.py: 门面唯一入口守卫（包外不得 import 子模块）
2. tests/engines/agents/test_models.py: 经门面建执行/验收模型（e2e）
🏁
"""

from __future__ import annotations

from typing import Any

from agentscope.model import ChatModelBase

from .catalog import (
    DeepSeekModelConfig,
    get_embedding,
    get_realtime,
    get_text,
    model_supports_image,
)
from .chat_model import ChatModelFactory
from .embedding_model import build_embedding_model
from .fallback import build_fallback_chat_model
from .loader import load_model_config, load_realtime_model_config
from .realtime_model import build_realtime_model
from .tts_model import build_tts_model

__all__ = [
    "DeepSeekModelConfig",
    "get_chat_model",
    "get_embedding",
    "get_embedding_model",
    "get_fallback_chat_model",
    "get_realtime",
    "get_realtime_model",
    "get_text",
    "get_tts_model",
    "model_supports_image",
]


def get_chat_model(config_key: str) -> ChatModelBase:
    """按角色键取一个已建好的聊天模型。

    Args:
        config_key: agent_config.yaml 顶层键，如 UI_EXECUTOR_ROLE_CONFIG。

    Returns:
        该角色的聊天模型实例。

    Raises:
        ValueError: 角色节或 ModelConfig 缺失，或 API 密钥环境变量未设置。
    """
    return ChatModelFactory(load_model_config(config_key)).create()


def get_fallback_chat_model(config_key: str) -> ChatModelBase | None:
    """按角色键取备用聊天模型；环境未配置备用模型名时返回 None。

    Args:
        config_key: agent_config.yaml 顶层键，用来取主模型的 vision / stream 与默认密钥地址。

    Returns:
        已建好的备用模型，或 None。

    Raises:
        ValueError: 主模型节缺失，或缺 API 密钥环境变量。
    """
    return build_fallback_chat_model(config_key)


def get_realtime_model(
    *,
    role_key: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    base_url: str = "",
    voice: str | None = None,
    parameters: Any = None,
    **parameter_kwargs: Any,
) -> Any:
    """取 Omni 实时语音模型。

    Args:
        role_key: 角色键；给定时从该节的 ModelConfig 补密钥 / 模型名 / 地址 / 音色。
        api_key: 显式密钥，优先于角色配置。
        model_name: 显式模型名，优先于角色配置。
        base_url: 显式基础地址，优先于角色配置。
        voice: 显式音色，优先于角色配置。
        parameters: 已构造好的框架 Parameters；与关键字参数互斥。
        parameter_kwargs: 传给框架 Parameters 的关键字（turn_detection / vad 等）。

    Returns:
        `DashScopeRealtimeModel` 实例。

    Raises:
        RuntimeError: 未安装 `agentscope[realtime]`，或模型/音色不受支持。
        ValueError: 角色节缺失，或密钥环境变量未设置。
        TypeError: `parameters` 与关键字参数同时传入。
    """
    ready = get_realtime("omni")
    if role_key is not None:
        config = load_realtime_model_config(role_key)
        api_key = api_key or config.api_key.get_secret_value()
        model_name = model_name or config.model_name
        base_url = base_url or config.base_url
        if voice is None:
            voice = config.voice
    if not api_key:
        api_key = ready.resolve_api_key()
    if not api_key:
        raise ValueError(f"环境变量未设置: {ready.api_key_env}")
    return build_realtime_model(
        api_key=api_key,
        model_name=model_name or ready.model,
        base_url=base_url,
        voice=voice,
        parameters=parameters,
        **parameter_kwargs,
    )


def get_embedding_model(
    api_key: str,
    *,
    model_name: str | None = None,
    dimensions: int | None = None,
    usage_sink: Any = None,
) -> Any:
    """取一个 DashScope 嵌入模型。

    Args:
        api_key: DashScope 密钥。
        model_name: 模型名；None 用目录默认值。
        dimensions: 向量维度；None 用目录默认值。
        usage_sink: 嵌入 token 用量回调；None 表示不记录。

    Returns:
        嵌入模型实例。
    """
    return build_embedding_model(
        api_key=api_key,
        model_name=model_name,
        dimensions=dimensions,
        usage_sink=usage_sink,
    )


def get_tts_model(
    *,
    api_key: str | None = None,
    model_name: str | None = None,
    voice: str | None = None,
) -> Any:
    """取一个 DashScope 语音合成模型。

    Args:
        api_key: 密钥；None 时读 `DASHSCOPE_API_KEY`。
        model_name: 模型名；None 时读 `AGENT_TTS_MODEL`。
        voice: 音色；None 时读 `AGENT_TTS_VOICE`。

    Returns:
        语音合成模型实例。

    Raises:
        RuntimeError: 缺少 TTS 依赖，或缺 `DASHSCOPE_API_KEY`。
    """
    return build_tts_model(api_key=api_key, model_name=model_name, voice=voice)
