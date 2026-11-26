from __future__ import annotations

import threading
import time

from dataclasses import dataclass, field
from typing import Any, Callable

from agentscope.middleware import MiddlewareBase

__all__ = [
    "BudgetExceeded",
    "BudgetMiddleware",
    "CancelMiddleware",
    "CancelToken",
    "RunBudget",
]


class BudgetExceeded(RuntimeError):
    pass


class RunCancelled(RuntimeError):
    pass


@dataclass
class RunBudget:
    max_model_calls: int | None = None
    max_seconds: float | None = None
    calls: int = 0
    started_at: float = field(default_factory=time.perf_counter)

    def check(self) -> None:
        if self.max_model_calls is not None and self.calls >= self.max_model_calls:
            raise BudgetExceeded(
                f"模型调用次数已达上限 {self.max_model_calls}（已用 {self.calls} 次）"
            )
        if self.max_seconds is not None and self.elapsed > self.max_seconds:
            raise BudgetExceeded(
                f"运行时长已达上限 {self.max_seconds:.0f} 秒（已用 {self.elapsed:.1f} 秒）"
            )

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.started_at

    def consume(self) -> None:
        self.calls += 1


@dataclass
class CancelToken:
    event: threading.Event = field(default_factory=threading.Event)
    reason: str = ""

    def cancel(self, reason: str = "用户取消") -> None:
        self.reason = reason
        self.event.set()

    def clear(self) -> None:
        self.reason = ""
        self.event.clear()

    @property
    def cancelled(self) -> bool:
        return self.event.is_set()

    def check(self) -> None:
        if self.cancelled:
            raise RunCancelled(self.reason or "运行已取消")


class BudgetMiddleware(MiddlewareBase):
    def __init__(self, budget: RunBudget) -> None:
        self.budget = budget

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        del agent
        self.budget.check()
        self.budget.consume()
        return await next_handler(**input_kwargs)


class CancelMiddleware(MiddlewareBase):
    def __init__(self, token: CancelToken) -> None:
        self.token = token

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        del agent
        self.token.check()
        return await next_handler(**input_kwargs)


if __name__ == "__main__":
    budget = RunBudget(max_model_calls=1)
    budget.consume()
    try:
        budget.check()
    except BudgetExceeded as exc:
        print("预算示例:", exc)  # noqa: T201 - 模块自测入口
