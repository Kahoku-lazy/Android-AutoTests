"""平台自动化用例提交：编译成里程碑附件，不新增用例行。"""

from __future__ import annotations

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from backend.apps.case_manager import api as case_api
from backend.apps.case_manager.models import AutomationCase
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

User = get_user_model()
_STEP = [{"action": "点电源", "assertion": "灯亮"}]


def _post(user, body):
    request = RequestFactory().post("/api/tasks/submit/", data=body)
    request.user_id = str(user.id)
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(user.id))}"
    return TaskSubmitAPIView.as_view()(request)


def test_platform_submit_stores_milestone_without_new_rows(monkeypatch):
    user = User.objects.create_user(username="sheet-runner", password="x")
    project_id = case_api.create_project(name="可执行", library_kind="automation", user_id=str(user.id))["id"]
    first = case_api.create_row(project_id=project_id, user_id=str(user.id), title="甲", steps=_STEP)
    second = case_api.create_row(
        project_id=project_id,
        user_id=str(user.id),
        title="乙",
        steps=[{"action": "返回", "assertion": "回到桌面"}],
    )
    before = AutomationCase.objects.count()
    monkeypatch.setattr("backend.apps.task_list.api.dispatch_device", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: type("Workflow", (), {"id": workflow_id})(),
    )
    response = _post(
        user,
        {
            "title": "回归",
            "workflow_id": "7",
            "device_serial": "R5CT62RH88F",
            "case_source": "platform",
            "case_ids": json.dumps([second["id"], first["id"]]),
        },
    )
    assert response.status_code == 200
    task = Task.objects.get(id=response.data["id"])
    attachment = task.file_attachments.get()
    assert "subject:" in attachment.body
    assert attachment.body.index("乙") < attachment.body.index("甲")
    assert AutomationCase.objects.count() == before
    assert task.title == "回归"
    assert task.case_identity == {
        "source": "platform",
        "rows": [
            {"project": "可执行", "id": second["id"], "title": "乙"},
            {"project": "可执行", "id": first["id"], "title": "甲"},
        ],
    }
