"""智能体接口瘦身与任务列表查询预算：列表不带头像、任务列表 SQL 不随任务数放大。"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.ai_assistant.serializers import AgentInputSerializer
from backend.apps.ai_assistant.views_drf import AgentViewSet
from backend.apps.task_list import api as task_api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import AgentTaskListAPIView

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

BIG_AVATAR = "x" * 5000


def _user():
    return get_user_model().objects.create_user(username="payload-user", password="x")


def _request(path: str, user):
    request = APIRequestFactory().get(path)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return request


def test_agent_list_has_no_avatar_and_stays_small():
    """列表响应不含头像，整体小于 64KB。"""
    user = _user()
    AIAgent.objects.create(
        name="带大头的智能体",
        owner=user,
        avatar="A" * 200_000,
        route_configs={"device_control": {"name": "线路A", "avatar": "B" * 200_000}},
    )

    response = AgentViewSet.as_view({"get": "list"})(_request("/api/ai/agents/", user))
    payload = json.dumps(response.data, ensure_ascii=False).encode("utf-8")

    assert response.status_code == 200
    assert len(payload) < 64 * 1024
    agent = response.data["agents"][0]
    assert "avatar" not in agent
    assert "avatar" not in agent["route_configs"]["device_control"]


def test_agent_detail_has_no_avatar():
    """详情同样不下发头像大字段。"""
    user = _user()
    agent = AIAgent.objects.create(
        name="详情智能体",
        owner=user,
        avatar="A" * 200_000,
        route_configs={"device_control": {"name": "线路B", "avatar": "B" * 200_000}},
    )

    response = AgentViewSet.as_view({"get": "retrieve"})(
        _request(f"/api/ai/agents/{agent.id}/", user),
        pk=agent.id,
    )

    assert response.status_code == 200
    assert "avatar" not in response.data["agent"]


def test_oversized_avatar_is_rejected():
    """写入侧拒绝超过 4096 字符的头像。"""
    serializer = AgentInputSerializer(data={"name": "x", "avatar": BIG_AVATAR})

    assert serializer.is_valid() is False
    assert "avatar" in serializer.errors


def test_task_list_reads_agents_once_without_join():
    """任务列表 SQL ≤ 5 条，且不再联表读取智能体。"""
    user = _user()
    agent = AIAgent.objects.create(name="任务线路", owner=user)
    for index in range(5):
        Task.objects.create(agent=agent, title=f"t{index}", goal="g", created_by=str(user.id))

    with CaptureQueriesContext(connection) as ctx:
        response = AgentTaskListAPIView.as_view()(_request("/api/tasks/", user))

    sql = [query["sql"] for query in ctx.captured_queries]
    assert response.status_code == 200
    assert len(sql) <= 5, sql
    assert not any("JOIN" in statement for statement in sql)


def test_task_list_keeps_row_fields():
    """列表行字段与口径不变（线路名、附件名、费用）。"""
    user = _user()
    agent = AIAgent.objects.create(
        name="线路显示名",
        owner=user,
        route_configs={"device_control": {"name": "任务线路"}},
    )
    task = Task.objects.create(agent=agent, title="任务", goal="g", created_by=str(user.id))
    task_api.add_task_attachment(
        task,
        kind="config",
        filename="a.yaml",
        body="x",
        sort_order=0,
    )

    with CaptureQueriesContext(connection) as ctx:
        response = AgentTaskListAPIView.as_view()(_request("/api/tasks/", user))

    row = response.data["tasks"][0]
    assert row["assistant_name"] == "任务线路"
    assert row["attachment_names"] == ["a.yaml"]
    assert "deepseek_cost" in row
    assert len(ctx.captured_queries) <= 5
