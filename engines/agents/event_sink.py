"""
python -m 调试路径: engines.agents.event_sink

本模块的业务功能如下：
1. EventSink: 结构化事件的接收方协议。
2. bind_sink / current_sink: 绑定与取出当前接收方。默认实现丢弃记录，不写库。
"""

from __future__ import annotations

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


@dataclass
class RunContext:
    """一次任务运行盖在每条事件上的上下文。引擎不写库。"""

    task_id: int = 0
    agent_id: int = 0
    case_title: str = ""
    step_seq: int | None = None
    attempt: int | None = None


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
    return _run.set(RunContext(task_id=task_id, agent_id=agent_id, case_title=case_title))


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
