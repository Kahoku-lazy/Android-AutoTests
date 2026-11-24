"""
模块功能：➡️ 报告台账接口契约：标准信封、鉴权与退役端点 404 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/report/integration/test_report_envelope.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant、backend/apps/task_list、backend/models/constants.py
🏁
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage, AIAssistantThread
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind, TaskStatus
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture
def auth_client(db):
    user = get_user_model().objects.create_user(username="report-user", password="x")
    return Client(HTTP_AUTHORIZATION="Bearer " + create_access_token(str(user.pk)))


def _seed_one_report_of_each_source():
    Task.objects.create(
        title="SOP 任务",
        task_kind=TaskKind.ASSISTANT_SOP,
        status=TaskStatus.COMPLETED,
        result=json.dumps(
            {
                "status": "success",
                "report_run": "20261118_102159",
                "report_name": "20261118_102159_sop_bound.html",
            }
        ),
    )
    AIAssistant.objects.create(
        assistant_id="20261116_8PD",
        display_name="涂鸦小助手",
        marker="#7C6F83",
        role_id="R0000000001",
    )
    thread = AIAssistantThread.objects.create(
        thread_id="53c17538d163aeb4",
        assistant_id="20261116_8PD",
        status=AIAssistantThread.STATUS_DONE,
    )
    AIAssistantMessage.objects.create(
        thread=thread,
        role=AIAssistantMessage.ROLE_ASSISTANT,
        content="已完成回到桌面",
        report_id="20261116_180702",
    )


def test_list_returns_standard_envelope_with_report_payload(auth_client):
    _seed_one_report_of_each_source()

    response = auth_client.get("/api/reports/")

    assert response.status_code == 200
    body = json.loads(response.content)
    assert set(body) == {"status", "data"}
    assert body["status"] is True
    data = body["data"]
    assert set(data) == {"summary", "total", "items"}
    assert data["summary"] == {"total_reports": 2, "sop_reports": 1, "agent_reports": 1}
    assert data["total"] == 2
    assert {item["source"] for item in data["items"]} == {"sop", "agent"}
    assert "trend" not in data
    assert "runs" not in data


def test_list_empty_for_user_without_reports(auth_client):
    response = auth_client.get("/api/reports/")

    assert response.status_code == 200
    data = json.loads(response.content)["data"]
    assert data == {
        "summary": {"total_reports": 0, "sop_reports": 0, "agent_reports": 0},
        "total": 0,
        "items": [],
    }


def test_unauthenticated_request_is_rejected(db):
    response = Client().get("/api/reports/")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/api/reports/cases/",
        "/api/reports/run/123/",
        "/api/reports/legacy.csv/",
        "/api/reports/legacy.csv/content/",
    ],
)
def test_retired_endpoints_return_404(auth_client, path):
    response = auth_client.get(path)

    assert response.status_code == 404
