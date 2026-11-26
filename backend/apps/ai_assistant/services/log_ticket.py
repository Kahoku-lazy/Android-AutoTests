from __future__ import annotations

import secrets
import time

TICKET_TTL_S = 60
_TICKETS: dict[str, tuple[str, str, float]] = {}


class LogTicketError(Exception):
    pass


def issue_log_ticket(thread_id: str, report_id: str) -> str:
    ticket = secrets.token_urlsafe(24)
    _TICKETS[ticket] = (thread_id, report_id, time.monotonic() + TICKET_TTL_S)
    return ticket


def consume_log_ticket(ticket: str, thread_id: str, report_id: str) -> None:
    row = _TICKETS.pop(ticket, None)
    if row is None:
        raise LogTicketError("凭证无效")
    bound_thread, bound_report, expires_at = row
    if time.monotonic() > expires_at or bound_thread != thread_id or bound_report != report_id:
        raise LogTicketError("凭证无效")
