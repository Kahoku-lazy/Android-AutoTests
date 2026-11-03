"""
文件名: ➡️ types.py 🏁
路径: ➡️ engines/agents/models/types.py 🏁
模块功能：➡️ 模型连接参数类型：聊天与实时语音两套不可变配置 🏁
Python 调试：➡️ python -m engines.agents.models.types 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ModelConfig: 聊天模型连接参数（provider / model_name / api_key / base_url / vision / stream）
2. RealtimeModelConfig: 实时语音模型连接参数（provider / model_name / api_key / base_url / voice）
3. 本模块只放不可变数据类：不做 IO、不建模型实例，供工厂与目录共用
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_forced_handover_thinking.py: 构造 ModelConfig 建模型
2. tests/engines/agents/test_models.py: 经模型工厂消费本配置类型
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import SecretStr

__all__ = ["ModelConfig", "RealtimeModelConfig"]


@dataclass(frozen=True)
class ModelConfig:
    """
    模型配置：提供商、模型名称、API 密钥、基础 URL，以及 vision / stream。

    Attributes:
        provider: 模型提供商，可选 deepseek、openai、dashscope。
        model_name: 模型名称，如 deepseek-chat、gpt-4o、qwen-plus。
        api_key: API 密钥，字符串或 SecretStr 类型。
        base_url: 基础 URL，可选。
        vision: 是否多模态（需截图输入时为 True）。
        stream: 是否流式输出。

    Raises:
        FrozenInstanceError: 模型配置不可变。
    """

    provider: str = ""
    model_name: str = ""
    api_key: str | SecretStr = ""
    base_url: str = ""
    vision: bool = False
    stream: bool = True

    def __post_init__(self) -> None:
        """把 api_key 包成 SecretStr，并把 vision / stream 归一到布尔。"""
        if not isinstance(self.api_key, SecretStr):
            object.__setattr__(self, "api_key", SecretStr(self.api_key))
        object.__setattr__(self, "vision", bool(self.vision))
        object.__setattr__(self, "stream", bool(self.stream))


@dataclass(frozen=True)
class RealtimeModelConfig:
    """
    DashScope Omni 实时语音模型配置（与聊天 ModelConfig 分离）。

    Attributes:
        provider: 提供商，当前仅支持 dashscope。
        model_name: 实时模型名，如 qwen3.5-omni-plus-realtime。
        api_key: API 密钥（SecretStr）。
        base_url: 可选；空则交给框架默认地址。
        voice: Parameters.voice 音色名。

    Raises:
        FrozenInstanceError: 配置不可变。
    """

    provider: str = "dashscope"
    model_name: str = "qwen3.5-omni-plus-realtime"
    api_key: str | SecretStr = ""
    base_url: str = ""
    voice: str = "Tina"

    def __post_init__(self) -> None:
        """把 api_key 包成 SecretStr，避免 repr 泄漏密钥。"""
        if not isinstance(self.api_key, SecretStr):
            object.__setattr__(self, "api_key", SecretStr(self.api_key))
