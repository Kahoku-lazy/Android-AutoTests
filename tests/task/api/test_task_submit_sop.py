"""任务提交契约：agent_id / device_serial / case_title 与 YAML 必填。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant import api as agent_api
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

YAML_TEXT = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
- title: 乙
  steps:
    - action: 再点一下
      assert: 页面已切换
""".strip()


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


@pytest.fixture
def sop_agent(db):
    key = agent_api.encrypt_key("sk-test")
    route = {
        "device_control": {
            "name": "Agent-01号",
            "executor": {"provider": "deepseek", "model_name": "deepseek-flash", "api_key": key},
            "verifier": {"provider": "deepseek", "model_name": "deepseek-flash", "api_key": key},
        }
    }
    return AIAgent.objects.create(name="自动化小助手", route_configs=route)


def _submit(user, *, data: dict, files: dict | None = None):
    factory = APIRequestFactory()
    request = factory.post("/api/tasks/submit/", data, format="multipart")
    if files:
        request.FILES.update(files)
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


def _yaml_file(name: str = "case.yaml") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, YAML_TEXT.encode("utf-8"), content_type="text/yaml")


@pytest.fixture(autouse=True)
def _no_dispatch(monkeypatch):
    monkeypatch.setattr(api, "dispatch_device", lambda serial: None)


def test_requires_agent_id(admin_user, sop_agent):
    response = _submit(
        admin_user,
        data={"title": "任务", "device_serial": "R5CT62RH88F"},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "智能体" in str(response.data)


def test_rejects_unknown_agent(admin_user):
    response = _submit(
        admin_user,
        data={"title": "任务", "agent_id": 99999, "device_serial": "R5CT62RH88F"},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "智能体" in str(response.data)


def test_requires_device(admin_user, sop_agent):
    response = _submit(
        admin_user,
        data={"title": "任务", "agent_id": sop_agent.id},
        files={"config": _yaml_file()},
    )
    assert response.status_code == 400
    assert "设备" in str(response.data)


def test_requires_yaml(admin_user, sop_agent):
    response = _submit(
        admin_user,
        data={"title": "任务", "agent_id": sop_agent.id, "device_serial": "R5CT62RH88F"},
    )
    assert response.status_code == 400
    assert "YAML" in str(response.data)


def test_creates_task_with_case_title(admin_user, sop_agent):
    response = _submit(
        admin_user,
        data={
            "title": "任务",
            "agent_id": sop_agent.id,
            "device_serial": "R5CT62RH88F",
            "case_title": "乙",
        },
        files={"config": _yaml_file()},
    )
    assert response.status_code == 200
    task = Task.objects.get(id=response.data["id"])
    assert task.case_title == "乙"
    assert task.device_serial == "R5CT62RH88F"
    assert task.agent_id == sop_agent.id

    config = task.file_attachments.get(kind="config")
    assert "标题" not in config.body  # YAML 原文保留
    assert "title: 乙" in config.body


def test_run_input_template_only_uses_device_serial():
    task = Task(device_serial="R5CT62RH88F")
    assert (
        api.build_sop_run_input(task)
        == "本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。"
    )
