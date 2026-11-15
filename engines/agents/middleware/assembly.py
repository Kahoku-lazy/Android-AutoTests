"""
文件名: ➡️ assembly.py 🏁
路径: ➡️ engines/agents/middleware/assembly.py 🏁
模块功能：➡️ 聊天助手默认中间件：事件流在外，模型重试在内 🏁
Python 调试：➡️ python -m engines.agents.middleware.assembly 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. build_agent_middlewares: 默认装配事件流、交卷关思考与模型重试。
2. 不装配链路追踪、语音合成、长期记忆，也不按 token 量禁工具。
🏁
关联模块：➡️
1. engines.agents.middleware.reply_events: 导入 ReplyEventsMiddleware
2. engines.agents.middleware.handover: 导入 ForcedHandoverMiddleware
3. engines.agents.middleware.model_retry: 导入重试装配
4. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/engines/agents/unit/test_agent_middleware_assembly.py: 默认只剩事件流与重试
🏁
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from agentscope.middleware import MiddlewareBase
from agentscope.model import ChatModelBase

from utils.logs import agent_event_log

from .handover import ForcedHandoverMiddleware
from .model_retry import build_model_retry_middleware, load_retry_settings
from .reply_events import ReplyEventsMiddleware


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
    extra: Sequence[MiddlewareBase] = (),
    with_events: bool = True,
) -> list[MiddlewareBase]:
    """按固定顺序装配中间件：事件流在外，模型重试在内。

    事件流只给没有外层记录的聊天助手。SOP 自己折叠事件，传入
    `with_events=False`，避免同一条事件写两遍。

    不装配链路追踪、语音合成和长期记忆。单步收敛只由 ReAct 轮次上限决定，
    这里 MUST NOT 再按 token 量把 `tool_choice` 改成 `none`。

    Args:
        fallback_model: 备用模型；None 表示模型重试不启用回退。
        extra: 调用方自带的中间件，排在事件流之后、重试之前。
        with_events: 是否挂回复事件流。SOP 传 False。

    Returns:
        交给 `Agent(middlewares=...)` 的列表。重试未开启时不出现。
    """
    middlewares = [
        ReplyEventsMiddleware() if with_events else None,
        *extra,
        ForcedHandoverMiddleware(),
        _safe(
            lambda: build_model_retry_middleware(
                load_retry_settings(),
                fallback_model=fallback_model,
            ),
            "模型重试与回退",
        ),
    ]
    return [item for item in middlewares if item is not None]
