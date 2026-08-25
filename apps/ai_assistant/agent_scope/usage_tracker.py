"""Per-conversation model usage tracker — 捕获缓存命中/写入 token。

AgentScope 的 ``ModelCallEndEvent`` 只带 input/output token，缓存字段
（``ChatUsage.cache_input_tokens`` / ``cache_creation_input_tokens``）仅在
模型响应里，故用 ``on_model_call`` 中间件在响应落地前捕获，按 conversation 聚合。
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Awaitable, Callable

from agentscope.middleware import MiddlewareBase

# conversation_id → {"cache_input_tokens", "cache_creation_input_tokens"}
_usage: dict[int, dict[str, int]] = {}


def register(conversation_id: int) -> dict[str, int]:
    """注册一个对话的用量累加器（幂等），返回累加器 dict。"""
    acc = {"cache_input_tokens": 0, "cache_creation_input_tokens": 0}
    _usage[conversation_id] = acc
    return acc


def get(conversation_id: int) -> dict[str, int]:
    """读取对话的缓存用量累加值；未注册返回全 0。"""
    return _usage.get(
        conversation_id,
        {"cache_input_tokens": 0, "cache_creation_input_tokens": 0},
    )


def unregister(conversation_id: int) -> None:
    """清理对话的用量累加器。"""
    _usage.pop(conversation_id, None)


class UsageCaptureMiddleware(MiddlewareBase):
    """在 ``on_model_call`` 钩子捕获 ChatUsage 的缓存字段，累加到注册表。"""

    def __init__(self, acc: dict[str, int]):
        self._acc = acc

    def _capture(self, usage: Any) -> None:
        if usage is None:
            return
        self._acc["cache_input_tokens"] += int(getattr(usage, "cache_input_tokens", 0) or 0)
        self._acc["cache_creation_input_tokens"] += int(
            getattr(usage, "cache_creation_input_tokens", 0) or 0
        )

    async def _capture_stream(self, gen: AsyncGenerator) -> AsyncGenerator:
        async for chunk in gen:
            self._capture(getattr(chunk, "usage", None))
            yield chunk

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Awaitable[Any]],
    ) -> Any:
        result = await next_handler(**input_kwargs)
        if isinstance(result, AsyncGenerator):
            # 流式：包装生成器，逐块捕获 usage（最终块携带完整 usage）
            return self._capture_stream(result)
        self._capture(getattr(result, "usage", None))
        return result
