"""
python -m 调试路径: engines.agents.middleware.model_retry

本模块的业务功能如下：
1. is_transient_model_error: 判定一次模型调用失败是否值得重试。
2. RetrySettings / load_retry_settings: 从环境变量读出重试与回退参数。
3. ModelRetryMiddleware: 模型调用失败时按退避重试，用尽后切备用模型再试。
4. build_model_retry_middleware: 按设置装配中间件，未启用时返回 None。
"""

from __future__ import annotations

import asyncio
import inspect
import os

from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from agentscope.middleware import MiddlewareBase
from agentscope.model import ChatModelBase

from utils.logs import agent_event_log

from ..event_sink import emit_record
from ..messaging.record import EventRecord

# 值得重试的 HTTP 状态：限流、超时、服务端临时故障。
_RETRYABLE_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
# 异常类名里出现这些片段即视为瞬态（覆盖各 SDK 的超时与连接类异常）。
_TRANSIENT_NAME_MARKERS = (
    "timeout",
    "timedout",
    "ratelimit",
    "overloaded",
    "serviceunavailable",
    "internalservererror",
    "apiconnection",
    "apitimeout",
    "remoteprotocol",
    "connecterror",
    "connectionerror",
    "readerror",
)
# 异常文案里出现这些片段即视为瞬态（没有状态码也没有专用异常类时兜底）。
_TRANSIENT_MESSAGE_MARKERS = (
    "timed out",
    "timeout",
    "connection reset",
    "connection aborted",
    "connection error",
    "temporarily unavailable",
    "rate limit",
    "too many requests",
    "overloaded",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
)
# 明确属于「请求本身有问题」的异常：不重试、不回退。
_NON_RETRYABLE_TYPES = (
    ValueError,
    TypeError,
    KeyError,
    IndexError,
    AttributeError,
    NotImplementedError,
    AssertionError,
)

_ATTEMPTS_ENV = "AGENT_MODEL_RETRY_ATTEMPTS"
_BASE_DELAY_ENV = "AGENT_MODEL_RETRY_BASE_DELAY_MS"
_MAX_DELAY_ENV = "AGENT_MODEL_RETRY_MAX_DELAY_MS"
_FALLBACK_MODEL_ENV = "AGENT_FALLBACK_MODEL"
_FALLBACK_PROVIDER_ENV = "AGENT_FALLBACK_PROVIDER"
_FALLBACK_BASE_URL_ENV = "AGENT_FALLBACK_BASE_URL"
_FALLBACK_API_KEY_ENV = "AGENT_FALLBACK_API_KEY"

DEFAULT_ATTEMPTS = 2
"""同一个模型默认最多调用几次（含第一次）；模型层已 provider 感知重试，这里只补一层。"""

DEFAULT_BASE_DELAY_MS = 800
"""首次重试前的等待毫秒数。"""

DEFAULT_MAX_DELAY_MS = 8000
"""单次等待的毫秒上限。"""

RETRY_EVENT = "ModelRetryEvent"
"""一次重试写进任务事件流的类型名。"""

FALLBACK_EVENT = "ModelFallbackEvent"
"""一次回退写进任务事件流的类型名。"""

EVENT_PHASE = "推理"
"""两类事件都落在推理阶段，与模型调用同一条时间线。"""

EVENT_BLOCK_TYPE = "retry"
"""事件卡片类型：重试/回退共用一种。"""


