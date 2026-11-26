from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

MILESTONE = """
name: 存储失败
steps:
  - subject: 点一下
    description: 页面已打开
    max_attempts: 3
""".strip()

DEVICE = "R5CT62RH88F"

STORAGE_MESSAGE = "任务配置文件写入失败：Permission denied，请检查运行账号对该目录的写权限"


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


@pytest.fixture(autouse=True)
def _workflow_and_no_dispatch(monkeypatch):
    monkeypatch.setattr(api, "dispatch_device", lambda serial: None)
    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: type(
            "Workflow",
            (),
            {
                "id": workflow_id,
                "name": "回归工作流",
                "release_state": "published",
                "kind": "ui",
                "orchestration": "goal",
            },
        )(),
    )


def _boom(*args, **kwargs):
    raise PermissionError(13, "Permission denied")


def _yaml_file() -> SimpleUploadedFile:
    return SimpleUploadedFile("case.yaml", MILESTONE.encode("utf-8"), content_type="text/yaml")


def _submit(user, *, data: dict, files: dict | None = None):
    factory = APIRequestFactory()
    request = factory.post("/api/tasks/submit/", data, format="multipart")
    if files:
        request.FILES.update(files)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


def _envelope(response) -> dict:
    response.render()
    assert response["Content-Type"].startswith("application/json")
    return json.loads(response.content)


def _submit_yaml(user):
    return _submit(
        user,
        data={"title": "任务", "workflow_id": 7, "device_serial": DEVICE},
        files={"config": _yaml_file()},
    )


def test_storage_failure_returns_readable_envelope(admin_user, monkeypatch):
    monkeypatch.setattr("backend.apps.task_list.attachments.store_flat_upload", _boom)
    response = _submit_yaml(admin_user)
    envelope = _envelope(response)
    assert response.status_code == 500
    assert envelope["status"] is False
    assert "写入失败" in envelope["message"]
    assert "写权限" in envelope["message"]
    assert "Traceback" not in str(envelope)


def test_storage_failure_keeps_task_out_of_db(admin_user, monkeypatch):
    monkeypatch.setattr("backend.apps.task_list.attachments.store_flat_upload", _boom)
    before = Task.objects.count()
    assert _submit_yaml(admin_user).status_code == 500
    assert Task.objects.count() == before


def test_success_envelope_and_missing_workflow_message(admin_user, monkeypatch):
    monkeypatch.setattr(
        "backend.apps.task_list.attachments.store_flat_upload",
        lambda filename, content: "stub.yaml",
    )
    ok = _submit_yaml(admin_user)
    body = _envelope(ok)
    assert ok.status_code == 200
    assert body["status"] is True
    assert set(body["data"]) >= {"id", "status"}

    missing = _submit(
        admin_user,
        data={"title": "任务", "device_serial": DEVICE},
        files={"config": _yaml_file()},
    )
    assert missing.status_code == 400
    missing_message = _envelope(missing)["message"]
    assert "请选择智能体" in missing_message
    assert "写入失败" not in missing_message


def test_platform_case_storage_failure_uses_same_message(admin_user, monkeypatch):
    monkeypatch.setattr(
        "backend.apps.case_manager.api.automation_case_identity",
        lambda case_ids, user_id: [{"case_id": case_ids[0]}],
    )
    monkeypatch.setattr(
        "backend.apps.case_manager.api.compile_automation_cases",
        lambda case_ids, user_id: MILESTONE,
    )
    monkeypatch.setattr("backend.apps.task_list.attachments.store_flat_upload", _boom)
    before = Task.objects.count()
    response = _submit(
        admin_user,
        data={
            "title": "任务",
            "workflow_id": 7,
            "device_serial": DEVICE,
            "case_source": "platform",
            "case_ids": json.dumps(["c1"]),
        },
    )
    body = _envelope(response)
    assert response.status_code == 500
    assert body["message"] == STORAGE_MESSAGE
    assert Task.objects.count() == before
