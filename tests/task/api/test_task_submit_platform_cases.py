"""平台用例来源的任务提交契约：物化 YAML 配置附件、越权与非法入参拒绝。"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant import api as agent_api
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.case_manager import api as case_api
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

CASE_STEPS = [
    {
        "action": "点击电源按钮",
        "assertion": "设备日志返回开关成功",
        "anchor": {"page": "H6810 详情页", "entry": "右上角电源按钮"},
        "log": {"sku": "H6810", "port": 7005, "keywords": ["switch_on"]},
    },
    {"action": "拖动亮度条", "assertion": "设备日志返回亮度设置成功"},
]


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


@pytest.fixture
def cases(admin_user):
    """一个项目 + 一张表 + 两条带执行提示的用例。"""
    user_id = str(admin_user.id)
    project = case_api.create_project(name="H6810 用例库", user_id=user_id)
    case_file = case_api.create_file(
        project_id=project["id"], name="H6810_structured_cases", user_id=user_id
    )
    ids = []
    for index, title in enumerate(["H6810 详情页开关与亮度功能测试", "H6810 颜色功能测试"]):
        row = case_api.create_definition(
            project_id=project["id"],
            file_id=case_file["id"],
            user_id=user_id,
            title=title,
            steps=CASE_STEPS,
            sort_order=index,
        )
        ids.append(row["id"])
    return ids


@pytest.fixture(autouse=True)
def _no_dispatch(monkeypatch):
    monkeypatch.setattr(api, "dispatch_device", lambda serial: None)


def _submit(user, data: dict):
    factory = APIRequestFactory()
    request = factory.post("/api/tasks/submit/", data, format="multipart")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


def _platform_payload(agent_id: int, case_ids) -> dict:
    return {
        "title": "H6810 平台用例回归",
        "agent_id": agent_id,
        "device_serial": "R5CT62RH88F",
        "device_label": "SM-G9730",
        "case_source": "platform",
        "case_ids": json.dumps(case_ids, ensure_ascii=False),
    }


def test_platform_cases_create_task_with_config_attachment(admin_user, sop_agent, cases):
    response = _submit(admin_user, _platform_payload(sop_agent.id, cases))
    assert response.status_code == 200, response.data

    task = Task.objects.get(id=response.data["id"])
    assert task.case_title == ""
    assert task.device_serial == "R5CT62RH88F"

    config = task.file_attachments.get(kind="config")
    assert config.filename == "平台用例-2条.yaml"
    assert "H6810 详情页开关与亮度功能测试" in config.body
    assert "anchor:" in config.body
    assert "keywords:" in config.body
    # 服务端生成的配置不落磁盘原件：materialize_config_file 会用正文写临时文件
    assert config.stored_path == ""


def test_platform_cases_keep_selection_order(admin_user, sop_agent, cases):
    response = _submit(admin_user, _platform_payload(sop_agent.id, list(reversed(cases))))
    assert response.status_code == 200
    task = Task.objects.get(id=response.data["id"])
    body = task.file_attachments.get(kind="config").body
    assert body.index("H6810 颜色功能测试") < body.index("H6810 详情页开关与亮度功能测试")


def test_empty_case_ids_rejected(admin_user, sop_agent):
    response = _submit(admin_user, _platform_payload(sop_agent.id, []))
    assert response.status_code == 400
    assert "平台用例" in str(response.data)
    assert Task.objects.count() == 0


def test_invalid_case_ids_json_rejected(admin_user, sop_agent):
    payload = _platform_payload(sop_agent.id, [])
    payload["case_ids"] = "not-json"
    response = _submit(admin_user, payload)
    assert response.status_code == 400
    assert "JSON" in str(response.data)


def test_other_users_case_rejected(admin_user, sop_agent, cases):
    other = get_user_model().objects.create_user(username="someone", password="pass")
    response = _submit(other, _platform_payload(sop_agent.id, cases))
    assert response.status_code == 404
    assert Task.objects.count() == 0


def test_missing_case_rejected(admin_user, sop_agent, cases):
    response = _submit(admin_user, _platform_payload(sop_agent.id, ["TC-19700101-0001"]))
    assert response.status_code == 404
    assert Task.objects.count() == 0
