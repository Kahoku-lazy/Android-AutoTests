from __future__ import annotations

import asyncio
import inspect
import os
import random

from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable

from agentscope.middleware import MiddlewareBase

__all__ = [
    "MAX_ATTEMPTS_LIMIT",
    "ModelRetryMiddleware",
    "RetrySettings",
    "is_transient_model_error",
]

MAX_ATTEMPTS_LIMIT = 8
MAX_BACKOFF_LIMIT = 60.0

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_FATAL_STATUS = frozenset({400, 401, 403, 404, 422})

_RETRY_NAME_HINTS = ("ratelimit", "timeout", "apiconnection", "serviceunavailable", "overloaded")
_FATAL_NAME_HINTS = (
    "authentication",
    "permissiondenied",
    "notfound",
    "badrequest",
    "validation",
    "invalid",
)


def _status_of(exc: BaseException) -> int:
    for attribute in ("status_code", "status", "http_status", "code"):
        value = getattr(exc, attribute, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else 0


def is_transient_model_error(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    if any(hint in name for hint in _FATAL_NAME_HINTS):
        return False
    status = _status_of(exc)
    if status in _FATAL_STATUS:
        return False
    if status in _RETRY_STATUS:
        return True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return any(hint in name for hint in _RETRY_NAME_HINTS)


@dataclass(frozen=True)
class RetrySettings:
    max_attempts: int = 3
    backoff_base: float = 0.8
    backoff_max: float = 8.0

    @classmethod
    def load(cls) -> "RetrySettings":
        attempts = _env_int("AE_MODEL_MAX_ATTEMPTS", cls.max_attempts, 1, MAX_ATTEMPTS_LIMIT)
        base = _env_float("AE_MODEL_BACKOFF_BASE", cls.backoff_base, 0.0, MAX_BACKOFF_LIMIT)
        cap = _env_float("AE_MODEL_BACKOFF_MAX", cls.backoff_max, 0.0, MAX_BACKOFF_LIMIT)
        return cls(max_attempts=attempts, backoff_base=base, backoff_max=max(cap, base))

    def delay_for(self, attempt: int) -> float:
        raw = min(self.backoff_base * (2 ** max(attempt - 1, 0)), self.backoff_max)
        jitter = raw * 0.2
        return max(raw + random.uniform(-jitter, jitter), 0.0)


def _env_int(name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def _env_float(name: str, default: float, low: float, high: float) -> float:
    try:
        value = float(os.environ.get(name, ""))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


class ModelRetryMiddleware(MiddlewareBase):
    def __init__(self, settings: RetrySettings | None = None) -> None:
        self.settings = settings or RetrySettings.load()

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        del agent
        attempt = 0
        while True:
            attempt += 1
            try:
                result = await next_handler(**input_kwargs)
            except Exception as exc:
                if attempt >= self.settings.max_attempts or not is_transient_model_error(exc):
                    raise
                await asyncio.sleep(self.settings.delay_for(attempt))
                continue
            if inspect.isasyncgen(result):
                return self._with_stream_retry(result, input_kwargs, next_handler, attempt)
            return result

    async def _with_stream_retry(
        self,
        stream: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
        attempt: int,
    ) -> AsyncGenerator[Any, None]:
        current = stream
        used = attempt
        while True:
            produced = False
            try:
                async for chunk in current:
                    produced = True
                    yield chunk
                return
            except Exception as exc:
                if produced or used >= self.settings.max_attempts:
                    raise
                if not is_transient_model_error(exc):
                    raise
            await asyncio.sleep(self.settings.delay_for(used))
            used += 1
            current = await next_handler(**input_kwargs)


if __name__ == "__main__":
    print(RetrySettings.load())  # noqa: T201 - 模块自测入口
