"""模型重试与回退中间件：分类判定、退避序列、回退、流式首块、环境变量解析。"""

from __future__ import annotations

import asyncio

import pytest

from engines.agents.event_sink import bind_sink, reset_sink
from engines.agents.middleware import build_model_retry_middleware, load_retry_settings
from engines.agents.middleware.model_retry import (
    ModelRetryMiddleware,
    RetrySettings,
    is_transient_model_error,
)

pytestmark = [pytest.mark.unit]


class _Model:
    """只有 model 属性的假模型，够日志与回退判定用。"""

    def __init__(self, name: str) -> None:
        self.model = name


class _HttpError(Exception):
    """带状态码的假 HTTP 异常。"""

    def __init__(self, status: int, message: str = "boom") -> None:
        super().__init__(message)
        self.status_code = status


class _Recorder:
    """记录等待时长与日志行。"""

    def __init__(self) -> None:
        self.delays: list[float] = []
        self.warnings: list[str] = []

    async def sleep(self, delay: float) -> None:
        self.delays.append(delay)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


class _Sink:
    """收集中间件写给任务事件流的记录；boom 时模拟接收方故障。"""

    def __init__(self, boom: bool = False) -> None:
        self.records: list = []
        self.boom = boom

    def emit(self, record, image_b64: str = "") -> None:
        if self.boom:
            raise RuntimeError("sink down")
        self.records.append(record)


class _Agent:
    """只有 name 属性的假智能体。"""

    def __init__(self, name: str = "executor_role") -> None:
        self.name = name


def _handler(script: list) -> tuple:
    """按脚本逐次返回或抛错的 next_handler，并记录每次用的模型。"""
    calls: list[str] = []

    async def next_handler(**kwargs):
        model = kwargs.get("current_model")
        calls.append(getattr(model, "model", "-"))
        step = script.pop(0) if script else RuntimeError("脚本已用尽")
        if isinstance(step, BaseException):
            raise step
        return step

    return next_handler, calls


def _middleware(recorder: _Recorder, **kwargs) -> ModelRetryMiddleware:
    """装配一个把等待与日志都记到 recorder 的中间件。"""
    return ModelRetryMiddleware(sleep=recorder.sleep, log=recorder, **kwargs)


async def _collect(stream) -> list:
    """收集异步流里的全部内容。"""
    return [chunk async for chunk in stream]


async def _stream(chunks: list, fail_after: int | None = None):
    """依次吐出内容；到 fail_after 位置先抛 502。"""
    for index, chunk in enumerate(chunks):
        if fail_after is not None and index == fail_after:
            raise _HttpError(502)
        yield chunk


# ── 分类判定 ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (_HttpError(429), True),
        (_HttpError(503), True),
        (_HttpError(500), True),
        (_HttpError(408), True),
        (_HttpError(401), False),
        (_HttpError(400), False),
        (_HttpError(404), False),
        (_HttpError(418), False),
        (asyncio.TimeoutError(), True),
        (ConnectionResetError("Connection reset by peer"), True),
        (RuntimeError("rate limit exceeded"), True),
        (ValueError("bad payload"), False),
        (TypeError("unexpected kwarg"), False),
    ],
)
def test_transient_classification(exc: BaseException, expected: bool) -> None:
    assert is_transient_model_error(exc) is expected


# ── 重试 ──────────────────────────────────────────────────


async def test_non_transient_error_is_not_retried() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(401)])
    middleware = _middleware(recorder, attempts=3)

    with pytest.raises(_HttpError):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert calls == ["primary"]
    assert recorder.delays == []


async def test_transient_error_retried_then_succeeds() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(503), "ok"])
    middleware = _middleware(recorder, attempts=2, base_delay=0.5)

    result = await middleware.on_model_call(
        agent=None,
        input_kwargs={"current_model": _Model("primary")},
        next_handler=handler,
    )

    assert result == "ok"
    assert calls == ["primary", "primary"]
    assert recorder.delays == [0.5]
    assert any("重试" in line for line in recorder.warnings)


async def test_retries_exhausted_raise_last_error() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(503), _HttpError(503)])
    middleware = _middleware(recorder, attempts=2, base_delay=0.5)

    with pytest.raises(_HttpError):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert calls == ["primary", "primary"]


async def test_backoff_doubles_and_caps() -> None:
    recorder = _Recorder()
    handler, _ = _handler([_HttpError(503)] * 4)
    middleware = _middleware(recorder, attempts=4, base_delay=0.5, max_delay=0.75)

    with pytest.raises(_HttpError):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert recorder.delays == [0.5, 0.75, 0.75]


