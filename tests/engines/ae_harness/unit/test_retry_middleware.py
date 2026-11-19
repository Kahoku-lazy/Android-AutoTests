"""模型调用重试：分类、退避、流式不重放、参数上限。

只测 `middleware/retry.py`；用替身处理函数模拟失败，不联网。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.middleware.retry import (
    MAX_ATTEMPTS_LIMIT,
    ModelRetryMiddleware,
    RetrySettings,
    _env_float,
    _env_int,
    is_transient_model_error,
)

pytestmark = [pytest.mark.unit]


class _ApiError(Exception):
    """带状态码的替身异常。"""

    def __init__(self, status: int) -> None:
        super().__init__(f"status {status}")
        self.status_code = status


class _RateLimitError(Exception):
    """按类型名判定的限流异常。"""


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (_ApiError(429), True),
        (_ApiError(503), True),
        (_ApiError(500), True),
        (_ApiError(400), False),
        (_ApiError(401), False),
        (_ApiError(422), False),
        (_RateLimitError("slow down"), True),
        (TimeoutError("timeout"), True),
        (ConnectionError("reset"), True),
        (ValueError("bad arg"), False),
    ],
)
def test_error_classification(exc: Exception, expected: bool):
    """限流/超时/5xx 可重试；参数与鉴权类不可重试。"""
    assert is_transient_model_error(exc) is expected


def test_fatal_status_wins_over_name():
    """命中黑名单状态码时，即使类型名像可重试也不重试。"""

    class _RateLimitBadRequest(Exception):
        status_code = 400

    assert is_transient_model_error(_RateLimitBadRequest()) is False


def test_settings_env_limits(monkeypatch: pytest.MonkeyPatch):
    """环境变量超上限被截断，非法值回退默认。"""
    monkeypatch.setenv("AE_MODEL_MAX_ATTEMPTS", "99")
    assert RetrySettings.load().max_attempts == MAX_ATTEMPTS_LIMIT

    monkeypatch.setenv("AE_MODEL_MAX_ATTEMPTS", "不是数字")
    assert RetrySettings.load().max_attempts == 3


def test_backoff_is_bounded_and_growing():
    """退避随失败次数增长，且不超过上限。"""
    settings = RetrySettings(max_attempts=8, backoff_base=0.1, backoff_max=0.4)
    assert settings.delay_for(1) < settings.delay_for(3)
    for attempt in range(1, 9):
        assert settings.delay_for(attempt) <= 0.4 * 1.2 + 0.01


def test_env_helpers_clamp(monkeypatch: pytest.MonkeyPatch):
    """两个读环境的辅助函数都做区间夹取。"""
    monkeypatch.setenv("X_INT", "-5")
    assert _env_int("X_INT", 3, 1, 8) == 1
    monkeypatch.setenv("X_FLOAT", "999")
    assert _env_float("X_FLOAT", 0.5, 0.0, 10.0) == 10.0


async def test_non_stream_retries_until_success():
    """非流式：前两次失败、第三次成功，调用方只看得到成功。"""
    attempts: list[int] = []

    async def handler(**_kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise _ApiError(503)
        return "ok"

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=3, backoff_base=0.0))
    result = await middleware.on_model_call(object(), {}, handler)

    assert result == "ok"
    assert len(attempts) == 3


async def test_non_stream_gives_up_after_limit():
    """非流式：次数用尽后上抛原异常。"""
    attempts: list[int] = []

    async def handler(**_kwargs):
        attempts.append(1)
        raise _ApiError(503)

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=2, backoff_base=0.0))
    with pytest.raises(_ApiError):
        await middleware.on_model_call(object(), {}, handler)
    assert len(attempts) == 2


async def test_non_retryable_raises_immediately():
    """不可重试的错误只调用一次。"""
    attempts: list[int] = []

    async def handler(**_kwargs):
        attempts.append(1)
        raise _ApiError(400)

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=5, backoff_base=0.0))
    with pytest.raises(_ApiError):
        await middleware.on_model_call(object(), {}, handler)
    assert len(attempts) == 1


async def test_stream_retries_before_first_chunk():
    """流式：首块之前失败可重试。"""
    calls: list[int] = []

    async def handler(**_kwargs):
        calls.append(1)
        if len(calls) == 1:

            async def bad():
                raise _ApiError(503)
                yield  # pragma: no cover - 只为让它成为异步生成器

            return bad()

        async def good():
            yield "第一块"
            yield "第二块"

        return good()

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=2, backoff_base=0.0))
    stream = await middleware.on_model_call(object(), {}, handler)
    chunks = [chunk async for chunk in stream]

    assert chunks == ["第一块", "第二块"]
    assert len(calls) == 2


async def test_stream_retries_when_the_reopen_itself_fails():
    """流式：重发本身再失败时继续重试，而不是把这次失败直接抛出。"""
    calls: list[int] = []

    async def handler(**_kwargs):
        calls.append(1)

        async def outcome():
            if len(calls) < 3:
                raise _ApiError(503)
            yield "唯一一块"

        return outcome()

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=3, backoff_base=0.0))
    stream = await middleware.on_model_call(object(), {}, handler)
    chunks = [chunk async for chunk in stream]

    assert chunks == ["唯一一块"]
    assert len(calls) == 3


async def test_stream_does_not_replay_after_first_chunk():
    """流式：已产出后失败直接上抛，不重放。"""
    calls: list[int] = []

    async def handler(**_kwargs):
        calls.append(1)

        async def half():
            yield "第一块"
            raise _ApiError(503)

        return half()

    middleware = ModelRetryMiddleware(RetrySettings(max_attempts=5, backoff_base=0.0))
    stream = await middleware.on_model_call(object(), {}, handler)

    received: list[str] = []
    with pytest.raises(_ApiError):
        async for chunk in stream:
            received.append(chunk)

    assert received == ["第一块"]
    assert len(calls) == 1
