"""助手报告的一次性开门凭证。只记栏编号与报告编号，不记磁盘路径。"""

from __future__ import annotations

import secrets
import time

TICKET_TTL_S = 60
_TICKETS: dict[str, tuple[str, str, float]] = {}


class LogTicketError(Exception):
    """凭证无效、过期或已使用。"""


def issue_log_ticket(thread_id: str, report_id: str) -> str:
    """签发一张 60 秒内可打开一次的凭证。

    Args:
        thread_id: 对话栏编号。
        report_id: 时间戳目录名。

    Returns:
        随机 ticket。不含路径。
    """
    ticket = secrets.token_urlsafe(24)
    _TICKETS[ticket] = (thread_id, report_id, time.monotonic() + TICKET_TTL_S)
    return ticket


def consume_log_ticket(ticket: str, thread_id: str, report_id: str) -> None:
    """校验并作废凭证。

    Raises:
        LogTicketError: 不存在、过期、已使用，或栏/报告不匹配。
    """
    row = _TICKETS.pop(ticket, None)
    if row is None:
        raise LogTicketError("凭证无效")
    bound_thread, bound_report, expires_at = row
    if time.monotonic() > expires_at or bound_thread != thread_id or bound_report != report_id:
        raise LogTicketError("凭证无效")
