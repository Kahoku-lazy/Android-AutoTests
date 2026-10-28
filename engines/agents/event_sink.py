"""
python -m 调试路径: engines.agents.event_sink

本模块的业务功能如下：
1. EventSink: 结构化事件的接收方协议。
2. bind_sink / current_sink: 绑定与取出当前接收方。默认实现丢弃记录，不写库。
3. flush_sink / emit_record: 让接收方写出事件；Django 已启动时改在工作线程里交记录。
4. RunContext / bind_run_context: 一次运行盖在每条事件上的上下文，引擎不写库。
5. set_case_title / set_step_context: 运行途中刷新当前用例名与当前步骤。
6. count_model_call / budget_exceeded: 运行预算（模型调用次数与时长）的计数与判定。
"""

from __future__ import annotations

import os
import time

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Protocol


class EventSink(Protocol):
    """接收一条结构化记录，以及可选的图片 base64。"""

    def emit(self, record, image_b64: str = "") -> None:
        """收下一条记录。默认实现什么都不做。

        Args:
            record: 结构化事件。
            image_b64: 拼好的图片 base64。没有图片时为空字符串。
        """


class _NullSink:
    """未绑定时的接收方：丢弃记录与图片。"""

    def emit(self, record, image_b64: str = "") -> None:
        """丢弃这条记录。

        Args:
            record: 结构化事件。
            image_b64: 拼好的图片 base64。
        """
        del record, image_b64


_NULL = _NullSink()
_current: ContextVar[EventSink] = ContextVar("agent_event_sink", default=_NULL)


def _env_int(name: str, default: int) -> int:
    """读一个整数环境变量。缺省或非法时回落到默认值。

    Args:
        name: 环境变量名。
        default: 读不到或不合法时使用的值。

    Returns:
        解析出的整数。
    """
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


# 运行预算：超过任一项即停止整轮任务。0 表示不限制。
MAX_MODEL_CALLS = _env_int("SOP_MAX_MODEL_CALLS", 600)
MAX_RUN_SECONDS = _env_int("SOP_MAX_RUN_SECONDS", 7200)


def bind_sink(sink: EventSink) -> Token[EventSink]:
    """把当前上下文的接收方换成给定实现。

    Args:
        sink: 这次任务使用的接收方。

    Returns:
        还原用的令牌，交给 reset_sink。
    """
    return _current.set(sink)


def reset_sink(token: Token[EventSink]) -> None:
    """还原 bind_sink 之前的接收方。

    Args:
        token: bind_sink 返回的令牌。
    """
    _current.reset(token)


def current_sink() -> EventSink:
    """取出当前接收方。未绑定时为丢弃实现。

    Returns:
        当前接收方。
    """
    return _current.get()


def flush_sink() -> None:
    """把当前接收方缓冲的事件立即写出；接收方没有 flush 时什么都不做。"""
    flush = getattr(current_sink(), "flush", None)
    if callable(flush):
        flush()


def _django_ready() -> bool:
    """当前进程是否已完成 Django 启动。

    Returns:
        已启动返回 True；未安装或未启动返回 False。
    """
    try:
        from django.apps import apps
    except ImportError:
        return False
    return bool(apps.ready)


def _deliver(record, image_b64: str, flush: bool) -> None:
    """把一条记录交给当前接收方。

    Args:
        record: 结构化事件。
        image_b64: 事件附带的图片 base64，没有时为空串。
        flush: 交完后是否立即让接收方落库。
    """
    current_sink().emit(record, image_b64)
    if flush:
        flush_sink()


async def emit_record(record, image_b64: str = "", *, flush: bool = False) -> None:
    """把一条记录交给当前接收方；Django 已启动时放进工作线程，避免异步上下文里查库。

    Args:
        record: 结构化事件。
        image_b64: 事件附带的图片 base64，没有时为空串。
        flush: 交完后是否立即让接收方落库。

    Raises:
        Exception: 原样抛出接收方的失败，由调用方决定是否吞掉。
    """
    if _django_ready():
        from channels.db import database_sync_to_async

        await database_sync_to_async(_deliver, thread_sensitive=False)(record, image_b64, flush)
        return
    _deliver(record, image_b64, flush)


@dataclass
class RunContext:
    """一次任务运行盖在每条事件上的上下文。引擎不写库。"""

    task_id: int = 0
    agent_id: int = 0
    case_title: str = ""
    step_seq: int | None = None
    attempt: int | None = None
    model_calls: int = 0
    """本次任务已发生的模型调用次数，由 count_model_call 累加。"""
    started: float = 0.0
    """本次任务起点，monotonic 秒。0 表示未计时。"""
    budget_exceeded: bool = False
    """已超预算。调用方据此终止整轮任务。"""


_run: ContextVar[RunContext | None] = ContextVar("agent_run_context", default=None)


def bind_run_context(task_id: int, agent_id: int, case_title: str = "") -> Token:
    """绑定这次运行的任务号与智能体号。

    Args:
        task_id: 平台任务 id。0 表示不落库。
        agent_id: 智能体 id。未知时为 0。
        case_title: 用例标题。

    Returns:
        还原用的令牌，交给 reset_run_context。
    """
    return _run.set(
        RunContext(
            task_id=task_id,
            agent_id=agent_id,
            case_title=case_title,
            started=time.monotonic(),
        )
    )


def reset_run_context(token: Token) -> None:
    """还原 bind_run_context 之前的上下文。

    Args:
        token: bind_run_context 返回的令牌。
    """
    _run.reset(token)


def current_run() -> RunContext:
    """取出当前运行上下文。未绑定时任务号为 0。

    Returns:
        当前上下文。
    """
    return _run.get() or RunContext()


def set_case_title(case_title: str) -> None:
    """更新当前正在跑的用例名。未绑定运行上下文时不做任何事。

    一个任务可以按序跑多条用例，每条用例开始时刷新一次，事件行才分得清归属。

    Args:
        case_title: 正在执行的用例标题。
    """
    ctx = _run.get()
    if ctx is None:
        return
    ctx.case_title = str(case_title or "")[:255]


def set_step_context(step_seq: int | None, attempt: int | None) -> None:
    """更新当前步骤序号和第几次尝试。未绑定运行上下文时不做任何事。

    Args:
        step_seq: 从 1 起的步骤序号。没有当前步时为 None。
        attempt: 该步第几次尝试。
    """
    ctx = _run.get()
    if ctx is None:
        return
    ctx.step_seq = step_seq
    ctx.attempt = attempt


def count_model_call() -> None:
    """给本次任务记一次模型调用。超过次数或时长上限时置位预算标志。

    不改任务状态、不抛异常：调用方读 budget_exceeded 自己决定怎么收场。
    """
    ctx = _run.get()
    if ctx is None:
        return
    ctx.model_calls += 1
    elapsed = time.monotonic() - ctx.started if ctx.started > 0 else 0.0
    over_calls = MAX_MODEL_CALLS > 0 and ctx.model_calls > MAX_MODEL_CALLS
    over_time = MAX_RUN_SECONDS > 0 and elapsed > MAX_RUN_SECONDS
    if over_calls or over_time:
        ctx.budget_exceeded = True


def budget_exceeded() -> bool:
    """本次任务是否已超预算。未绑定运行上下文时为 False。

    Returns:
        已超次数或时长上限返回 True。
    """
    ctx = _run.get()
    return bool(ctx is not None and ctx.budget_exceeded)