def _status_of(exc: BaseException) -> int | None:
    """取出异常携带的 HTTP 状态码。

    Args:
        exc: 模型调用抛出的异常。

    Returns:
        找到的状态码；没有则返回 None。
    """
    for attr in ("status_code", "status", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    code = getattr(response, "status_code", None)
    return code if isinstance(code, int) else None


def is_transient_model_error(exc: BaseException) -> bool:
    """判定一次模型调用失败是否属于「重试可能成功」的瞬态故障。

    Args:
        exc: 模型调用抛出的异常。

    Returns:
        瞬态返回 True；请求本身有问题（鉴权、参数、代码缺陷）返回 False。
    """
    status = _status_of(exc)
    if status is not None:
        if status in _RETRYABLE_STATUS:
            return True
        if 400 <= status < 500:
            return False
        if status >= 500:
            return True
    name = type(exc).__name__.lower()
    if any(marker in name for marker in _TRANSIENT_NAME_MARKERS):
        return True
    if isinstance(exc, _NON_RETRYABLE_TYPES):
        return False
    message = str(exc).lower()
    return any(marker in message for marker in _TRANSIENT_MESSAGE_MARKERS)


def _env_int(name: str, default: int) -> int:
    """读一个整数环境变量，缺省或非法时回落默认值。

    Args:
        name: 环境变量名。
        default: 读不到或非法时使用的值。

    Returns:
        解析出的整数。
    """
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    """读一个浮点环境变量，缺省或非法时回落默认值。

    Args:
        name: 环境变量名。
        default: 读不到或非法时使用的值。

    Returns:
        解析出的浮点数。
    """
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class RetrySettings:
    """
    重试与回退的运行参数，全部来自环境变量。

    Attributes:
        attempts: 同一个模型最多调用几次（含第一次）；1 表示不重试。
        base_delay: 首次重试前的等待秒数。
        max_delay: 单次等待的秒数上限。
        fallback_model_name: 备用模型名；空串表示不启用回退。
        fallback_provider: 备用模型 provider；空串表示沿用主模型。
        fallback_base_url: 备用模型 base_url；空串表示沿用主模型。
        fallback_api_key: 备用模型密钥；空串表示沿用主模型。

    Raises:
        FrozenInstanceError: 参数不可变。
    """

    attempts: int = DEFAULT_ATTEMPTS
    base_delay: float = DEFAULT_BASE_DELAY_MS / 1000
    max_delay: float = DEFAULT_MAX_DELAY_MS / 1000
    fallback_model_name: str = ""
    fallback_provider: str = ""
    fallback_base_url: str = ""
    fallback_api_key: str = field(default="", repr=False)

    @property
    def enabled(self) -> bool:
        """是否需要装配中间件：会重试或配置了备用模型。

        Returns:
            会重试或配了备用模型时返回 True。
        """
        return self.attempts > 1 or bool(self.fallback_model_name)


def load_retry_settings() -> RetrySettings:
    """从环境变量装配重试与回退参数，非法值回落默认。

    Returns:
        本次运行的参数；默认允许同模型重试一次、不启用备用模型。
    """
    attempts = max(1, _env_int(_ATTEMPTS_ENV, DEFAULT_ATTEMPTS))
    base_delay = max(0.0, _env_float(_BASE_DELAY_ENV, DEFAULT_BASE_DELAY_MS) / 1000)
    max_delay = max(base_delay, _env_float(_MAX_DELAY_ENV, DEFAULT_MAX_DELAY_MS) / 1000)
    return RetrySettings(
        attempts=attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        fallback_model_name=os.environ.get(_FALLBACK_MODEL_ENV, "").strip(),
        fallback_provider=os.environ.get(_FALLBACK_PROVIDER_ENV, "").strip(),
        fallback_base_url=os.environ.get(_FALLBACK_BASE_URL_ENV, "").strip(),
        fallback_api_key=os.environ.get(_FALLBACK_API_KEY_ENV, "").strip(),
    )


async def _replay(
    first: Any,
    rest: AsyncGenerator[Any, None],
) -> AsyncGenerator[Any, None]:
    """先吐出已探到的首块，再转发剩余块；退出时关闭底层流。

    Args:
        first: 已经取到的第一个数据块。
        rest: 剩下的底层流。

    Yields:
        首块与后续每一块，顺序与内容不变。
    """
    try:
        yield first
        async for chunk in rest:
            yield chunk
    finally:
        await rest.aclose()


class ModelRetryMiddleware(MiddlewareBase):
    """
    模型调用韧性的中间件：退避重试 + 备用模型回退 + 警告日志。

    只包住 `on_model_call`。重试计数与当前模型都用局部变量，不写
    `agent.state`，因此同一实例可被多个 Agent 共用。

    Attributes:
        fallback_model: 主模型用尽后改用的模型；None 表示不回退。

    Raises:
        ValueError: `attempts` 小于 1，或退避参数为负。
    """

    def __init__(
        self,
        *,
        attempts: int = DEFAULT_ATTEMPTS,
        base_delay: float = DEFAULT_BASE_DELAY_MS / 1000,
        max_delay: float = DEFAULT_MAX_DELAY_MS / 1000,
        fallback_model: ChatModelBase | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        log: Any = agent_event_log,
    ) -> None:
        """
        创建重试与回退中间件。

        Args:
            attempts: 同一个模型最多调用几次（含第一次）；1 表示不重试。
            base_delay: 首次重试前的等待秒数。
            max_delay: 单次等待的秒数上限。
            fallback_model: 备用模型；None 表示不回退。
            sleep: 等待实现，测试可注入。
            log: 日志记录器，默认 `agent_event_log`。

        Raises:
            ValueError: `attempts` 小于 1，或退避参数为负、上限小于基准。
        """
        if attempts < 1:
            raise ValueError(f"重试次数必须至少为 1：{attempts}")
        if base_delay < 0 or max_delay < 0:
            raise ValueError(f"退避时长不能为负：{base_delay} / {max_delay}")
        if max_delay < base_delay:
            raise ValueError(f"退避上限不能小于基准：{base_delay} / {max_delay}")

        self.attempts = int(attempts)
        self.base_delay = float(base_delay)
        self.max_delay = float(max_delay)
        self.fallback_model = fallback_model
        self._sleep = sleep
        self._log = log

    def _model_chain(self, input_kwargs: dict) -> list[ChatModelBase]:
        """本次调用依次尝试的模型：主模型在前，备用模型在后。

        Args:
            input_kwargs: `on_model_call` 的入参。

        Returns:
            非空的模型列表。
        """
        primary = input_kwargs.get("current_model")
        chain = [primary] if self.fallback_model is None else [primary, self.fallback_model]
        return [model for model in chain if model is not None]

    def _delay(self, attempt: int) -> float:
        """第 `attempt` 次重试前的等待秒数：基准翻倍、上限封顶。

        Args:
            attempt: 已经失败了几次（从 1 起）。

        Returns:
            本次等待的秒数。
        """
        return min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))

    @staticmethod
    def _model_name(model: Any) -> str:
        """取模型名，取不到时用占位符。

        Args:
            model: 模型实例。

        Returns:
            用于日志的模型名。
        """
        return str(getattr(model, "model", "") or "-")

    def _warn(self, message: str) -> None:
        """写一条警告日志；记录器不支持 warning 时静默跳过。

        Args:
            message: 日志正文。
        """
        warning = getattr(self._log, "warning", None)
        if callable(warning):
            warning(message)

    async def _emit(self, event_type: str, agent: Any, *, model: str, payload: dict) -> None:
        """把一次重试或回退写成一条结构化事件，交给当前任务接收方。

        未绑定接收方时由丢弃实现吸收；接收方失败只记警告，不影响重试节奏。

        Args:
            event_type: `RETRY_EVENT` 或 `FALLBACK_EVENT`。
            agent: 发起调用的智能体，只取名字。
            model: 本次使用的模型名。
            payload: 事件载荷，必须是可 JSON 化的字典。
        """
        record = EventRecord(
            event_type=event_type,
            phase=EVENT_PHASE,
            block_type=EVENT_BLOCK_TYPE,
            role_name=str(getattr(agent, "name", "") or ""),
            model=model,
            payload=payload,
        )
        try:
            await emit_record(record, flush=True)
        except Exception as exc:  # noqa: BLE001 - 写事件失败不能打断重试
            self._warn(f"重试事件写入失败（{type(exc).__name__}: {exc}），继续重试")

    async def _call_once(
        self,
        next_handler: Callable[..., Awaitable[Any]],
        input_kwargs: dict,
        model: ChatModelBase,
    ) -> Any:
        """按指定模型调用一次；流式响应先探首块，失败在此抛出。

        Args:
            next_handler: 调用链里的下一层。
            input_kwargs: `on_model_call` 的入参。
            model: 本次使用的模型。

        Returns:
            模型响应；流式为已缓存首块的异步生成器。
        """
        kwargs = {**input_kwargs, "current_model": model}
        response = await next_handler(**kwargs)
        if not inspect.isasyncgen(response):
            return response
        try:
            first = await anext(response)
        except StopAsyncIteration:
            await response.aclose()
            raise RuntimeError("模型流式响应为空") from None
        except BaseException:
            await response.aclose()
            raise
        return _replay(first, response)

    async def on_model_call(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., Awaitable[Any]],
    ) -> Any:
        """
        拦截一次底层模型调用，按需重试或回退。

        Args:
            agent: 发起调用的智能体。
            input_kwargs: 含 `current_model` / `messages` / `tools` / `tool_choice`。
            next_handler: 调用链里的下一层。

        Returns:
            模型响应，或包好首块的流式生成器。

        Raises:
            Exception: 原样抛出最后一次失败；非瞬态错误在第一次失败时立即抛出。
        """
        models = self._model_chain(input_kwargs)
        last_error: BaseException | None = None
        for index, model in enumerate(models):
            for attempt in range(1, self.attempts + 1):
                try:
                    return await self._call_once(next_handler, input_kwargs, model)
                except Exception as exc:
                    if not is_transient_model_error(exc):
                        raise
                    last_error = exc
                    if attempt < self.attempts:
                        delay = self._delay(attempt)
                        self._warn(
                            f"模型调用失败，第 {attempt}/{self.attempts} 次："
                            f"{self._model_name(model)} · {type(exc).__name__}: {exc}"
                            f"；{delay:.1f}s 后重试"
                        )
                        await self._emit(
                            RETRY_EVENT,
                            agent,
                            model=self._model_name(model),
                            payload={
                                "attempt": attempt,
                                "attempts": self.attempts,
                                "delay_ms": int(delay * 1000),
                                "reason": f"{type(exc).__name__}: {exc}"[:400],
                            },
                        )
                        await self._sleep(delay)
            if index + 1 < len(models):
                self._warn(
                    f"模型 {self._model_name(model)} 已用尽 {self.attempts} 次尝试，"
                    f"回退到备用模型 {self._model_name(self.fallback_model)}"
                )
                await self._emit(
                    FALLBACK_EVENT,
                    agent,
                    model=self._model_name(model),
                    payload={
                        "from_model": self._model_name(model),
                        "to_model": self._model_name(self.fallback_model),
                        "attempts": self.attempts,
                    },
                )
        if last_error is None:
            raise RuntimeError("模型调用未执行：没有可用模型")
        raise last_error


def build_model_retry_middleware(
    settings: RetrySettings | None = None,
    *,
    fallback_model: ChatModelBase | None = None,
) -> ModelRetryMiddleware | None:
    """按设置装配中间件；未启用时返回 None，调用方据此跳过装配。

    Args:
        settings: 重试与回退参数；None 表示现读环境变量。
        fallback_model: 已构造好的备用模型；None 表示不回退。

    Returns:
        `ModelRetryMiddleware` 实例；既不重试也无备用模型时为 None。

    Raises:
        ValueError: 参数非法（次数小于 1 或退避为负）。
    """
    resolved = settings if settings is not None else load_retry_settings()
    if not resolved.enabled:
        return None
    return ModelRetryMiddleware(
        attempts=resolved.attempts,
        base_delay=resolved.base_delay,
        max_delay=resolved.max_delay,
        fallback_model=fallback_model,
    )