# ── 回退 ──────────────────────────────────────────────────


async def test_fallback_used_after_primary_exhausted() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(503), _HttpError(503), "from-fallback"])
    middleware = _middleware(
        recorder,
        attempts=2,
        base_delay=0.5,
        fallback_model=_Model("backup"),
    )

    result = await middleware.on_model_call(
        agent=None,
        input_kwargs={"current_model": _Model("primary")},
        next_handler=handler,
    )

    assert result == "from-fallback"
    assert calls == ["primary", "primary", "backup"]
    assert any("回退" in line for line in recorder.warnings)


async def test_fallback_also_failing_raises_last_error() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(503), _HttpError(503), _HttpError(502), _HttpError(502)])
    middleware = _middleware(
        recorder,
        attempts=2,
        base_delay=0.5,
        fallback_model=_Model("backup"),
    )

    with pytest.raises(_HttpError):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert calls == ["primary", "primary", "backup", "backup"]


async def test_non_transient_error_skips_fallback() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(401), "should-not-run"])
    middleware = _middleware(
        recorder,
        attempts=3,
        fallback_model=_Model("backup"),
    )

    with pytest.raises(_HttpError):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert calls == ["primary"]


# ── 流式 ──────────────────────────────────────────────────


async def test_stream_failure_before_first_chunk_is_retried() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_stream(["a", "b"], fail_after=0), _stream(["a", "b"])])
    middleware = _middleware(recorder, attempts=2, base_delay=0.5)

    stream = await middleware.on_model_call(
        agent=None,
        input_kwargs={"current_model": _Model("primary")},
        next_handler=handler,
    )

    assert await _collect(stream) == ["a", "b"]
    assert calls == ["primary", "primary"]
    assert recorder.delays == [0.5]


async def test_stream_failure_after_first_chunk_is_not_retried() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_stream(["a", "b"], fail_after=1)])
    middleware = _middleware(recorder, attempts=3, base_delay=0.5)

    stream = await middleware.on_model_call(
        agent=None,
        input_kwargs={"current_model": _Model("primary")},
        next_handler=handler,
    )

    with pytest.raises(_HttpError):
        await _collect(stream)

    assert calls == ["primary"]
    assert recorder.delays == []


async def test_empty_stream_is_reported_without_retry() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_stream([]), "unused"])
    middleware = _middleware(recorder, attempts=3, base_delay=0.5)

    with pytest.raises(RuntimeError, match="流式响应为空"):
        await middleware.on_model_call(
            agent=None,
            input_kwargs={"current_model": _Model("primary")},
            next_handler=handler,
        )

    assert calls == ["primary"]


# ── 参数与装配 ─────────────────────────────────────────────


def test_invalid_attempts_rejected() -> None:
    with pytest.raises(ValueError):
        ModelRetryMiddleware(attempts=0)


def test_invalid_delays_rejected() -> None:
    with pytest.raises(ValueError):
        ModelRetryMiddleware(base_delay=1.0, max_delay=0.5)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "AGENT_MODEL_RETRY_ATTEMPTS",
        "AGENT_MODEL_RETRY_BASE_DELAY_MS",
        "AGENT_MODEL_RETRY_MAX_DELAY_MS",
        "AGENT_FALLBACK_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_retry_settings()

    assert settings.attempts == 2
    assert settings.base_delay == 0.8
    assert settings.max_delay == 8.0
    assert settings.enabled is True


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODEL_RETRY_ATTEMPTS", "4")
    monkeypatch.setenv("AGENT_MODEL_RETRY_BASE_DELAY_MS", "1000")
    monkeypatch.setenv("AGENT_MODEL_RETRY_MAX_DELAY_MS", "4000")
    monkeypatch.setenv("AGENT_FALLBACK_MODEL", "deepseek-pro")
    monkeypatch.setenv("AGENT_FALLBACK_PROVIDER", "deepseek")

    settings = load_retry_settings()

    assert settings.attempts == 4
    assert settings.base_delay == 1.0
    assert settings.max_delay == 4.0
    assert settings.fallback_model_name == "deepseek-pro"
    assert "secret" not in repr(RetrySettings(attempts=1, fallback_api_key="secret"))


def test_disabled_settings_build_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODEL_RETRY_ATTEMPTS", "1")
    monkeypatch.delenv("AGENT_FALLBACK_MODEL", raising=False)

    settings = load_retry_settings()

    assert settings.enabled is False
    assert build_model_retry_middleware(settings) is None


