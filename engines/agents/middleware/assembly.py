"""
python -m 调试路径: engines.agents.middleware.assembly

本模块的业务功能如下：
1. build_agent_middlewares: 按固定顺序装配全部中间件，单项失败只跳过该项。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from agentscope.middleware import MiddlewareBase
from agentscope.model import ChatModelBase

from utils.logs import agent_event_log

from .budget import build_budget_middleware
from .memory import build_memory_middleware
from .model_retry import build_model_retry_middleware, load_retry_settings
from .rag_context import build_rag_middleware
from .tracing import build_tracing_middleware
from .tts import build_tts_middleware


def _safe(builder: Callable[[], object], name: str) -> object | None:
    """执行一个装配器；失败时记警告并跳过，不阻断角色创建。

    Args:
        builder: 无参装配函数。
        name: 能力名，写进警告。

    Returns:
        装配出的中间件；失败或该能力未开启时返回 None。
    """
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001 - 单项配置非法不能拖垮角色创建
        agent_event_log.warning("中间件「%s」装配失败，已跳过：%s", name, exc)
        return None


def build_agent_middlewares(
    *,
    fallback_model: ChatModelBase | None = None,
    with_rag: bool = False,
    with_tts: bool = True,
    extra: Sequence[MiddlewareBase] = (),
) -> list[MiddlewareBase]:
    """按固定顺序装配中间件：最外层在前。

    顺序：链路追踪 → 回复预算 → RAG 上下文 → 语音合成 → 长期记忆入口 → 模型重试。
    追踪放最外，才能把预算触发的收尾也算进同一棵 span；重试放最内，才能只重发
    那一次模型调用、不重放已产出的事件。

    RAG 默认不装配：`data/rag_index` 是产品资料，只有知识类／语音类角色才该带上，
    设备控制角色拿到这些片段只会被带偏。调用方要显式传 `with_rag=True`。

    Args:
        fallback_model: 备用模型；None 表示模型重试不启用回退。
        with_rag: 该角色是否属于知识类／语音类（决定是否尝试装配 RAG）。
        with_tts: 是否允许按全局开关装配语音中间件；语音链路自带 TTS 时传 False。
        extra: 调用方自带的中间件，排在语音之后、重试之前。

    Returns:
        交给 `Agent(middlewares=...)` 的列表，未开启的能力不出现。
    """
    middlewares = [
        _safe(build_tracing_middleware, "链路追踪"),
        _safe(build_budget_middleware, "回复预算"),
        _safe(build_rag_middleware, "RAG 上下文") if with_rag else None,
        _safe(build_tts_middleware, "语音合成") if with_tts else None,
        _safe(build_memory_middleware, "长期记忆"),
        *extra,
        _safe(
            lambda: build_model_retry_middleware(
                load_retry_settings(),
                fallback_model=fallback_model,
            ),
            "模型重试与回退",
        ),
    ]
    return [item for item in middlewares if item is not None]
