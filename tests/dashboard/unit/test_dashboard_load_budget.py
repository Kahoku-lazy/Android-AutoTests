"""仪表盘加载预算：一次请求只读一次智能体、SQL 条数上限、响应字段完整。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.dashboard.views import DashboardStatsAPIView

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

TOP_LEVEL_KEYS = (
    "devices",
    "cases",
    "assistants",
    "workflows",
    "runs",
    "ai_usage",
    "usage_ledger",
    "charts",
    "execution_summary",
    "recent_tasks",
    "last_updated",
    "system_status",
)


def _make_user():
    """先建好用户，避免建库语句混进被测量的查询窗口。"""
    return get_user_model().objects.create_user(username="dash-budget", password="x")


def _stats_response(user):
    request = APIRequestFactory().get("/api/dashboard/stats/")
    force_authenticate(request, user=user)
    return DashboardStatsAPIView.as_view()(request)


def test_stats_does_not_read_retired_agent_table():
    """智能体表已下线，统计请求不再查询 ai_agents。"""
    user = _make_user()
    with CaptureQueriesContext(connection) as ctx:
        response = _stats_response(user)

    assert response.status_code == 200
    agent_queries = [query["sql"] for query in ctx.captured_queries if "ai_agents" in query["sql"]]
    assert agent_queries == []


def test_stats_stays_within_query_budget():
    """单次统计请求 SQL 不超过 32 条。

    平台概览新增助手、工作流、任务状态与运营三项的只读计数。
    """
    user = _make_user()
    with CaptureQueriesContext(connection) as ctx:
        _stats_response(user)

    assert len(ctx.captured_queries) <= 32


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
