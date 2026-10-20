"""仪表盘把一个智能体的小时用量合成一份。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIAgent, AIUsageHourly
from apps.dashboard.ai_usage import ai_usage_stats

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_agent_usage_sums_roles_into_one_total():
    owner = get_user_model().objects.create_user(username="usage-owner", password="pass")
    agent = AIAgent.objects.create(
        name="助手",
        owner=owner,
        route_configs={"device_control": {"name": "Agent-01"}},
    )
    shared = {
        "stat_date": date(2026, 10, 20),
        "stat_hour": 16,
        "agent_id": agent.id,
        "model": "deepseek-flash",
    }
    AIUsageHourly.objects.create(
        **shared,
        role_name="executor_role",
        role_kind="executor",
        input_tokens=1000,
        cache_input_tokens=400,
        output_tokens=50,
        cost_total=Decimal("0.01000000"),
    )
    AIUsageHourly.objects.create(
        **shared,
        role_name="verifier_role",
        role_kind="verifier",
        input_tokens=200,
        cache_input_tokens=100,
        output_tokens=20,
        cost_total=Decimal("0.00200000"),
    )

    stats = ai_usage_stats(str(owner.id))
    row = next(item for item in stats["agents"] if item["id"] == agent.id)
    assert row["name"] == "Agent-01"
    assert row["input_tokens"] == 1200
    assert row["cache_hit_tokens"] == 500
    assert row["output_tokens"] == 70
    assert row["cost_total"] == "0.01200000"
    assert stats["input_tokens"]["total"] == 1200
    assert stats["cache_hit_tokens"]["total"] == 500
    assert stats["output_tokens"]["total"] == 70
    assert stats["deepseek_cost"]["total"] == 0.012
