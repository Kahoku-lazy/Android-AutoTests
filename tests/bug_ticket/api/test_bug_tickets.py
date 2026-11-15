"""BUG 单接口：列表、详情、状态更新与历史同步。"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.bug_manager import api as bug_api
from backend.apps.bug_manager.models import BugTicket
from backend.apps.bug_manager.views import (
    BugDetailAPIView,
    BugListAPIView,
    BugSyncAPIView,
)
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind, TaskStatus

pytestmark = [pytest.mark.api, pytest.mark.django_db]


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="bug-api-user", password="x", is_superuser=True, is_staff=True
    )


@pytest.fixture
def task(user):
    agent = AIAgent.objects.create(owner=user, name="Agent-01", task_kind=TaskKind.DEVICE_CONTROL)
    return Task.objects.create(
        agent=agent,
        title="H6810 全功能测试",
        task_kind=TaskKind.DEVICE_CONTROL,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {
                "status": "fail",
                "reason": "图片页未完成；涂鸦页未完成",
                "failed": ["图片页", "涂鸦页"],
            },
            ensure_ascii=False,
        ),
    )


def _call(view, method: str, user, *, path="/api/bugs/", data=None, **params):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return view.as_view()(request, **params)


def test_list_returns_summary_and_category_filter(user, task):
    bug_api.record_task_bugs(task)

    response = _call(BugListAPIView, "get", user, data=None)
    assert response.status_code == 200
    assert response.data["summary"]["total"] == 2
    assert response.data["summary"]["ui_automation"] == 2
    assert response.data["total"] == 2
    assert response.data["items"][0]["task_id"] == task.id
    assert response.data["items"][0]["bug_no"].startswith("BUG-")

    filtered = _call(
        BugListAPIView,
        "get",
        user,
        data={"category": "case_authoring"},
    )
    assert filtered.status_code == 200
    assert filtered.data["total"] == 0


def test_list_filters_by_status_and_keyword(user, task):
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.filter(task_id=task.id).first()
    ticket.status = BugTicket.STATUS_RESOLVED
    ticket.save(update_fields=["status"])

    response = _call(
        BugListAPIView,
        "get",
        user,
        data=None,
    )
    assert response.status_code == 200

    factory = APIRequestFactory()
    request = factory.get("/api/bugs/", {"status": "resolved"})
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    resolved = BugListAPIView.as_view()(request)
    assert resolved.status_code == 200
    assert resolved.data["total"] == 1


def test_detail_and_status_update(user, task):
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.filter(task_id=task.id).first()

    detail = _call(BugDetailAPIView, "get", user, bug_id=ticket.id)
    assert detail.status_code == 200
    assert "图片页" in detail.data["detail"]

    patched = _call(
        BugDetailAPIView,
        "patch",
        user,
        data={"status": "resolved"},
        bug_id=ticket.id,
    )
    assert patched.status_code == 200
    assert patched.data["status"] == "resolved"
    assert patched.data["resolved_at"]


def test_invalid_status_is_rejected(user, task):
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.filter(task_id=task.id).first()

    response = _call(
        BugDetailAPIView,
        "patch",
        user,
        data={"status": "done"},
        bug_id=ticket.id,
    )

    assert response.status_code == 400
    ticket.refresh_from_db()
    assert ticket.status == BugTicket.STATUS_OPEN


def test_invisible_ticket_returns_404():
    owner = get_user_model().objects.create_user(username="bug-owner-x", password="x")
    other = get_user_model().objects.create_user(username="bug-other-x", password="x")
    agent = AIAgent.objects.create(owner=owner, name="Agent-X", task_kind=TaskKind.DEVICE_CONTROL)
    task = Task.objects.create(
        agent=agent,
        title="X",
        task_kind=TaskKind.DEVICE_CONTROL,
        status=TaskStatus.FAILED,
        result=json.dumps({"status": "fail", "failed": []}, ensure_ascii=False),
    )
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.get(task_id=task.id)

    response = _call(BugDetailAPIView, "get", other, bug_id=ticket.id)

    assert response.status_code == 404


def test_sync_backfills_and_is_idempotent(user, task):
    first = _call(BugSyncAPIView, "post", user, path="/api/bugs/sync/", data={})
    second = _call(BugSyncAPIView, "post", user, path="/api/bugs/sync/", data={})

    assert first.status_code == 200
    assert first.data["created"] == 2
    assert second.data["created"] == 0
    assert BugTicket.objects.filter(task_id=task.id).count() == 2
