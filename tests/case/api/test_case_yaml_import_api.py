"""用例库 YAML 导入接口契约：上传导入、结构非法不落库、越权拒绝。

用请求工厂直调导入视图（与 ``test_case_definitions_api.py`` 同款），不依赖
运行中的服务与 JWT 中间件；写库仍走 ``apps.case_manager.api``。
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.case_manager import api as case_api
from backend.apps.case_manager import views_drf as case_views
from backend.apps.case_manager.models import TestDefinition as CaseDefinition

pytestmark = [pytest.mark.django_db, pytest.mark.api, pytest.mark.case_manager]

URL = "/api/cases/import-yaml/"

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
def user(db):
    return get_user_model().objects.create_user(username="api-yaml-owner", password="pass")


@pytest.fixture
def project(user):
    return case_api.create_project(name="H6810 用例库", user_id=str(user.id))


def _upload(user, *, project_id, body: str = YAML_TEXT, name: str = "H6810.yaml", **extra):
    payload: dict = {
        "file": SimpleUploadedFile(name, body.encode("utf-8"), content_type="text/yaml"),
        **extra,
    }
    if project_id is not None:
        payload["project_id"] = project_id
    factory = APIRequestFactory()
    request = factory.post(URL, payload, format="multipart")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return case_views.import_yaml(request)


def test_upload_imports_cases(user, project):
    response = _upload(user, project_id=project["id"])
    assert response.status_code == 200, response.data
    assert response.data["created"] == 2
    assert response.data["file_name"] == "H6810"
    assert CaseDefinition.objects.filter(file_id=response.data["file_id"]).count() == 2


def test_upload_reuses_sheet_by_file_name(user, project):
    first = _upload(user, project_id=project["id"]).data
    second = _upload(user, project_id=project["id"]).data
    assert second["file_id"] == first["file_id"]
    assert second["created"] == 0
    assert second["updated"] == 2


def test_invalid_structure_returns_reason_and_writes_nothing(user, project):
    response = _upload(user, project_id=project["id"], body="- title: 甲\n")
    assert response.status_code == 400
    assert "steps" in str(response.data)
    assert CaseDefinition.objects.count() == 0


def test_rejects_non_yaml_file(user, project):
    response = _upload(user, project_id=project["id"], name="cases.txt")
    assert response.status_code == 400
    assert "YAML" in str(response.data)


def test_requires_project_id(user):
    response = _upload(user, project_id=None)
    assert response.status_code == 400
    assert "项目" in str(response.data)


def test_other_users_project_is_not_found(user):
    other = get_user_model().objects.create_user(username="not-owner", password="pass")
    project = case_api.create_project(name="别人的项目", user_id=str(user.id))
    response = _upload(other, project_id=project["id"])
    assert response.status_code == 404
    assert CaseDefinition.objects.count() == 0


def test_business_type_is_taken_from_request(user, project):
    response = _upload(user, project_id=project["id"], business_type="lighting")
    assert response.status_code == 200, response.data
    rows = CaseDefinition.objects.filter(file_id=response.data["file_id"])
    assert {row.business_type for row in rows} == {"lighting"}


def test_invalid_business_type_rejected(user, project):
    response = _upload(user, project_id=project["id"], business_type="furniture")
    assert response.status_code == 400
    assert "业务类型" in str(response.data)
    assert CaseDefinition.objects.count() == 0
