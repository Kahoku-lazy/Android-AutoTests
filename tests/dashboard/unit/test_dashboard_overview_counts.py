"""平台概览计数：助手、工作流、运行中、排队，以及运营字段裁剪。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind
from backend.shared.auth.jwt_auth import create_access_token
from backend.shared.users import OPERATOR_GROUP

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

User = get_user_model()
STATS_URL = "/api/dashboard/stats/"


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


def _seed_counts():
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
    )
    role = AIRole.objects.create(role_id="20261117abc", name="执行", model_config=config)
    AIAssistant.objects.create(
        assistant_id="20261117_001",
        display_name="小助",
        marker="teal",
        role_id=role.role_id,
    )
    AISopWorkflow.objects.create(
        name="检查",
        executor_assistant_id="20261117_001",
        verifier_assistant_id="20261117_001",
    )
    Task.objects.create(title="跑着", status="running", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="排队", status="pending", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="退役", status="running", task_kind=TaskKind.DEVICE_CONTROL)


def test_overview_counts_workflow_tasks_only(client):
    user = User.objects.create_user(username="overview-user", password="x")
    _seed_counts()

    data = client.get(STATS_URL, **_headers(user)).json()["data"]

    assert data["assistants"]["total"] == 1
    assert data["workflows"]["total"] == 1
    assert data["runs"] == {"active": 1, "pending": 1}
    assert data["ai_usage"]["task_count"]["total"] == 2
    assert "ops" not in data


def test_operator_and_superuser_receive_ops_counts(client):
    operator = User.objects.create_user(username="overview-ops", password="x")
    operator.groups.add(Group.objects.create(name=OPERATOR_GROUP))
    superuser = User.objects.create_user(username="overview-root", password="x", is_superuser=True)
    _seed_counts()

    for user in (operator, superuser):
        ops = client.get(STATS_URL, **_headers(user)).json()["data"]["ops"]
        assert ops["users"] == 2
        assert ops["agents"] == 1
        assert ops["models"] == 1


def test_anonymous_stats_stay_unauthorized(client):
    response = client.get(STATS_URL)
    assert response.status_code == 401
    assert "ops" not in response.json()
