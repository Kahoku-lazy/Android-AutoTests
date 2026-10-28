"""Agent-02 用例行写入用例库：映射、归属、幂等与失败回滚。"""

from __future__ import annotations

import pytest

from backend.apps.case_manager import api_import
from backend.apps.case_manager.api import import_case_rows
from backend.apps.case_manager.models import CaseFile, CaseProject, CaseStep
from backend.apps.case_manager.models import TestDefinition as Definition

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
            "source_case_id": "TC-H717D-BTN-V1-002",
            "title": "运行中关机",
            "priority": "P1",
            "module": "按键",
            "precondition": "设备运行",
            "steps": [{"action": "单击 POWER", "assertion": "所有灯熄灭"}],
        },
    ]


def _import(*, user_id: str = "7", task_id: int = 101, rows=None, title="H717D 用例"):
    return import_case_rows(
        user_id=user_id,
        task_id=task_id,
        task_title=title,
        rows=_rows() if rows is None else rows,
    )


def test_import_creates_project_file_and_cases():
    result = _import()

    assert result["status"] == "imported"
    assert result["case_count"] == 2
    assert result["path"] == f"/cases/projects/{result['project_id']}/files/{result['file_id']}"
    project = CaseProject.objects.get(id=result["project_id"])
    case_file = CaseFile.objects.get(id=result["file_id"])
    assert project.name == api_import.PROJECT_NAME
    assert project.created_by == "7"
    assert case_file.name == "H717D 用例（任务 101）"
    assert case_file.created_by == "7"
    rows = Definition.objects.filter(file=case_file).order_by("sort_order")
    assert [row.title for row in rows] == ["待机开机", "运行中关机"]
    assert rows[0].priority == "P0"
    assert rows[0].module == "按键"
    assert rows[0].precondition == "设备待机\n环境常规"
    assert rows[0].source_case_id == "TC-H717D-BTN-V1-001"
    assert rows[0].source_task_id == "101"
    assert rows[0].system == "ANDROID"
    assert rows[0].case_type == "FUNC"
    assert rows[0].business_type == "appliance"
    assert list(CaseStep.objects.filter(case=rows[0]).values_list("action", flat=True)) == [
        "单击 POWER",
        "等待 3s",
    ]


def test_import_is_idempotent_per_task():
    first = _import()
    second = _import()

    assert second["file_id"] == first["file_id"]
    assert second["case_count"] == 2
    assert Definition.objects.filter(source_task_id="101").count() == 2


def test_second_task_reuses_project_but_creates_new_file():
    first = _import(task_id=101)
    second = _import(task_id=102)

    assert second["project_id"] == first["project_id"]
    assert second["file_id"] != first["file_id"]
    assert CaseProject.objects.count() == 1
    assert CaseFile.objects.count() == 2


def test_invalid_rows_are_skipped_without_failing_batch():
    rows = _rows()
    rows[1]["title"] = ""
    result = _import(rows=rows)

    assert result["status"] == "imported"
    assert result["case_count"] == 1
    assert result["skipped_count"] == 1
    assert result["skipped"][0]["reason"] == "测试标题为空"


def test_all_invalid_rows_return_skipped_without_creating_file():
    result = _import(rows=[{"title": "", "steps": []}])

    assert result["status"] == "skipped"
    assert result["path"] == ""
    assert CaseProject.objects.count() == 0
    assert CaseFile.objects.count() == 0


def test_import_failure_rolls_back_project_file_and_cases(monkeypatch):
    def _boom(**_kwargs):
        raise RuntimeError("模拟写入失败")

    monkeypatch.setattr(api_import, "create_definition", _boom)
    result = _import(task_id=103)

    assert result["status"] == "failed"
    assert "模拟写入失败" in result["message"]
    assert CaseProject.objects.count() == 0
    assert CaseFile.objects.count() == 0
    assert Definition.objects.count() == 0
