"""项目表上限、YAML 追加、个人视图和里程碑编译。"""

from __future__ import annotations

import pytest

from backend.apps.case_manager import api as case_api
from backend.apps.case_manager.api_projects import ConflictError
from backend.apps.task_list.attachments import validate_milestone_yaml

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

_STEP = [{"action": "点电源", "assertion": "灯亮"}]


def _project(kind: str = "automation") -> int:
    return case_api.create_project(name=f"表-{kind}", library_kind=kind, user_id="7")["id"]


def test_thousandth_row_is_rejected(monkeypatch):
    project_id = _project("functional")
    monkeypatch.setattr("backend.apps.case_manager.api_rows._lock_count", lambda _project: 999)
    with pytest.raises(ConflictError, match="999"):
        case_api.create_row(project_id=project_id, user_id="7", title="超限", steps=_STEP)


def test_yaml_appends_three_rows():
    project_id = _project("functional")
    text = """
- title: 甲
  steps: [{action: a, assertion: b}]
- title: 乙
  steps: [{action: c, assertion: d}]
- title: 丙
  steps: [{action: e, assertion: f}]
"""
    result = case_api.import_yaml_text(project_id=project_id, user_id="7", text=text)
    assert result["imported"] == 3
    assert case_api.get_sheet(project_id=project_id, user_id="7")["project"]["case_count"] == 3


def test_yaml_rejects_missing_step_milestone_and_hints():
    project_id = _project("functional")
    samples = [
        "- title: 缺步骤\n  steps: []\n",
        "name: 里程碑\nsteps:\n  - subject: 打开\n    description: 停在首页\n",
        "- title: 带锚点\n  steps: [{action: a, assertion: b, anchor: {page: 首页}}]\n",
    ]
    for text in samples:
        with pytest.raises(ValueError):
            case_api.import_yaml_text(project_id=project_id, user_id="7", text=text)
    assert case_api.get_sheet(project_id=project_id, user_id="7")["project"]["case_count"] == 0


def test_import_over_limit_rejects_whole_file(monkeypatch):
    project_id = _project("functional")
    monkeypatch.setattr("backend.apps.case_manager.api_rows._lock_count", lambda _project: 990)
    text = "\n".join(f"- title: 行{i}\n  steps: [{{action: a, assertion: b}}]" for i in range(20))
    with pytest.raises(ConflictError, match="还可追加 9"):
        case_api.import_yaml_text(project_id=project_id, user_id="7", text=text)


def test_view_is_per_user_and_rejects_unknown_field():
    project_id = _project()
    saved = case_api.save_sheet_view(
        project_id=project_id,
        user_id="7",
        payload={"hidden_columns": ["module"], "filters": {"priority": "P0"}, "group_by": "module"},
    )
    assert case_api.get_sheet(project_id=project_id, user_id="7")["view"]["hidden_columns"] == [
        "module"
    ]
    assert case_api.get_sheet(project_id=project_id, user_id="8")["view"]["hidden_columns"] == []
    with pytest.raises(ValueError, match="未登记"):
        case_api.save_sheet_view(
            project_id=project_id,
            user_id="7",
            payload={"hidden_columns": ["secret"]},
        )
    assert saved["filters"]["priority"] == "P0"


def test_compile_keeps_order_and_rejects_functional_or_foreign():
    project_id = _project("automation")
    first = case_api.create_row(project_id=project_id, user_id="7", title="甲", steps=_STEP)
    second = case_api.create_row(
        project_id=project_id,
        user_id="7",
        title="乙",
        steps=[{"action": "滑动", "assertion": "列表动"}],
    )
    text = case_api.compile_automation_cases(case_ids=[second["id"], first["id"]], user_id="7")
    validate_milestone_yaml(text)
    assert text.index("乙") < text.index("甲")
    functional_id = _project("functional")
    foreign = case_api.create_row(project_id=functional_id, user_id="7", title="功能", steps=_STEP)
    with pytest.raises(LookupError, match="自动化"):
        case_api.compile_automation_cases(case_ids=[foreign["id"]], user_id="7")
    with pytest.raises(LookupError, match="无权限"):
        case_api.compile_automation_cases(case_ids=[first["id"]], user_id="8")
