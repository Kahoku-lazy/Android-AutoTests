"""用例写路径契约：步骤整段替换、校验错误定位、旧字段忽略与读取查询数。

用请求工厂直调 ``TestDefinitionViewSet``，不依赖运行中的服务与 Redis；
写库仍走 ``apps.case_manager.api``，测试只断言对外可见的结果。
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.case_manager import api as case_api
from apps.case_manager import models as case_models
from apps.case_manager import views_drf as case_views

pytestmark = [pytest.mark.django_db, pytest.mark.api, pytest.mark.case_manager]


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="case-owner", password="pass")


@pytest.fixture
def sheet(user):
    """一个属于 ``user`` 的项目 + 文件。"""
    project = case_api.create_project(name="H6810", user_id=str(user.id))
    case_file = case_api.create_file(
        project_id=project["id"],
        name="详情页用例",
        user_id=str(user.id),
    )
    return project, case_file


def _call(*, method: str, user, data: dict, pk: str | None = None):
    factory = APIRequestFactory()
    path = "/api/cases/definitions/" if pk is None else f"/api/cases/definitions/{pk}/"
    request = getattr(factory, method)(path, data, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    if pk is None:
        handler = case_views.TestDefinitionViewSet.as_view({"post": "create"})
        return handler(request)
    handler = case_views.TestDefinitionViewSet.as_view({"patch": "partial_update"})
    return handler(request, pk=pk)


def _steps_payload(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    return [{"action": action, "assertion": assertion} for action, assertion in pairs]


def _create(user, sheet, *, steps, **extra):
    project, case_file = sheet
    body = {
        "project_id": project["id"],
        "file_id": case_file["id"],
        "title": "H6810 详情页开关测试",
        "steps": steps,
        **extra,
    }
    return _call(method="post", user=user, data=body)


def test_create_returns_ordered_steps_and_defaults(user, sheet):
    response = _create(
        user,
        sheet,
        steps=_steps_payload(
            ("启动 Govee Home App", "前台为 Govee，进入主页"),
            ("点击 H6810 开关按键", "设备日志出现开灯事件"),
            ("再次点击开关", "设备日志出现关灯事件"),
        ),
    )
    assert response.status_code == 201, response.data
    data = response.data
    assert data["step_count"] == 3
    assert [s["action"] for s in data["steps"]][0] == "启动 Govee Home App"
    assert [s["action"] for s in data["steps"]][2] == "再次点击开关"
    assert data["priority"] == "P1"
    assert data["system"] == "ANDROID"
    assert data["case_type"] == "AUTO"
    assert "test_type" not in data and "expected_result" not in data


def test_update_replaces_steps_entirely(user, sheet):
    created = _create(
        user,
        sheet,
        steps=_steps_payload(("A", "a"), ("B", "b"), ("C", "c")),
    ).data

    response = _call(
        method="patch",
        user=user,
        pk=created["id"],
        data={"steps": _steps_payload(("A", "a"), ("C", "c"))},
    )
    assert response.status_code == 200, response.data
    assert [s["action"] for s in response.data["steps"]] == ["A", "C"]
    assert response.data["step_count"] == 2

    remaining = list(
        case_models.CaseStep.objects.filter(case_id=created["id"]).values_list("action", flat=True)
    )
    assert remaining == ["A", "C"]


def test_update_without_steps_keeps_existing_steps(user, sheet):
    created = _create(user, sheet, steps=_steps_payload(("A", "a"), ("B", "b"))).data

    response = _call(method="patch", user=user, pk=created["id"], data={"title": "改标题"})
    assert response.status_code == 200, response.data
    assert response.data["step_count"] == 2
    assert response.data["title"] == "改标题"


def test_zero_steps_rejected(user, sheet):
    response = _create(user, sheet, steps=[])
    assert response.status_code == 400
    assert "执行步骤" in str(response.data)


def test_empty_assertion_reports_step_index(user, sheet):
    response = _create(
        user,
        sheet,
        steps=_steps_payload(("启动 App", "进入主页"), ("点击开关", "")),
    )
    assert response.status_code == 400
    assert "第 2 步" in str(response.data)


def test_overlong_step_rejected(user, sheet):
    response = _create(
        user,
        sheet,
        steps=_steps_payload(("启动 App", "进入主页"), ("点击开关", "长" * 2001)),
    )
    assert response.status_code == 400
    assert "2000" in str(response.data)


def test_invalid_enum_rejected(user, sheet):
    response = _create(user, sheet, steps=_steps_payload(("A", "a")), system="WINDOWS")
    assert response.status_code == 400
    assert "ANDROID" in str(response.data)


def test_legacy_fields_are_ignored(user, sheet):
    response = _create(
        user,
        sheet,
        steps=_steps_payload(("A", "a")),
        test_type="app",
        expected_result="旧字段",
    )
    assert response.status_code == 201, response.data
    assert "test_type" not in response.data
    assert "expected_result" not in response.data


def test_failed_save_keeps_previous_steps(user, sheet):
    created = _create(user, sheet, steps=_steps_payload(("A", "a"), ("B", "b"))).data

    rejected = _call(
        method="patch",
        user=user,
        pk=created["id"],
        data={"steps": _steps_payload(("A", "a"), ("", "b"))},
    )
    assert rejected.status_code == 400
    persisted = case_api.get_definition(case_id=created["id"], user_id=str(user.id))
    assert [s["action"] for s in persisted["steps"]] == ["A", "B"]


def test_batch_delete_removes_cases_and_steps(user, sheet):
    project, case_file = sheet
    first = _create(user, sheet, steps=_steps_payload(("A", "a"))).data
    second = _create(user, sheet, steps=_steps_payload(("B", "b"))).data

    deleted = case_api.batch_delete_definitions(
        case_ids=[first["id"], second["id"]],
        user_id=str(user.id),
    )
    assert deleted["deleted"] >= 2
    assert not case_models.CaseStep.objects.filter(case_id__in=[first["id"], second["id"]]).exists()
    assert not case_models.TestDefinition.objects.filter(file_id=case_file["id"]).exists()


def test_file_sheet_does_not_scale_queries_with_rows(user, sheet):
    """200 行 × 5 步的文件，读取必须预取步骤，查询数不随行数线性增长。"""
    project, case_file = sheet
    cases = [
        case_models.TestDefinition(
            id=f"TC-TEST-{index:04d}",
            project_id=project["id"],
            file_id=case_file["id"],
            title=f"用例 {index}",
            priority="P1",
            system="ANDROID",
            case_type="AUTO",
            business_type="appliance",
            module="设备管理",
            sort_order=index,
            created_by=str(user.id),
            updated_by=str(user.id),
        )
        for index in range(200)
    ]
    case_models.TestDefinition.objects.bulk_create(cases)
    steps = [
        case_models.CaseStep(
            case_id=case.id,
            sort_order=step_index,
            action=f"动作 {step_index}",
            assertion=f"断言 {step_index}",
        )
        for case in cases
        for step_index in range(1, 6)
    ]
    case_models.CaseStep.objects.bulk_create(steps)

    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as captured:
        payload = case_api.get_file_sheet(file_id=case_file["id"], user_id=str(user.id))

    assert len(payload["rows"]) == 200
    assert payload["rows"][0]["step_count"] == 5
    # 固定上限：行数 × 步骤数若各查一次，这里会是 1200 级别
    assert len(captured.captured_queries) <= 10, len(captured.captured_queries)
