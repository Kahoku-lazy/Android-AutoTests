"""YAML 与用例库互转契约：幂等导入、清理开关、导出往返与归属校验。"""

from __future__ import annotations

import pytest
import yaml

from django.contrib.auth import get_user_model

from backend.apps.case_manager import api as case_api
from backend.apps.case_manager.api_yaml import export_yaml_text, import_yaml_text

pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.case_manager]

YAML_TWO_CASES = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
      anchor:
        page: 首页
      log:
        sku: H6810
        port: 7005
        keywords: [switch_on]
- title: 乙
  steps:
    - action: 再点一下
      assert: 页面已切换
""".strip()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="yaml-owner", password="pass")


@pytest.fixture
def project(user):
    return case_api.create_project(name="H6810 用例库", user_id=str(user.id))


def _import(user, project, text, **kwargs):
    return import_yaml_text(
        project_id=project["id"],
        user_id=str(user.id),
        text=text,
        file_name=kwargs.pop("file_name", "H6810_structured_cases"),
        **kwargs,
    )


def test_first_import_creates_sheet_and_rows(user, project):
    result = _import(user, project, YAML_TWO_CASES)
    assert result["created"] == 2
    assert result["updated"] == 0
    assert result["file_name"] == "H6810_structured_cases"

    sheet = case_api.get_file_sheet(file_id=result["file_id"], user_id=str(user.id))
    assert [row["title"] for row in sheet["rows"]] == ["甲", "乙"]
    first_step = sheet["rows"][0]["steps"][0]
    assert first_step["anchor"] == {"page": "首页"}
    assert first_step["log"] == {"sku": "H6810", "port": 7005, "keywords": ["switch_on"]}


def test_reimport_is_idempotent(user, project):
    first = _import(user, project, YAML_TWO_CASES)
    second = _import(user, project, YAML_TWO_CASES)
    assert second["file_id"] == first["file_id"]
    assert second["created"] == 0
    assert second["updated"] == 2

    sheet = case_api.get_file_sheet(file_id=first["file_id"], user_id=str(user.id))
    assert len(sheet["rows"]) == 2


def test_missing_rows_kept_without_prune(user, project):
    first = _import(user, project, YAML_TWO_CASES)
    single = YAML_TWO_CASES.split("- title: 乙")[0].strip()
    result = _import(user, project, single)
    assert result["removed"] == 0

    sheet = case_api.get_file_sheet(file_id=first["file_id"], user_id=str(user.id))
    assert len(sheet["rows"]) == 2


def test_prune_removes_missing_rows(user, project):
    first = _import(user, project, YAML_TWO_CASES)
    single = YAML_TWO_CASES.split("- title: 乙")[0].strip()
    result = _import(user, project, single, prune=True)
    assert result["removed"] == 1

    sheet = case_api.get_file_sheet(file_id=first["file_id"], user_id=str(user.id))
    assert [row["title"] for row in sheet["rows"]] == ["甲"]


def test_export_round_trip_keeps_hints(user, project):
    result = _import(user, project, YAML_TWO_CASES)
    sheet = case_api.get_file_sheet(file_id=result["file_id"], user_id=str(user.id))
    ids = [row["id"] for row in sheet["rows"]]

    text = export_yaml_text(case_ids=ids, user_id=str(user.id))
    exported = yaml.safe_load(text)
    original = yaml.safe_load(YAML_TWO_CASES)

    assert [case["title"] for case in exported] == [case["title"] for case in original]
    assert exported[0]["steps"][0]["anchor"] == original[0]["steps"][0]["anchor"]
    assert exported[0]["steps"][0]["log"]["keywords"] == ["switch_on"]
    # 没有执行提示的步骤只留 action / assert
    assert set(exported[1]["steps"][0]) == {"action", "assert"}


def test_export_keeps_selection_order(user, project):
    result = _import(user, project, YAML_TWO_CASES)
    sheet = case_api.get_file_sheet(file_id=result["file_id"], user_id=str(user.id))
    ids = [row["id"] for row in sheet["rows"]]
    exported = yaml.safe_load(export_yaml_text(case_ids=list(reversed(ids)), user_id=str(user.id)))
    assert [case["title"] for case in exported] == ["乙", "甲"]


def test_export_rejects_other_users_case(user, project):
    result = _import(user, project, YAML_TWO_CASES)
    sheet = case_api.get_file_sheet(file_id=result["file_id"], user_id=str(user.id))
    case_id = sheet["rows"][0]["id"]

    other = get_user_model().objects.create_user(username="other", password="pass")
    with pytest.raises(LookupError):
        export_yaml_text(case_ids=[case_id], user_id=str(other.id))


def test_export_rejects_empty_selection(user):
    with pytest.raises(ValueError):
        export_yaml_text(case_ids=[], user_id=str(user.id))


def test_import_rejects_other_users_project(user):
    other = get_user_model().objects.create_user(username="intruder", password="pass")
    project = case_api.create_project(name="别人的项目", user_id=str(user.id))
    with pytest.raises(LookupError):
        import_yaml_text(
            project_id=project["id"],
            user_id=str(other.id),
            text=YAML_TWO_CASES,
            file_name="偷来的",
        )


def test_duplicate_titles_inside_one_yaml_are_skipped(user, project):
    text = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
- title: 甲
  steps:
    - action: 再点一下
      assert: 页面已切换
"""
    result = _import(user, project, text)
    assert result["created"] == 1
    assert result["skipped"] == [{"title": "甲", "reason": "同一份 YAML 内标题重复"}]
