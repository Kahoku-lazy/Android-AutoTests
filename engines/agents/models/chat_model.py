"""
文件名: ➡️ chat_model.py 🏁
路径: ➡️ engines/agents/models/chat_model.py 🏁
模块功能：➡️ 聊天模型工厂：按 provider 建 DeepSeek / DashScope / OpenAI，并在强制交卷时关思考 🏁
Python 调试：➡️ python -m engines.agents.models.chat_model 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-09 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ChatModelFactory: 按 provider 创建 DeepSeek / DashScope / OpenAI 聊天模型
2. apply_forced_handover_kwargs: 强制结构化交卷那一次请求关掉思考，其余请求原样返回
3. bind_forced_handover: 把上面的请求改写挂到模型调用上，已挂过即原样返回（幂等）
4. get_or_create_chat_model: 同一配置指纹、同一事件循环内复用已建实例
5. clear_chat_model_cache: 清空实例复用，供测试隔离环境变量
6. _config_fingerprint / _same_loop: 复用判定：连接参数 + 事件循环都相同才命中
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

import asyncio
import hashlib
import weakref

from dataclasses import dataclass

from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)
from pydantic import SecretStr

from utils.logs import agent_event_log

from .types import ModelConfig

# 框架在自由推理用尽后，会把工具选择强制成这个名字。
_FORCED_HANDOVER_TOOL = "GenerateStructuredOutput"

# 实例上的标记：强制交卷改写已挂过。共享实例被反复装配时不再叠包装。
_HANDOVER_BOUND_FLAG = "_forced_handover_bound"

__all__ = [
    "ChatModelFactory",
    "apply_forced_handover_kwargs",
    "bind_forced_handover",
    "clear_chat_model_cache",
    "get_or_create_chat_model",
]


@dataclass
class _CachedModel:
    """
    一条聊天模型复用记录。

    Attributes:
        loop_ref: 建实例时的事件循环弱引用；None 表示当时不在事件循环内。
        model: 已建好的模型实例。
    """

    loop_ref: weakref.ReferenceType | None
    model: ChatModelBase


# 配置指纹 → 复用记录。见 openspec 变更 agent-role-build-cache-and-guards。
_MODEL_CACHE: dict[tuple, _CachedModel] = {}


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

    幂等：同一个实例已挂过就原样返回，避免共享实例被反复包裹。

    Args:
        model: 已建好的聊天模型实例。

    Returns:
        同一个模型实例（`_call_api` 已被包装）。
    """
    if getattr(model, _HANDOVER_BOUND_FLAG, False):
        return model
    original = model._call_api

    async def _call_api(*args, **kwargs):
        kwargs = apply_forced_handover_kwargs(model, kwargs.get("tool_choice"), kwargs)
        return await original(*args, **kwargs)

    model._call_api = _call_api
    setattr(model, _HANDOVER_BOUND_FLAG, True)
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


def _config_fingerprint(config: ModelConfig) -> tuple[str, str, str, str, bool, bool]:
    """把连接参数收成可哈希的复用键；密钥只留摘要，不把明文放进长期结构。

    Args:
        config: 模型连接参数。

    Returns:
        (provider, 模型名, 地址, 密钥摘要, vision, stream)。
    """
    api_key = config.api_key
    if isinstance(api_key, SecretStr):
        api_key = api_key.get_secret_value()
    digest = hashlib.sha256(str(api_key).encode("utf-8")).hexdigest()[:32]
    return (
        config.provider,
        config.model_name,
        str(config.base_url or ""),
        digest,
        bool(config.vision),
        bool(config.stream),
    )


def _current_loop() -> asyncio.AbstractEventLoop | None:
    """取当前事件循环；不在事件循环内时返回 None。

    Returns:
        正在运行的事件循环，或 None。
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def _same_loop(entry: _CachedModel, loop: asyncio.AbstractEventLoop | None) -> bool:
    """判断复用记录是否属于当前事件循环。

    用弱引用判等而不是 id：循环回收后 id 会被复用，靠 id 比较会拿到已死循环的客户端。

    Args:
        entry: 已有的复用记录。
        loop: 当前事件循环；None 表示不在循环内。

    Returns:
        同一循环（或都在循环外）时为 True。
    """
    if entry.loop_ref is None:
        return loop is None
    return loop is not None and entry.loop_ref() is loop


def get_or_create_chat_model(config: ModelConfig) -> ChatModelBase:
    """按连接参数取聊天模型；同一循环、同一配置复用已建实例。

    复用的理由：每次构造 `openai` 客户端都要重建 SSL 上下文，单次约 1 s，
    与角色内容无关。跨事件循环不复用——异步客户端与循环绑定，共享会引入
    连接复用风险（每个平台任务在自己线程的循环里跑）。

    Args:
        config: 模型连接参数。

    Returns:
        该配置对应的聊天模型实例。
    """
    key = _config_fingerprint(config)
    loop = _current_loop()
    entry = _MODEL_CACHE.get(key)
    if entry is not None and _same_loop(entry, loop):
        return entry.model
    model = ChatModelFactory(config).create()
    _MODEL_CACHE[key] = _CachedModel(
        loop_ref=None if loop is None else weakref.ref(loop),
        model=model,
    )
    return model


def clear_chat_model_cache() -> None:
    """清空实例复用记录。测试隔离环境变量时使用；运行期无需调用。

    Returns:
        None。
    """
    _MODEL_CACHE.clear()
