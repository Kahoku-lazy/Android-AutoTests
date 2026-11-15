"""停机排空：标志位、派发阻断、本机端点与 JWT 放行边界。"""

from __future__ import annotations

import pytest

from django.http import JsonResponse
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskDrainAPIView
from backend.gateway.middleware import JWTAuthenticationMiddleware
from backend.models.constants import TaskStatus

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

DRAIN_PATH = "/api/system/drain/"


@pytest.fixture(autouse=True)
def _reset_drain_flag(monkeypatch):
    """每个用例从“未排空”开始，避免进程内标志串味。"""
    monkeypatch.setattr(api, "_DRAINING", False)
    yield


def test_dispatch_is_blocked_while_draining():
    """排空后不再领取 pending 任务，任务保持排队。"""
    agent = AIAgent.objects.create(name="drain-agent")
    task = Task.objects.create(
        agent=agent, title="queued", status=TaskStatus.PENDING, device_serial="S1"
    )

    api.begin_drain()

    assert api.is_draining() is True
    assert api.dispatch_device("S1") is None
    task.refresh_from_db()
    assert task.status == TaskStatus.PENDING


def test_count_running_tasks():
    """只统计 running，pending/completed 不计。"""
    agent = AIAgent.objects.create(name="drain-agent")
    Task.objects.create(agent=agent, title="r1", status=TaskStatus.RUNNING)
    Task.objects.create(agent=agent, title="r2", status=TaskStatus.RUNNING)
    Task.objects.create(agent=agent, title="p", status=TaskStatus.PENDING)
    Task.objects.create(agent=agent, title="c", status=TaskStatus.COMPLETED)

    assert api.count_running_tasks() == 2


def test_drain_view_allows_loopback():
    """回环来源可置位排空并拿到 running 数。"""
    request = APIRequestFactory().post(DRAIN_PATH, REMOTE_ADDR="127.0.0.1")

    response = TaskDrainAPIView.as_view()(request)

    assert response.status_code == 200
    assert response.data["draining"] is True
    assert response.data["running"] == 0


def test_drain_view_rejects_non_loopback():
    """非回环来源不能操作停机开关。"""
    request = APIRequestFactory().post(DRAIN_PATH, REMOTE_ADDR="10.1.2.3")

    response = TaskDrainAPIView.as_view()(request)

    assert response.status_code == 403
    assert api.is_draining() is False


def test_middleware_allows_loopback_drain_without_jwt():
    """回环来源访问排空端点不需要 JWT。"""

    def get_response(request):
        return JsonResponse({"ok": True})

    request = RequestFactory().post(DRAIN_PATH, REMOTE_ADDR="127.0.0.1")

    response = JWTAuthenticationMiddleware(get_response)(request)

    assert response.status_code == 200


def test_middleware_still_requires_jwt_for_other_api_paths():
    """放行只限排空端点：其它 /api/ 路径仍要求登录。"""

    def get_response(request):
        return JsonResponse({"ok": True})

    request = RequestFactory().get("/api/tasks/", REMOTE_ADDR="127.0.0.1")

    response = JWTAuthenticationMiddleware(get_response)(request)

    assert response.status_code == 401


def test_middleware_rejects_non_loopback_drain_without_jwt():
    """非回环来源访问排空端点仍按未登录处理。"""

    def get_response(request):
        return JsonResponse({"ok": True})

    request = RequestFactory().post(DRAIN_PATH, REMOTE_ADDR="10.1.2.3")

    response = JWTAuthenticationMiddleware(get_response)(request)

    assert response.status_code == 401
