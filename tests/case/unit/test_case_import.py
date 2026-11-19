"""验收用例追加到功能表：不建文件，超限整份拒绝。"""

from __future__ import annotations

import pytest

from backend.apps.case_manager import api_import
from backend.apps.case_manager.api import import_case_rows
from backend.apps.case_manager.models import (
    LIBRARY_FUNCTIONAL,
    CaseProject,
    FunctionalCase,
    FunctionalStep,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _rows() -> list[dict]:
    return [
        {
            "source_case_id": "TC-H717D-BTN-V1-001",
            "title": "待机开机",
            "priority": "P0",
            "module": "按键",
            "precondition": "设备待机<br>环境常规",
            "steps": [
                {"action": "单击 POWER", "assertion": "模式灯亮"},
                {"action": "等待 3s", "assertion": "3s 内进入待机模式"},
            ],
        },
        {
            "title": "运行中关机",
            "priority": "P1",
            "module": "按键",
            "steps": [{"action": "单击 POWER", "assertion": "所有灯熄灭"}],
        },
    ]


def _import(*, user_id: str = "7", task_id: int = 101, rows=None):
    return import_case_rows(
        user_id=user_id,
        task_id=task_id,
        task_title="H717D 用例",
        rows=_rows() if rows is None else rows,
    )


def test_import_appends_to_functional_project():
    result = _import()
    assert result["status"] == "imported"
    assert result["path"] == f"/cases/projects/{result['project_id']}"
    assert "file_id" not in result
    project = CaseProject.objects.get(id=result["project_id"])
    assert project.library_kind == LIBRARY_FUNCTIONAL
    assert project.name == api_import.PROJECT_NAME
    rows = FunctionalCase.objects.filter(project=project).order_by("sort_order")
    assert [row.title for row in rows] == ["待机开机", "运行中关机"]
    assert rows[0].precondition == "设备待机\n环境常规"
    assert list(FunctionalStep.objects.filter(case=rows[0]).values_list("action", flat=True)) == [
        "单击 POWER",
        "等待 3s",
    ]


def test_second_task_appends_same_project():
    first = _import(task_id=101)
    second = _import(task_id=102)
    assert second["project_id"] == first["project_id"]
    assert CaseProject.objects.count() == 1
    assert FunctionalCase.objects.filter(project_id=first["project_id"]).count() == 4


def test_same_task_is_idempotent():
    _import()
    again = _import()
    assert again["status"] == "imported"
    assert FunctionalCase.objects.filter(source_task_id="101").count() == 2


def test_over_limit_keeps_existing_rows(monkeypatch):
    project = CaseProject.objects.create(
        name=api_import.PROJECT_NAME, library_kind="functional", created_by="7"
    )
    first = _import(task_id=201)
    assert first["status"] == "imported"
    monkeypatch.setattr(api_import, "_project_row_count", lambda _project: 998)
    result = _import(task_id=202)
    assert result["status"] == "failed"
    assert "1" in result["message"]
    assert FunctionalCase.objects.filter(project=project).count() == 2


def test_import_failure_rolls_back(monkeypatch):
    def _boom(**_kwargs):
        raise RuntimeError("模拟写入失败")

    monkeypatch.setattr(api_import, "create_row", _boom)
    result = _import()
    assert result["status"] == "failed"
    assert CaseProject.objects.count() == 0
    assert FunctionalCase.objects.count() == 0
