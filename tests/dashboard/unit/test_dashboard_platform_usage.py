"""仪表盘用量与费用按全平台合计：不可见智能体与 agent_id=0 的用量也要计入。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model

from backend.apps.dashboard.ai_usage import (
    ai_daily_series,
    ai_today_usage_slots,
    ai_usage_stats,
)
from backend.apps.usage_ledger.models import ModelUsage

DAY = datetime(2026, 10, 21, 11, 5, 0)


@pytest.fixture
def platform_users(db):
    """查看者。账本不按智能体过滤，造数只用编号区分来源。"""
    user_model = get_user_model()
    viewer = user_model.objects.create_user(username="dash-platform-a", password="x")
    return viewer, type("Agent", (), {"id": 1})(), type("Agent", (), {"id": 2})()


def _usage(agent_id: int, hour: int, input_tokens: int, output_tokens: int, cost: str) -> None:
    ModelUsage.objects.create(
        event_id=f"dash:{agent_id}:{hour}:{input_tokens}",
        occurred_at=DAY.replace(hour=hour),
        provider="deepseek",
        category="LLM",
        model="deepseek-flash",
        source="task",
        execution_id=str(agent_id),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_total=Decimal(cost),
        pricing_status="priced",
    )


@pytest.mark.unit
@pytest.mark.django_db
def test_usage_totals_include_hidden_agents_and_unowned_rows(platform_users):
    viewer, visible, hidden = platform_users
    _usage(visible.id, 9, 100, 10, "0.001")
    _usage(hidden.id, 10, 200, 20, "0.002")
    _usage(0, 10, 300, 30, "0.003")

    with patch("backend.apps.dashboard.ai_usage.timezone.now", return_value=DAY):
        stats = ai_usage_stats(str(viewer.id))

    assert stats["total_tokens"]["today"] == 660
    assert stats["deepseek_cost"]["today"] == pytest.approx(0.006)
    assert stats["agents"] == []


@pytest.mark.unit
@pytest.mark.django_db
def test_today_slots_sum_platform_usage(platform_users):
    viewer, visible, hidden = platform_users
    _usage(visible.id, 9, 100, 10, "0.001")
    _usage(hidden.id, 10, 200, 20, "0.002")
    _usage(0, 10, 300, 30, "0.003")

    slots = ai_today_usage_slots(str(viewer.id), now=DAY)

    assert slots["tokens"][9] == 110
    assert slots["tokens"][10] == 550
    assert slots["tokens"][11] is None
    assert slots["current"]["tokens"] == 0
    assert slots["cost"][10] == pytest.approx(0.005)


@pytest.mark.unit
@pytest.mark.django_db
def test_daily_series_sums_platform_usage(platform_users):
    viewer, visible, hidden = platform_users
    _usage(visible.id, 9, 100, 10, "0.001")
    _usage(hidden.id, 10, 200, 20, "0.002")
    _usage(0, 10, 300, 30, "0.003")

    with patch("backend.apps.dashboard.ai_usage.timezone.now", return_value=DAY):
        series = ai_daily_series(str(viewer.id), days=2)

    assert series["total_tokens"] == [0, 660]
    assert series["deepseek_cost"] == [0.0, pytest.approx(0.006)]
