"""
文件名: ➡️ create.py 🏁
路径: ➡️ engines/agents/models/create.py 🏁
模块功能：➡️ 唯一出口 create_model：从整张表里取一条，校验后创建模型 🏁
Python 调试：➡️ python -m engines.agents.models.create 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 3.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. create_model: 本包唯一出口——按短名取条目、校验、创建模型实例。
2. _create_chat / _create_realtime / _create_tts / _create_embedding: 四族构造，内部使用。DeepSeek 看图用原生客户端。
3. 密钥只从条目的 api_key 取：对象由 config 加密注入，这里只调 reveal()。
4. 不读文件、不读环境变量、不做缓存：调用哪个模型由 agent 决定。
🏁
关联模块：➡️
1. engines.agents.models.loader: 导入 parse，按族校验并返回参数对象。
2. engines.agents.models.schema: 导入三个参数类与 ModelConfigError。
🏁
测试：➡️
1. 待功能定型后补：四族创建、视觉选路与密钥打码
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agentscope.credential import (
    DashScopeCredential,
    DeepSeekCredential,
)
from agentscope.embedding import DashScopeEmbeddingModel
from agentscope.formatter import (
    DashScopeChatFormatter,
    DashScopeMultiAgentFormatter,
    DeepSeekChatFormatter,
    DeepSeekMultiAgentFormatter,
)
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
)
from agentscope.tts import DashScopeTTSModel

from .loader import parse
from .schema import (
    ChatModelSchema,
    EmbeddingModelSchema,
    ModelConfigError,
    RealtimeModelSchema,
)

__all__ = ["create_model"]

# 各族未配置 context_size 时的兜底窗口。
_DEEPSEEK_TEXT_CONTEXT = 65536
_DASHSCOPE_CHAT_CONTEXT = 131072
_DASHSCOPE_EMBEDDING_CONTEXT = 8192

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def _credential(entry: Any, cls: type, base_url: str = ""):
    """
    构造凭证：只在这一次调用里调 reveal() 取明文。

    Args:
        entry: 已校验的参数对象（带 config 注入的 api_key）。
        cls: 凭证类。
        base_url: 基础地址；空串表示用 provider 默认。

    Returns:
        凭证实例。

    Raises:
        ModelConfigError: 该条目的密钥没配到（环境变量为空）或密文非法。
    """
    try:
        plain = entry.api_key.reveal()
    except ValueError as exc:
        # 缺密钥不阻断装载，报错推迟到这里：消息带上模型名，类型统一成 ModelConfigError。
        raise ModelConfigError(f"{entry.model_name}: {exc}") from exc
    if base_url:
        return cls(api_key=plain, base_url=base_url)
    return cls(api_key=plain)


def _parameters(entry: ChatModelSchema, parameters_cls: type | None) -> Any:
    """
    构造框架 Parameters；没配参数时返回 None。

    Args:
        entry: 已校验的聊天模型参数。
        parameters_cls: 该客户端类的 Parameters 类。

    Returns:
        Parameters 实例或 None。

    Raises:
        ModelConfigError: 参数不被该客户端类接受。
    """
    if not entry.parameters or parameters_cls is None:
        return None
    try:
        return parameters_cls(**entry.parameters)
    except TypeError as exc:
        raise ModelConfigError(
            f"{entry.model_name}.parameters: 参数不被 {parameters_cls.__qualname__} 接受：{exc}",
        ) from exc


def _chat_formatter(entry: ChatModelSchema) -> Any:
    """
    按 provider 与 formatter 取格式化器实例。

    图片类型必须写进 formatter.input_types。框架默认只有 text/plain，
    不写的话截图会被格式化器丢掉，模型看不到图。

    Args:
        entry: 已校验的聊天模型参数。

    Returns:
        格式化器实例。
    """
    multi = entry.formatter == "multi_agent"
    if entry.provider == "deepseek":
        formatter_cls = DeepSeekMultiAgentFormatter if multi else DeepSeekChatFormatter
    else:
        formatter_cls = DashScopeMultiAgentFormatter if multi else DashScopeChatFormatter
    return formatter_cls(input_types=list(entry.input_types))


def _stream(stream: bool | None) -> bool:
    """
    取流式开关。

    Args:
        stream: 调用方传入的覆盖值；None 表示用默认。

    Returns:
        最终布尔值（默认 True）。
    """
    return True if stream is None else stream


def _context_size(entry: ChatModelSchema, default: int) -> int:
    """
    取上下文窗口：条目 > provider 默认。

    Args:
        entry: 已校验的聊天模型参数。
        default: 条目没写时的默认窗口。

    Returns:
        最终窗口大小。
    """
    return entry.context_size or default


def _deepseek_chat(entry: ChatModelSchema, stream: bool | None) -> DeepSeekChatModel:
    """
    建 DeepSeek 聊天模型。2.0.9 的原生类已能看图，不再换成 OpenAI 客户端。

    Args:
        entry: 已校验的聊天模型参数。
        stream: 流式开关覆盖值。

    Returns:
        DeepSeekChatModel 实例。
    """
    return DeepSeekChatModel(
        credential=_credential(entry, DeepSeekCredential, entry.base_url or _DEEPSEEK_BASE_URL),
        model=entry.model_name,
        parameters=_parameters(entry, DeepSeekChatModel.Parameters),
        stream=_stream(stream),
        max_retries=entry.max_retries,
        context_size=_context_size(entry, _DEEPSEEK_TEXT_CONTEXT),
        formatter=_chat_formatter(entry),
    )


def _dashscope_chat(entry: ChatModelSchema, stream: bool | None) -> DashScopeChatModel:
    """
    建 DashScope 聊天模型（原生支持图片，不需要单独的视觉档）。

    Args:
        entry: 已校验的聊天模型参数。
        stream: 流式开关覆盖值。

    Returns:
        DashScopeChatModel 实例。
    """
    return DashScopeChatModel(
        credential=_credential(entry, DashScopeCredential),
        model=entry.model_name,
        parameters=_parameters(entry, DashScopeChatModel.Parameters),
        stream=_stream(stream),
        max_retries=entry.max_retries,
        context_size=_context_size(entry, _DASHSCOPE_CHAT_CONTEXT),
        formatter=_chat_formatter(entry),
    )


def _create_chat(entry: ChatModelSchema, *, stream: bool | None = None) -> ChatModelBase:
    """
    建聊天模型。DeepSeek 看图不再换客户端，图片类型交给格式化器。

    Args:
        entry: 已校验的聊天模型参数。
        stream: 流式开关覆盖值；None 用默认（True）。

    Returns:
        聊天模型实例。

    Raises:
        ModelConfigError: provider 不受支持，或参数不被客户端类接受。
    """
    if entry.provider == "deepseek":
        return _deepseek_chat(entry, stream)
    if entry.provider == "dashscope":
        return _dashscope_chat(entry, stream)
    raise ModelConfigError(f"chat 族不支持的 provider：{entry.provider!r}")


def _create_realtime(entry: RealtimeModelSchema):
    """
    建 Omni 实时语音模型（额外依赖延迟导入）。

    Args:
        entry: 已校验的语音模型参数。

    Returns:
        DashScopeRealtimeModel 实例。

    Raises:
        ModelConfigError: provider 不是 dashscope，或未安装 agentscope[realtime]。
    """
    if entry.provider != "dashscope":
        raise ModelConfigError(f"realtime 族只支持 dashscope，收到 {entry.provider!r}")
    try:
        from agentscope.realtime import DashScopeRealtimeModel
    except ImportError as exc:
        raise ModelConfigError(
            '创建实时语音模型需要额外依赖：pip install "agentscope[realtime]"',
        ) from exc
    values: dict[str, Any] = {}
    if entry.voice:
        values["voice"] = entry.voice
    return DashScopeRealtimeModel(
        model=entry.model_name,
        credential=_credential(entry, DashScopeCredential),
        parameters=DashScopeRealtimeModel.Parameters(**values),
    )


def _create_tts(entry: RealtimeModelSchema) -> DashScopeTTSModel:
    """
    建语音合成模型（默认流式合成）。

    Args:
        entry: 已校验的语音模型参数。

    Returns:
        DashScopeTTSModel 实例。

    Raises:
        ModelConfigError: provider 不是 dashscope，或音色不被接受。
    """
    if entry.provider != "dashscope":
        raise ModelConfigError(f"tts 族只支持 dashscope，收到 {entry.provider!r}")
    values: dict[str, Any] = {}
    if entry.voice:
        values["voice"] = entry.voice
    try:
        parameters = DashScopeTTSModel.Parameters(**values)
    except TypeError as exc:
        raise ModelConfigError(f"{entry.model_name}.voice: 音色不被接受：{exc}") from exc
    return DashScopeTTSModel(
        credential=_credential(entry, DashScopeCredential),
        model=entry.model_name,
        parameters=parameters,
        stream=True,
    )


def _create_embedding(entry: EmbeddingModelSchema) -> DashScopeEmbeddingModel:
    """
    建向量模型。

    Args:
        entry: 已校验的向量模型参数。

    Returns:
        DashScopeEmbeddingModel 实例。

    Raises:
        ModelConfigError: provider 不是 dashscope。
    """
    if entry.provider != "dashscope":
        raise ModelConfigError(f"embedding 族只支持 dashscope，收到 {entry.provider!r}")
    return DashScopeEmbeddingModel(
        credential=_credential(entry, DashScopeCredential),
        model=entry.model_name,
        dimensions=entry.dimensions,
        context_size=_DASHSCOPE_EMBEDDING_CONTEXT,
    )


def create_model(
    catalog: Mapping[str, Any],
    short_name: str,
    *,
    stream: bool | None = None,
) -> object:
    """
    从整张模型表里取一条，校验后创建模型（本包唯一出口）。

    用哪个模型由调用方（agent）决定；这里只负责「这条配置能不能用、能不能建出来」。

    Args:
        catalog: config 读好的整张模型表（条目里已注入加密密钥）。
        short_name: 模型短名，如 `deepseek_flash`。
        stream: 聊天族的流式开关覆盖值；其余族忽略。

    Returns:
        框架模型实例。

    Raises:
        ModelConfigError: 短名不存在、条目非法，或族不支持。
    """
    entry = parse(catalog, short_name)
    if isinstance(entry, ChatModelSchema):
        return _create_chat(entry, stream=stream)
    if isinstance(entry, EmbeddingModelSchema):
        return _create_embedding(entry)
    if isinstance(entry, RealtimeModelSchema):
        if entry.family == "realtime":
            return _create_realtime(entry)
        return _create_tts(entry)
    raise ModelConfigError(f"{short_name}: 无法识别族的参数对象 {type(entry).__name__}")
