"""
文件名: ➡️ control.py 🏁
路径: ➡️ engines/ae_harness/middleware/control.py 🏁
模块功能：➡️ 运行控制：模型调用次数/时长预算与外部取消 🏁
Python 调试：➡️ python -m engines.ae_harness.middleware.control 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RunBudget: 一次运行的两个上限——模型调用次数与墙钟秒数；超限抛 BudgetExceeded。
2. CancelToken: 跨线程置位的取消令牌；被取消抛 RunCancelled。
3. BudgetMiddleware / CancelMiddleware: 在每次模型调用前判定，只做「提前中止」，不扩展能力。
🏁
关联模块：➡️
1. 无本地依赖：只依赖标准库与框架的中间件基类。
🏁
测试：➡️
1. 暂无
🏁
"""

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
    """运行预算耗尽。调用方应记为「中止」，而不是「失败」。"""


class RunCancelled(RuntimeError):
    """运行被外部取消。与预算耗尽区分开，便于分别统计。"""


@dataclass
class RunBudget:
    """
    一次运行的上限。

    Attributes:
        max_model_calls: 最多调用几次模型；None 表示不限。
        max_seconds: 最长跑多少秒；None 表示不限。
        calls: 已用调用次数。
        started_at: 计时起点（单调时钟）。
    """

    max_model_calls: int | None = None
    max_seconds: float | None = None
    calls: int = 0
    started_at: float = field(default_factory=time.perf_counter)

    def check(self) -> None:
        """
        判定是否已经超限，超限就抛。

        Raises:
            BudgetExceeded: 次数或时长超限。
        """
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
        """
        已经跑了多少秒。

        Returns:
            从计时起点到现在的秒数。
        """
        return time.perf_counter() - self.started_at

    def consume(self) -> None:
        """记一次模型调用。"""
        self.calls += 1


@dataclass
class CancelToken:
    """
    跨线程取消令牌。

    Attributes:
        event: 置位即表示要停。
        reason: 取消原因，写进异常消息。
    """

    event: threading.Event = field(default_factory=threading.Event)
    reason: str = ""

    def cancel(self, reason: str = "用户取消") -> None:
        """
        置位取消。

        Args:
            reason: 取消原因。
        """
        self.reason = reason
        self.event.set()

    def clear(self) -> None:
        """复位，便于复用同一个令牌。"""
        self.reason = ""
        self.event.clear()

    @property
    def cancelled(self) -> bool:
        """
        是否已取消。

        Returns:
            已置位返回 True。
        """
        return self.event.is_set()

    def check(self) -> None:
        """
        已取消就抛。

        Raises:
            RunCancelled: 令牌已置位。
        """
        if self.cancelled:
            raise RunCancelled(self.reason or "运行已取消")


class BudgetMiddleware(MiddlewareBase):
    """每次模型调用前检查预算；超限抛 `BudgetExceeded`。"""

    def __init__(self, budget: RunBudget) -> None:
        """
        记录预算对象。

        Args:
            budget: 共享的预算实例；同一轮内所有角色应传同一个。
        """
        self.budget = budget

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        """
        调用前判预算，通过后计数并放行。

        Args:
            agent: 当前智能体。
            input_kwargs: 参数。
            next_handler: 下一层调用。

        Returns:
            下一层的结果。

        Raises:
            BudgetExceeded: 次数或时长超限。
        """
        del agent
        self.budget.check()
        self.budget.consume()
        return await next_handler(**input_kwargs)


class CancelMiddleware(MiddlewareBase):
    """每次模型调用前检查取消令牌；已置位抛 `RunCancelled`。"""

    def __init__(self, token: CancelToken) -> None:
        """
        记录取消令牌。

        Args:
            token: 共享的取消令牌；外部从别的线程置位。
        """
        self.token = token

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        """
        调用前判取消，通过后放行。

        Args:
            agent: 当前智能体。
            input_kwargs: 参数。
            next_handler: 下一层调用。

        Returns:
            下一层的结果。

        Raises:
            RunCancelled: 令牌已置位。
        """
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
