"""任务统计接口契约：状态口径、成功率分母与可见范围。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import AgentTaskStatsAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/tasks/stats/"


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="stats-admin", password="pass", is_superuser=True, is_staff=True
    )


@pytest.fixture
def agent(db):
    return AIAgent.objects.create(name="统计用助手", route_configs={})


def _stats(user) -> dict:
    factory = APIRequestFactory()
    request = factory.get(URL)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = AgentTaskStatsAPIView.as_view()(request)
    assert response.status_code == 200
    return response.data


def _make_tasks(agent, status: str, count: int) -> None:
    for index in range(count):
        Task.objects.create(
            agent=agent,
            title=f"{status}-{index}",
            task_kind="device_control",
            status=status,
        )


def test_counts_and_success_rate(admin_user, agent):
    _make_tasks(agent, "completed", 9)
    _make_tasks(agent, "failed", 1)
    _make_tasks(agent, "running", 2)

    data = _stats(admin_user)
    assert data["total"] == 12
    assert data["running"] == 2
    assert data["success"] == 9
    assert data["failed"] == 1
    assert data["finished"] == 10
    assert data["success_rate"] == 90.0


def test_success_includes_legacy_status(admin_user, agent):
    _make_tasks(agent, "completed", 1)
    _make_tasks(agent, "success", 1)
    data = _stats(admin_user)
    assert data["success"] == 2
    assert data["success_rate"] == 100.0


def test_running_and_pending_are_not_finished(admin_user, agent):
    _make_tasks(agent, "running", 1)
    _make_tasks(agent, "pending", 2)
    data = _stats(admin_user)
    assert data["total"] == 3
    assert data["finished"] == 0
    assert data["success_rate"] == 0.0


def test_empty_library_returns_zeros(admin_user, agent):
    data = _stats(admin_user)
    assert data["total"] == 0
    assert data["finished"] == 0
    assert data["success_rate"] == 0.0


def test_other_users_tasks_are_excluded(db, agent):
    owner = get_user_model().objects.create_user(username="stats-owner", password="pass")
    other = get_user_model().objects.create_user(username="stats-other", password="pass")
    other_agent = AIAgent.objects.create(name="别人的助手", owner_id=str(other.id), route_configs={})
    _make_tasks(agent, "completed", 2)
    _make_tasks(other_agent, "failed", 5)

    data = _stats(owner)
    assert data["total"] == 2
    assert data["failed"] == 0
    assert data["success_rate"] == 100.0


def test_query_count_does_not_scale_with_rows(admin_user, agent, django_assert_max_num_queries):
    _make_tasks(agent, "completed", 40)
    with django_assert_max_num_queries(6):
        data = _stats(admin_user)
    assert data["total"] == 40


def test_agents_list_covers_every_visible_agent(admin_user, agent):
    empty_agent = AIAgent.objects.create(name="还没跑过的助手", route_configs={})
    _make_tasks(agent, "completed", 2)

    data = _stats(admin_user)
    by_id = {row["id"]: row for row in data["agents"]}
    assert set(by_id) == {agent.id, empty_agent.id}
    assert by_id[agent.id]["total"] == 2
    assert by_id[empty_agent.id]["total"] == 0
    assert by_id[empty_agent.id]["success_rate"] == 0.0


def test_agent_counts_follow_status(admin_user, agent):
    other_agent = AIAgent.objects.create(name="另一个助手", route_configs={})
    _make_tasks(agent, "completed", 2)
    _make_tasks(agent, "failed", 1)
    _make_tasks(other_agent, "interrupted", 1)

    data = _stats(admin_user)
    by_id = {row["id"]: row for row in data["agents"]}
    assert by_id[agent.id]["success"] == 2
    assert by_id[agent.id]["failed"] == 1
    assert by_id[agent.id]["success_rate"] == 66.7
    assert by_id[other_agent.id]["interrupted"] == 1
    assert by_id[other_agent.id]["success_rate"] == 0.0


def test_agent_name_comes_from_route_config(db):
    owner = get_user_model().objects.create_user(username="stats-namer", password="pass")
    agent = AIAgent.objects.create(
        name="内部名",
        route_configs={"device_control": {"name": "Agent-01号"}},
    )
    _make_tasks(agent, "completed", 1)

    data = _stats(owner)
    assert data["agents"][0]["name"] == "Agent-01号"


def test_other_users_agent_absent_from_agents_list(db, agent):
    owner = get_user_model().objects.create_user(username="stats-viewer", password="pass")
    other = get_user_model().objects.create_user(username="stats-stranger", password="pass")
    other_agent = AIAgent.objects.create(name="别人的助手", owner_id=str(other.id), route_configs={})
    _make_tasks(other_agent, "completed", 1)

    data = _stats(owner)
    ids = [row["id"] for row in data["agents"]]
    assert other_agent.id not in ids
