from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import AgentTaskListAPIView
from backend.models.constants import TaskKind

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _list_tasks(user) -> list[dict]:
    request = APIRequestFactory().get("/api/tasks/")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = AgentTaskListAPIView.as_view()(request)
    assert response.status_code == 200
    return response.data["tasks"]


def test_task_row_reports_creator_account_name():
    user = get_user_model().objects.create_user(
        username="Kahoku", password="pass", is_superuser=True, is_staff=True
    )
    task = api.create_task(
        title="创建人回读",
        goal="目标",
        task_kind=TaskKind.ASSISTANT_SOP,
        created_by=str(user.id),
    )

    rows = _list_tasks(user)
    row = next(item for item in rows if item["id"] == task.id)
    assert row["created_by"] == str(user.id)
    assert row["created_by_name"] == "Kahoku"
    assert Task.objects.get(pk=task.id).created_by == str(user.id)

    Task.objects.filter(pk=task.id).update(created_by="")
    row = next(item for item in _list_tasks(user) if item["id"] == task.id)
    assert row["created_by"] == ""
    assert row["created_by_name"] == ""

    Task.objects.filter(pk=task.id).update(created_by="not-a-user")
    row = next(item for item in _list_tasks(user) if item["id"] == task.id)
    assert row["created_by"] == "not-a-user"
    assert row["created_by_name"] == ""
