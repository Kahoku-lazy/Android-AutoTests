"""GET /api/reports 以可见 AITask 为数据源。"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from apps.ai_assistant.models import AIAgent, AITask
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db, pytest.mark.report_generator]


@pytest.fixture
def auth_client(db):
    user = get_user_model().objects.create_user(
        username="report-admin",
        password="x",
        is_superuser=True,
    )
    client = Client()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}
    return user, client, headers


def _agent(user, name="rpt-agent"):
    return AIAgent.objects.create(
        name=name,
        owner=user,
        route_configs={"device_control": {"name": "UI 助手"}},
    )


def test_reports_empty_when_no_tasks(auth_client):
    _user, client, headers = auth_client
    resp = client.get("/api/reports/", {"chart_range": "7"}, **headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["runs"] == []
    assert body["summary"]["total_runs"] == 0
    assert body["summary"]["total_pass"] == 0
    assert body["summary"]["total_fail"] == 0
    assert body["summary"]["pass_rate"] == 0.0
    assert body["trend"]["range_days"] == 7
    assert body["trend"]["pass"] == [0] * 7
    assert body["trend"]["fail"] == [0] * 7
    assert body["trend"]["rate"] == [0] * 7


def test_reports_lists_visible_task_and_kpis(auth_client):
    user, client, headers = auth_client
    agent = _agent(user)
    now = timezone.now()
    task = AITask.objects.create(
        agent=agent,
        title="登录冒烟",
        status="completed",
        device_serial="SER1",
        device_label="Pixel",
        started_at=now - timedelta(minutes=2),
        finished_at=now,
    )
    resp = client.get("/api/reports/", **headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total_runs"] == 1
    assert body["summary"]["total_pass"] == 1
    assert body["summary"]["total_fail"] == 0
    row = body["runs"][0]
    assert row["run_id"] == str(task.id)
    assert row["task_name"] == "登录冒烟"
    assert row["device_serial"] == "Pixel"
    assert row["creator"] == "UI 助手"
    assert row["status"] == "completed"
    assert "case_count" not in row
    assert "passed" not in row
    assert "failed" not in row
    assert "rate" not in row
    assert row["duration"] != "—"
    assert row["started_at"]


def test_reports_pending_excluded_from_pass_fail(auth_client):
    user, client, headers = auth_client
    agent = _agent(user)
    AITask.objects.create(agent=agent, title="wait", status="pending")
    AITask.objects.create(agent=agent, title="ok", status="completed")
    AITask.objects.create(agent=agent, title="ok-alias", status="success")
    AITask.objects.create(agent=agent, title="bad", status="failed")
    body = client.get("/api/reports/", **headers).json()
    assert body["summary"]["total_runs"] == 4
    assert body["summary"]["total_pass"] == 2
    assert body["summary"]["total_fail"] == 1
    assert body["summary"]["pass_rate"] == 66.7


def test_reports_device_falls_back_to_serial(auth_client):
    user, client, headers = auth_client
    agent = _agent(user)
    AITask.objects.create(
        agent=agent,
        title="无别名",
        status="failed",
        device_serial="ABC123",
        device_label="",
    )
    row = client.get("/api/reports/", **headers).json()["runs"][0]
    assert row["device_serial"] == "ABC123"
