"""
文件名: ➡️ chat_model.py 🏁
路径: ➡️ engines/agents/models/chat_model.py 🏁
模块功能：➡️ 聊天模型工厂：按 provider 建 DeepSeek / DashScope / OpenAI，并在强制交卷时关思考 🏁
Python 调试：➡️ python -m engines.agents.models.chat_model 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ChatModelFactory: 按 provider 创建 DeepSeek / DashScope / OpenAI 聊天模型
2. apply_forced_handover_kwargs: 强制结构化交卷那一次请求关掉思考，其余请求原样返回
3. bind_forced_handover: 把上面的请求改写挂到模型调用上
🏁
关联模块：➡️
1. engines.agents.models.types: 导入 ModelConfig，工厂的输入
2. utils.logs: 导入 agent_event_log，输出模型创建事件
🏁
测试：➡️
1. tests/graybox/unit/test_forced_handover_thinking.py: 强制交卷关闭思考，未满轮次的请求保持原样
2. tests/engines/agents/test_models.py: executor/verifier 模型连通性（e2e）
🏁
"""

from __future__ import annotations

from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)

from utils.logs import agent_event_log

from .types import ModelConfig

# 框架在自由推理用尽后，会把工具选择强制成这个名字。
_FORCED_HANDOVER_TOOL = "GenerateStructuredOutput"

__all__ = [
    "ChatModelFactory",
    "apply_forced_handover_kwargs",
    "bind_forced_handover",
]


def apply_forced_handover_kwargs(model: object, tool_choice: object, kwargs: dict) -> dict:
    """强制交卷时关闭思考，并保留额外体里的其他键。其余请求原样返回。

    Args:
        model: 被调用的模型实例，读它的 extra_body。
        tool_choice: 本次请求的工具选择；只有 mode 为强制交卷工具时才改写。
        kwargs: 本次请求的原始关键字参数。

    Returns:
        改写后的请求参数；非强制交卷时原样返回。
    """
    if getattr(tool_choice, "mode", None) != _FORCED_HANDOVER_TOOL:
        return kwargs
    base = dict(getattr(model, "extra_body", None) or {})
    incoming = dict(kwargs.get("extra_body") or {})
    thinking = dict(base.get("thinking") or {})
    thinking.update(dict(incoming.get("thinking") or {}))
    thinking["type"] = "disabled"
    merged = {**base, **incoming, "thinking": thinking}
    return {**kwargs, "extra_body": merged}


def bind_forced_handover(model: ChatModelBase) -> ChatModelBase:
    """挂到模型调用上：只有强制结构化交卷的那一次关闭思考。

    Args:
        model: 已建好的聊天模型实例。

    Returns:
        同一个模型实例（`_call_api` 已被包装）。
    """
    original = model._call_api

    async def _call_api(*args, **kwargs):
        kwargs = apply_forced_handover_kwargs(model, kwargs.get("tool_choice"), kwargs)
        return await original(*args, **kwargs)

    model._call_api = _call_api
    return model


class ChatModelFactory:
    """按 provider 创建 DeepSeek、DashScope 或 OpenAI 模型。"""

    def __init__(self, config: ModelConfig):
        """
        创建模型工厂：根据模型配置创建模型。

        Args:
            config: 模型配置（含 stream / vision）。
        """

        self.log = agent_event_log
        self.config = config
        self.stream = config.stream
        self.vision = config.vision

    def _credential(self, credential_cls):
        """凭证：base_url 原样传入（DeepSeek 与 OpenAI 兼容档的现有口径）。"""
        return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)

    def _credential_default_endpoint(self, credential_cls):
        """凭证：base_url 为空时不传，交给框架默认地址（DashScope 的现有口径）。"""
        if self.config.base_url:
            return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)
        return credential_cls(api_key=self.config.api_key)

    def deepseek_model(self) -> ChatModelBase:
        """创建 DeepSeek。vision 时走 OpenAI 兼容客户端，才能把截图当图片传入。

        Returns:
            DeepSeek 聊天模型实例。
        """
        config = self.config
        if self.vision:
            return OpenAIChatModel(
                credential=self._credential(OpenAICredential),
                model=config.model_name,
                parameters=OpenAIChatModel.Parameters(thinking_enable=True),
                stream=self.stream,
                extra_body={"thinking": {"type": "enabled"}},
            )
        return DeepSeekChatModel(
            credential=self._credential(DeepSeekCredential),
            model=config.model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=True),
            stream=self.stream,
        )

    def openai_model(self) -> OpenAIChatModel:
        """创建 OpenAI 模型。

        Returns:
            OpenAI 聊天模型实例。
        """
        config = self.config
        return OpenAIChatModel(
            credential=self._credential(OpenAICredential),
            model=config.model_name,
            stream=self.stream,
        )

    def dashscope_model(self) -> DashScopeChatModel:
        """创建 DashScope 模型。base_url 为空时使用框架默认地址。

        Returns:
            DashScope 聊天模型实例。
        """
        config = self.config
        return DashScopeChatModel(
            credential=self._credential_default_endpoint(DashScopeCredential),
            model=config.model_name,
            stream=self.stream,
        )

    def create(self) -> ChatModelBase:
        """按 provider 创建模型。

        Returns:
            该 provider 对应的聊天模型实例。

        Raises:
            ValueError: provider 不在支持集合内（deepseek / openai / dashscope），
                报错会列出可选厂商。
        """
        config = self.config
        builders = {
            "deepseek": self.deepseek_model,
            "openai": self.openai_model,
            "dashscope": self.dashscope_model,
        }
        builder = builders.get(config.provider)
        if builder is None:
            raise ValueError(f"不支持的模型提供商: {config.provider}；可选：{', '.join(builders)}")
        return bind_forced_handover(builder())
