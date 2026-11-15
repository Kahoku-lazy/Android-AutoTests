"""
文件名: ➡️ handover.py 🏁
路径: ➡️ engines/agents/middleware/handover.py 🏁
模块功能：➡️ 强制结构化交卷那一次关闭思考，其余请求原样返回 🏁
Python 调试：➡️ python -m engines.agents.middleware.handover 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. apply_forced_handover_kwargs: 只改写强制交卷请求的 thinking，其余原样返回。
2. ForcedHandoverMiddleware: 在模型调用前改写请求，不包装模型实例。
🏁
关联模块：➡️
1. 无本地依赖：只使用 agentscope 的中间件基类。
🏁
测试：➡️
1. tests/engines/agents/unit/test_forced_handover_thinking.py: 强制交卷关闭思考，未满轮次请求保持原样
🏁
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from agentscope.middleware import MiddlewareBase

__all__ = ["ForcedHandoverMiddleware", "apply_forced_handover_kwargs"]

# 框架在自由推理用尽后，会把工具选择强制成这个名字。
_FORCED_HANDOVER_TOOL = "GenerateStructuredOutput"


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
    merged: dict[str, Any] = {**base, **incoming, "thinking": thinking}
    return {**kwargs, "extra_body": merged}


class ForcedHandoverMiddleware(MiddlewareBase):
    """
    在模型调用前改写强制交卷请求。

    改写是纯函数，不包装模型，所以同一聊天模型交给多个智能体也不会叠包装。

    Attributes:
        无。
    """

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Awaitable[Any]],
    ) -> Any:
        """
        强制交卷时关闭思考，然后把改写后的参数交给下一层。

        Args:
            agent: 发起调用的智能体。
            input_kwargs: 含 `current_model` / `tool_choice` / `extra_body`。
            next_handler: 调用链里的下一层。

        Returns:
            下一层的模型响应。
        """
        model = input_kwargs.get("current_model") or getattr(agent, "model", None)
        kwargs = apply_forced_handover_kwargs(model, input_kwargs.get("tool_choice"), input_kwargs)
        return await next_handler(**kwargs)
