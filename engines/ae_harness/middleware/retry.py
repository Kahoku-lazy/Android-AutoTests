"""
文件名: ➡️ retry.py 🏁
路径: ➡️ engines/ae_harness/middleware/retry.py 🏁
模块功能：➡️ 模型调用重试：错误分类、指数退避、流式不重放 🏁
Python 调试：➡️ python -m engines.ae_harness.middleware.retry 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. is_transient_model_error: 判断一次模型调用失败是否值得重试（黑名单优先）。
2. RetrySettings: 从环境变量读重试次数与退避参数，带硬上限。
3. ModelRetryMiddleware: 在 on_model_call 上重试同一动作；流式只在首块之前重试。
🏁
关联模块：➡️
1. 无本地依赖：只依赖标准库与框架的中间件基类。
🏁
测试：➡️
1. 暂无
🏁
"""

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

# 硬上限：避免有人把重试次数或退避调到失控。
MAX_ATTEMPTS_LIMIT = 8
MAX_BACKOFF_LIMIT = 60.0

# 值得重试的 HTTP 状态：限流、超时、服务端临时故障。
_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
# 明确属于「请求本身有问题」的状态：即使命中上面的集合也不重试。
_FATAL_STATUS = frozenset({400, 401, 403, 404, 422})

# 异常类型名里出现这些词，判定为可重试。
_RETRY_NAME_HINTS = ("ratelimit", "timeout", "apiconnection", "serviceunavailable", "overloaded")
# 异常类型名里出现这些词，判定为不可重试（优先于可重试）。
_FATAL_NAME_HINTS = (
    "authentication",
    "permissiondenied",
    "notfound",
    "badrequest",
    "validation",
    "invalid",
)


def _status_of(exc: BaseException) -> int:
    """
    从异常里尽力取出 HTTP 状态码。

    Args:
        exc: 异常对象。

    Returns:
        状态码；取不到时返回 0。
    """
    for attribute in ("status_code", "status", "http_status", "code"):
        value = getattr(exc, attribute, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else 0


def is_transient_model_error(exc: BaseException) -> bool:
    """
    判断一次模型调用失败是否值得重试。

    黑名单优先：参数非法、鉴权失败这类错误重试多少次都不会成功。

    Args:
        exc: 调用抛出的异常。

    Returns:
        值得重试返回 True。
    """
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
    """
    重试参数。

    Attributes:
        max_attempts: 最多调用几次（含第一次）。
        backoff_base: 第一次退避的秒数。
        backoff_max: 单次退避的上限秒数。
    """

    max_attempts: int = 3
    backoff_base: float = 0.8
    backoff_max: float = 8.0

    @classmethod
    def load(cls) -> "RetrySettings":
        """
        从环境变量读取参数，非法值回退默认，超限截断。

        Returns:
            解析后的参数。
        """
        attempts = _env_int("AE_MODEL_MAX_ATTEMPTS", cls.max_attempts, 1, MAX_ATTEMPTS_LIMIT)
        base = _env_float("AE_MODEL_BACKOFF_BASE", cls.backoff_base, 0.0, MAX_BACKOFF_LIMIT)
        cap = _env_float("AE_MODEL_BACKOFF_MAX", cls.backoff_max, 0.0, MAX_BACKOFF_LIMIT)
        return cls(max_attempts=attempts, backoff_base=base, backoff_max=max(cap, base))

    def delay_for(self, attempt: int) -> float:
        """
        算第 n 次失败后该等多久。

        Args:
            attempt: 已失败次数，从 1 开始。

        Returns:
            带 ±20% 抖动的退避秒数。
        """
        raw = min(self.backoff_base * (2 ** max(attempt - 1, 0)), self.backoff_max)
        jitter = raw * 0.2
        return max(raw + random.uniform(-jitter, jitter), 0.0)


def _env_int(name: str, default: int, low: int, high: int) -> int:
    """
    读一个带范围的整型环境变量。

    Args:
        name: 变量名。
        default: 缺省值。
        low: 下限。
        high: 上限。

    Returns:
        夹在范围内取值。
    """
    try:
        value = int(os.environ.get(name, ""))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def _env_float(name: str, default: float, low: float, high: float) -> float:
    """
    读一个带范围的浮点环境变量。

    Args:
        name: 变量名。
        default: 缺省值。
        low: 下限。
        high: 上限。

    Returns:
        夹在范围内取值。
    """
    try:
        value = float(os.environ.get(name, ""))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


class ModelRetryMiddleware(MiddlewareBase):
    """
    模型调用失败时重试同一动作。

    只补一层重试：模型层已有 provider 感知的重试，这里处理跨调用的抖动与流式边界。
    """

    def __init__(self, settings: RetrySettings | None = None) -> None:
        """
        记录重试参数。

        Args:
            settings: 重试参数；不传则从环境变量读。
        """
        self.settings = settings or RetrySettings.load()

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        """
        包住一次模型调用：调用本身失败可重试，流式只在首块之前重试。

        不靠函数类型判断流式：先拿到返回值，再看它是不是异步生成器，
        因为下一层可能是普通协程返回生成器。

        Args:
            agent: 当前智能体。
            input_kwargs: 交给下一层的参数。
            next_handler: 下一层调用。

        Returns:
            模型响应或异步生成器。

        Raises:
            Exception: 不可重试或重试用尽时上抛原异常。
        """
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
        """
        流式包装：已经产出过片段后失败不再重试。

        Args:
            stream: 当前这一轮的异步生成器。
            input_kwargs: 参数，重试时重新交给下一层。
            next_handler: 下一层调用。
            attempt: 已经用掉的调用次数。

        Yields:
            响应片段。

        Raises:
            Exception: 已产出后失败、不可重试或次数用尽时上抛。
        """
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
            # 重发放在 except 之外：重发本身再失败时回到循环顶部，继续按同一规则重试。
            await asyncio.sleep(self.settings.delay_for(used))
            used += 1
            current = await next_handler(**input_kwargs)


if __name__ == "__main__":
    print(RetrySettings.load())  # noqa: T201 - 模块自测入口
