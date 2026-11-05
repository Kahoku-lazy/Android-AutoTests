"""仪表盘加载预算：一次请求只读一次智能体、SQL 条数上限、响应字段完整。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.dashboard.views import DashboardStatsAPIView

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

TOP_LEVEL_KEYS = (
    "devices",
    "cases",
    "workflow",
    "runs",
    "agents",
    "ai_usage",
    "usage_ledger",
    "charts",
    "execution_summary",
    "recent_tasks",
    "last_updated",
    "system_status",
)


def _make_user():
    """先建好用户与智能体，避免建库语句混进被测量的查询窗口。"""
    user = get_user_model().objects.create_user(username="dash-budget", password="x")
    AIAgent.objects.create(name="预算智能体", owner=user, avatar="x" * 1024)
    return user


def _stats_response(user):
    request = APIRequestFactory().get("/api/dashboard/stats/")
    force_authenticate(request, user=user)
    return DashboardStatsAPIView.as_view()(request)


def test_stats_reads_agents_once_without_avatar():
    """统计请求只查一次 ai_agents，且不读取 avatar 大字段。"""
    user = _make_user()
    with CaptureQueriesContext(connection) as ctx:
        response = _stats_response(user)

    assert response.status_code == 200
    agent_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if "ai_agents" in query["sql"] and query["sql"].lstrip().startswith("SELECT")
    ]
    assert len(agent_queries) == 1, agent_queries
    assert "avatar" not in agent_queries[0]


def test_stats_stays_within_query_budget():
    """单次统计请求 SQL 不超过 25 条。"""
    user = _make_user()
    with CaptureQueriesContext(connection) as ctx:
        _stats_response(user)

    assert len(ctx.captured_queries) <= 25


def test_stats_response_shape_unchanged():
    """响应顶层字段仍完整，用量账本仍是五个口径。"""
    response = _stats_response(_make_user())
    data = response.data

    for key in TOP_LEVEL_KEYS:
        assert key in data, key
    ledger = data["usage_ledger"]
    assert {"today", "total", "voice_today", "voice_total", "recent"} <= set(ledger)
    for name in ("today", "total", "voice_today", "voice_total"):
        assert {"period", "total", "categories"} <= set(ledger[name])
