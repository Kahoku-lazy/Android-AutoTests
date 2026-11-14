"""运行控制：次数上限、时长上限、取消、异常可区分。

只测 `middleware/control.py`；用替身处理函数，不联网。
"""

from __future__ import annotations

import time

import pytest

from engines.ae_harness.middleware.control import (
    BudgetExceeded,
    BudgetMiddleware,
    CancelMiddleware,
    CancelToken,
    RunBudget,
    RunCancelled,
)

pytestmark = [pytest.mark.unit]


async def _passthrough(**_kwargs):
    """替身：下一层永远成功。"""
    return "ok"


def test_budget_counts_and_stops():
    """次数上限：用满后再检查就抛，且异常类型可识别。"""
    budget = RunBudget(max_model_calls=2)
    budget.consume()
    budget.check()
    budget.consume()
    with pytest.raises(BudgetExceeded):
        budget.check()


def test_budget_seconds_stops():
    """时长上限：超过就抛。"""
    budget = RunBudget(max_seconds=0.01)
    time.sleep(0.02)
    with pytest.raises(BudgetExceeded):
        budget.check()


def test_budget_without_limits_never_raises():
    """不设上限时永不停。"""
    budget = RunBudget()
    for _ in range(100):
        budget.check()
        budget.consume()


async def test_budget_middleware_allows_within_limit():
    """未超限时放行并计数。"""
    budget = RunBudget(max_model_calls=3)
    middleware = BudgetMiddleware(budget)

    assert await middleware.on_model_call(object(), {}, _passthrough) == "ok"
    assert budget.calls == 1


async def test_budget_middleware_raises_before_call():
    """超限时在调用前抛出，下一层不会被调用。"""
    calls: list[int] = []

    async def handler(**_kwargs):
        calls.append(1)
        return "ok"

    budget = RunBudget(max_model_calls=1)
    middleware = BudgetMiddleware(budget)

    await middleware.on_model_call(object(), {}, handler)
    with pytest.raises(BudgetExceeded):
        await middleware.on_model_call(object(), {}, handler)
    assert len(calls) == 1


def test_cancel_token_set_and_check():
    """置位后检查抛取消异常，复位后可再用。"""
    token = CancelToken()
    token.check()
    token.cancel("用户点了停止")
    with pytest.raises(RunCancelled, match="用户点了停止"):
        token.check()
    token.clear()
    token.check()


def test_budget_and_cancel_are_different_types():
    """预算与取消必须是不同异常类型，便于分别统计。"""
    assert BudgetExceeded is not RunCancelled
    assert not issubclass(BudgetExceeded, RunCancelled)
    assert not issubclass(RunCancelled, BudgetExceeded)


async def test_cancel_middleware_raises_before_call():
    """取消令牌置位后，下一次模型调用前抛出且不调用下一层。"""
    calls: list[int] = []

    async def handler(**_kwargs):
        calls.append(1)
        return "ok"

    token = CancelToken()
    middleware = CancelMiddleware(token)

    await middleware.on_model_call(object(), {}, handler)
    token.cancel()
    with pytest.raises(RunCancelled):
        await middleware.on_model_call(object(), {}, handler)
    assert len(calls) == 1


async def test_cancel_from_other_thread():
    """取消可以被另一个线程置位（SOP 在线程里跑的场景）。"""
    import threading

    token = CancelToken()
    worker = threading.Thread(target=lambda: token.cancel("外部线程"))
    worker.start()
    worker.join()

    assert token.cancelled is True
    with pytest.raises(RunCancelled):
        CancelMiddleware(token).check() if hasattr(
            CancelMiddleware(token), "check"
        ) else token.check()
