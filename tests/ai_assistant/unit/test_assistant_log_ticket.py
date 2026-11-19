"""一次性开门凭证：60 秒、只用一次、栏不匹配拒绝。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.services import log_ticket

pytestmark = [pytest.mark.unit]


def test_ticket_opens_once():
    ticket = log_ticket.issue_log_ticket("lane", "20261116_180000")
    log_ticket.consume_log_ticket(ticket, "lane", "20261116_180000")
    with pytest.raises(log_ticket.LogTicketError):
        log_ticket.consume_log_ticket(ticket, "lane", "20261116_180000")


def test_expired_ticket_is_rejected(monkeypatch):
    ticket = log_ticket.issue_log_ticket("lane", "20261116_180000")
    monkeypatch.setattr(
        log_ticket, "time", type("T", (), {"monotonic": staticmethod(lambda: 10**9)})()
    )
    with pytest.raises(log_ticket.LogTicketError):
        log_ticket.consume_log_ticket(ticket, "lane", "20261116_180000")


def test_wrong_lane_is_rejected():
    ticket = log_ticket.issue_log_ticket("lane", "20261116_180000")
    with pytest.raises(log_ticket.LogTicketError):
        log_ticket.consume_log_ticket(ticket, "other", "20261116_180000")
