"""仪表盘当日逐小时用量：按时间进度出数、整点边界、进行中小时、空数据。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIAgent, AIUsageHourly
from apps.dashboard.ai_usage import (
    ai_daily_series,
    ai_task_daily_execution,
    ai_today_usage_slots,
)

DAY = datetime(2026, 10, 21, 11, 5, 0)


@pytest.fixture
def visible_agent(db):
    user = get_user_model().objects.create_user(
        username="dash-today-usage",
        password="x",
        is_superuser=True,
    )
    agent = AIAgent.objects.create(name="today-usage-agent", owner=user)
    return user, agent


def _usage(agent, hour, inp, out, cost):
    AIUsageHourly.objects.create(
        stat_date=DAY.date(),
        stat_hour=hour,
        agent_id=agent.id,
        model="deepseek-chat",
        role_name="执行者",
        input_tokens=inp,
        output_tokens=out,
        cost_total=Decimal(str(cost)),
    )


@pytest.mark.unit
@pytest.mark.django_db
def test_today_usage_is_hourly_and_does_not_leak_future_hours(visible_agent):
    user, agent = visible_agent
    _usage(agent, 1, 100, 20, "0.001")
    _usage(agent, 3, 50, 0, "0.0005")
    _usage(agent, 5, 30, 10, "0.0002")
    _usage(agent, 9, 30, 0, "0.0003")

    slots = ai_today_usage_slots(str(user.id), now=DAY)

    assert len(slots["tokens"]) == 24
    assert slots["tokens"][1] == 120
    assert slots["tokens"][3] == 50
    assert slots["tokens"][5] == 40
    assert slots["tokens"][9] == 30
    assert slots["tokens"][10] == 0
    # 11 点这一小时进行中，12 点及以后还没开始
    assert slots["tokens"][11] is None
    assert all(value is None for value in slots["tokens"][12:])
    assert slots["cost"][1] == pytest.approx(0.001)
    assert slots["cost"][3] == pytest.approx(0.0005)
    assert slots["current"]["hour"] == pytest.approx(11.08)
    assert slots["current"]["tokens"] == 0


@pytest.mark.unit
@pytest.mark.django_db
def test_today_usage_completed_hour_moves_to_curve(visible_agent):
    user, agent = visible_agent
    _usage(agent, 11, 40, 0, "0.0004")

    slots = ai_today_usage_slots(str(user.id), now=datetime(2026, 10, 21, 12, 30, 0))

    assert slots["tokens"][11] == 40
    assert slots["current"]["hour"] == pytest.approx(12.5)
    assert slots["current"]["tokens"] == 0


@pytest.mark.unit
@pytest.mark.django_db
def test_today_usage_on_hour_boundary_has_no_current(visible_agent):
    user, agent = visible_agent
    _usage(agent, 11, 40, 0, "0.0004")

    slots = ai_today_usage_slots(str(user.id), now=datetime(2026, 10, 21, 12, 0, 0))

    assert slots["current"] is None
    assert slots["tokens"][11] == 40


@pytest.mark.unit
@pytest.mark.django_db
def test_today_usage_empty_day(visible_agent):
    user, _agent = visible_agent

    slots = ai_today_usage_slots(str(user.id), now=DAY)

    # 已走完的小时为 0，未走完/未开始为 None
    assert slots["tokens"][:11] == [0] * 11
    assert slots["tokens"][11:] == [None] * 13
    assert slots["cost"][:11] == [0] * 11
    assert slots["current"]["tokens"] == 0
    assert slots["current"]["cost"] == 0


@pytest.mark.unit
@pytest.mark.django_db
def test_daily_series_default_to_one_week(visible_agent):
    user, _agent = visible_agent

    assert len(ai_daily_series(str(user.id))["labels"]) == 7
    assert len(ai_task_daily_execution(str(user.id))["labels"]) == 7