def test_enabled_settings_build_middleware_with_fallback() -> None:
    settings = RetrySettings(attempts=3, fallback_model_name="backup-model")
    fallback = _Model("backup")

    middleware = build_model_retry_middleware(settings, fallback_model=fallback)

    assert middleware is not None
    assert middleware.attempts == 3
    assert middleware.fallback_model is fallback


# ── 角色装配 ──────────────────────────────────────────────


def _build_role():
    """用假密钥建一个最小角色，只在构造期验证装配，不发请求。"""
    from agentscope.tool import Toolkit

    from engines.agents.role.base import AgentRoleConfig, BaseRole

    config, role = AgentRoleConfig(
        provider="deepseek",
        model_name="deepseek-flash",
        base_url="https://api.deepseek.com/v1",
        api_key="test-key",
        name="probe_role",
        system_prompt="probe",
        toolkit=Toolkit(),
        vision=False,
    ).load_config()
    return BaseRole(config, role)


def test_base_role_wires_middleware_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODEL_RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("AGENT_FALLBACK_MODEL", "deepseek-pro")

    role = _build_role()
    middlewares = role._middlewares()

    assert [type(item).__name__ for item in middlewares] == [
        "ReplyBudgetControlMiddleware",
        "ModelRetryMiddleware",
    ]
    assert middlewares[-1].fallback_model.model == "deepseek-pro"
    # Agent 只把实现了 on_model_call 的中间件放进模型调用链，预算中间件不在其中
    assert [type(item).__name__ for item in role.agent._model_call_middlewares] == [
        "ModelRetryMiddleware"
    ]


def test_base_role_skips_middleware_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODEL_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("AGENT_REPLY_TOKEN_BUDGET", "0")
    monkeypatch.delenv("AGENT_FALLBACK_MODEL", raising=False)
    monkeypatch.delenv("AGENT_TTS_MIDDLEWARE", raising=False)
    monkeypatch.delenv("AGENT_RAG_ENABLED", raising=False)
    monkeypatch.delenv("AGENT_TRACING_OTLP_ENDPOINT", raising=False)

    assert _build_role()._middlewares() == []


# ── 任务事件流 ────────────────────────────────────────────


async def _run_with_sink(handler, middleware, sink) -> object:
    """绑定假接收方跑一次调用，结束后还原接收方。"""
    token = bind_sink(sink)
    try:
        return await middleware.on_model_call(
            agent=_Agent(),
            input_kwargs={"current_model": _Model("deepseek-flash")},
            next_handler=handler,
        )
    finally:
        reset_sink(token)


async def test_retry_writes_event_record() -> None:
    recorder = _Recorder()
    sink = _Sink()
    handler, _ = _handler([_HttpError(503), "ok"])
    middleware = _middleware(recorder, attempts=2, base_delay=0.5)

    await _run_with_sink(handler, middleware, sink)

    assert [record.event_type for record in sink.records] == ["ModelRetryEvent"]
    record = sink.records[0]
    assert record.phase == "推理"
    assert record.block_type == "retry"
    assert record.role_name == "executor_role"
    assert record.model == "deepseek-flash"
    assert record.payload == {
        "attempt": 1,
        "attempts": 2,
        "delay_ms": 500,
        "reason": "_HttpError: boom",
    }


async def test_fallback_writes_event_after_retries() -> None:
    recorder = _Recorder()
    sink = _Sink()
    handler, _ = _handler([_HttpError(503), _HttpError(503), "from-fallback"])
    middleware = _middleware(
        recorder,
        attempts=2,
        base_delay=0.5,
        fallback_model=_Model("deepseek-pro"),
    )

    result = await _run_with_sink(handler, middleware, sink)

    assert result == "from-fallback"
    assert [record.event_type for record in sink.records] == [
        "ModelRetryEvent",
        "ModelFallbackEvent",
    ]
    assert sink.records[1].payload == {
        "from_model": "deepseek-flash",
        "to_model": "deepseek-pro",
        "attempts": 2,
    }


async def test_sink_failure_does_not_block_retry() -> None:
    recorder = _Recorder()
    handler, calls = _handler([_HttpError(503), "ok"])
    middleware = _middleware(recorder, attempts=2, base_delay=0.5)

    result = await _run_with_sink(handler, middleware, _Sink(boom=True))

    assert result == "ok"
    assert calls == ["deepseek-flash", "deepseek-flash"]
    assert any("事件写入失败" in line for line in recorder.warnings)
