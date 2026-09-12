"""Unit tests for project / directory / file / document case api layer."""

from __future__ import annotations

import pytest

from apps.case_manager import api as case_api
from apps.case_manager.api_projects import ConflictError

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_create_project_and_empty_tree():
    data = case_api.create_project(name="家电冒烟", description="d", user_id="42")
    assert data["name"] == "家电冒烟"
    tree = case_api.get_project_tree(project_id=data["id"], user_id="42")
    assert tree["tree"] == []


def test_directory_file_move_and_cycle_forbidden():
    p = case_api.create_project(name="P", user_id="42")["id"]
    d1 = case_api.create_directory(project_id=p, name="根目录", user_id="42")["id"]
    d2 = case_api.create_directory(project_id=p, name="子目录", user_id="42", parent_id=d1)[
        "id"
    ]
    with pytest.raises(ConflictError):
        case_api.move_item(
            user_id="42",
            item_type="directory",
            item_id=d1,
            target_directory_id=d2,
        )
    file_data = case_api.create_file(
        project_id=p, name="冒烟表", user_id="42", directory_id=d1
    )
    case = case_api.create_definition(
        project_id=p, file_id=file_data["id"], user_id="42", title="用例A"
    )
    assert case["id"].startswith("TC-")
    assert case["file_id"] == file_data["id"]
    moved = case_api.move_item(
        user_id="42",
        item_type="file",
        item_id=file_data["id"],
        target_directory_id=d2,
    )
    assert moved["directory_id"] == d2
    sheet = case_api.get_file_sheet(file_id=file_data["id"], user_id="42")
    assert len(sheet["rows"]) == 1
    assert sheet["rows"][0]["directory_id"] == d2


def test_user_isolation():
    p = case_api.create_project(name="仅自己", user_id="42")["id"]
    assert case_api.get_project(project_id=p, user_id="99") is None
    with pytest.raises(LookupError):
        case_api.get_project_tree(project_id=p, user_id="99")


def test_update_requires_steps_and_expected():
    p = case_api.create_project(name="表单", user_id="42")["id"]
    f = case_api.create_file(project_id=p, name="表", user_id="42")["id"]
    case = case_api.create_definition(project_id=p, file_id=f, user_id="42")
    with pytest.raises(ValueError, match="执行步骤"):
        case_api.update_definition(
            case_id=case["id"],
            user_id="42",
            title="有标题",
            steps="",
            expected_result="",
        )


def test_tree_lists_files_not_cases():
    p = case_api.create_project(name="树", user_id="42")["id"]
    f = case_api.create_file(project_id=p, name="文件1", user_id="42")["id"]
    case_api.create_definition(project_id=p, file_id=f, user_id="42", title="行1")
    tree = case_api.get_project_tree(project_id=p, user_id="42")
    assert len(tree["tree"]) == 1
    assert tree["tree"][0]["type"] == "file"
    assert tree["tree"][0]["name"] == "文件1"
