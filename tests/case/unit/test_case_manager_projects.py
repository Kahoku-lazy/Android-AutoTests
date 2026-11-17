"""项目表：创建锁定库类型，拒绝目录和文件入口。"""

from __future__ import annotations

import pytest

from backend.apps.case_manager import api as case_api
from backend.apps.case_manager.api_projects import ConflictError

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

_STEP = [{"action": "点电源", "assertion": "灯亮"}]


def test_create_project_locks_library_kind():
    data = case_api.create_project(name="家电冒烟", library_kind="automation", user_id="42")
    assert data["library_kind"] == "automation"
    assert data["case_count"] == 0
    with pytest.raises(ConflictError, match="不可修改"):
        case_api.update_project(project_id=data["id"], user_id="42", library_kind="functional")


def test_directory_and_file_apis_are_gone():
    assert not hasattr(case_api, "create_directory")
    assert not hasattr(case_api, "create_file")
    assert not hasattr(case_api, "get_project_tree")


def test_user_isolation():
    project_id = case_api.create_project(name="仅自己", library_kind="functional", user_id="42")["id"]
    assert case_api.get_project(project_id=project_id, user_id="99") is None
    with pytest.raises(LookupError):
        case_api.create_row(
            project_id=project_id,
            user_id="99",
            title="越权",
            steps=[{"action": "点", "assertion": "亮"}],
        )


def test_sheet_row_belongs_to_project():
    project_id = case_api.create_project(name="表", library_kind="functional", user_id="42")["id"]
    row = case_api.create_row(project_id=project_id, user_id="42", title="开机", steps=_STEP)
    sheet = case_api.get_sheet(project_id=project_id, user_id="42")
    assert row["id"].startswith("TC-")
    assert "case_type" not in row
    assert sheet["rows"][0]["title"] == "开机"
    assert sheet["project"]["case_count"] == 1
