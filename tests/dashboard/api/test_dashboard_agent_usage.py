"""仪表盘把一个智能体的小时用量合成一份。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from backend.apps.dashboard.ai_usage import ai_usage_stats
from backend.apps.usage_ledger.models import ModelUsage

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_agent_usage_sums_roles_into_one_total():
    agent = type("Agent", (), {"id": 1})()
    ModelUsage.objects.create(
        event_id="agent-usage:1",
        occurred_at=datetime(2026, 10, 20, 16, 0, 0),
        provider="deepseek",
        category="LLM",
        model="deepseek-flash",
        source="task",
        execution_id=str(agent.id),
        input_tokens=1000,
        cache_input_tokens=400,
        output_tokens=50,
        total_tokens=1050,
        cost_total=Decimal("0.01000000"),
        pricing_status="priced",
    )
    ModelUsage.objects.create(
        event_id="agent-usage:2",
        occurred_at=datetime(2026, 10, 20, 16, 1, 0),
        provider="deepseek",
        category="LLM",
        model="deepseek-flash",
        source="task",
        execution_id=str(agent.id),
        input_tokens=200,
        cache_input_tokens=100,
        output_tokens=20,
        total_tokens=220,
        cost_total=Decimal("0.00200000"),
        pricing_status="priced",
    )

    stats = ai_usage_stats("1")
    assert stats["agents"] == []
    assert stats["input_tokens"]["total"] == 1200
    assert stats["cache_hit_tokens"]["total"] == 500
    assert stats["output_tokens"]["total"] == 70
    assert stats["deepseek_cost"]["total"] == 0.012
