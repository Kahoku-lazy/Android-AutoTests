"""
模块功能：➡️ 工作流任务提交：必须有工作流和设备；上传里程碑不把文件名写入用例身份 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/task/api/test_task_submit_sop.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/task_list、backend/apps/ai_assistant
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

MILESTONE = """
name: 回归
steps:
  - subject: 点一下
    description: 页面已打开
    max_attempts: 3
""".strip()


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


def _submit(user, *, data: dict, files: dict | None = None):
    factory = APIRequestFactory()
    request = factory.post("/api/tasks/submit/", data, format="multipart")
    if files:
        request.FILES.update(files)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


def _yaml_file(name: str = "case.yaml") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, MILESTONE.encode("utf-8"), content_type="text/yaml")


@pytest.fixture(autouse=True)
def _workflow_and_no_dispatch(monkeypatch):
    monkeypatch.setattr(api, "dispatch_device", lambda serial: None)
    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: type("Workflow", (), {"id": workflow_id, "name": "回归工作流"})(),
    )


def test_requires_workflow(admin_user):
    response = _submit(
        admin_user,
        data={"title": "任务", "device_serial": "R5CT62RH88F"},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "智能体" in str(response.data)


def test_rejects_unknown_workflow(admin_user, monkeypatch):
    from backend.apps.ai_assistant.models import AISopWorkflow

    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: (_ for _ in ()).throw(AISopWorkflow.DoesNotExist()),
    )
    response = _submit(
        admin_user,
        data={"title": "任务", "workflow_id": 99999, "device_serial": "R5CT62RH88F"},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "工作流" in str(response.data)


def test_requires_device(admin_user):
    response = _submit(
        admin_user,
        data={"title": "任务", "workflow_id": 7},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "设备" in str(response.data)


def test_requires_yaml(admin_user):
    response = _submit(
        admin_user,
        data={"title": "任务", "workflow_id": 7, "device_serial": "R5CT62RH88F"},
    )
    assert response.status_code == 400
    assert "YAML" in str(response.data)


def test_milestone_upload_does_not_store_filename_as_case_identity(admin_user):
    response = _submit(
        admin_user,
        data={
            "title": "任务",
            "workflow_id": 7,
            "device_serial": "R5CT62RH88F",
            "case_title": "乙",
        },
        files={"config": _yaml_file()},
    )
    assert response.status_code == 200
    task = Task.objects.get(id=response.data["id"])
    assert task.case_title == ""
    assert task.case_identity == {"source": "milestone", "rows": []}
    assert "case.yaml" not in str(task.case_identity)
    assert task.device_serial == "R5CT62RH88F"
    assert task.title == "任务"

    config = task.file_attachments.get(kind="config")
    assert config.filename == "case.yaml"
    assert "subject: 点一下" in config.body


def test_run_input_template_only_uses_device_serial():
    task = Task(device_serial="R5CT62RH88F")
    assert (
        api.build_sop_run_input(task)
        == "本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。"
    )
