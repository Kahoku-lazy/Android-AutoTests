"""BUG 提取规则：任务终态 -> 分类、来源键与错误正文。"""

from __future__ import annotations

import json

from types import SimpleNamespace

import pytest

from backend.apps.bug_manager.extract import build_bug_drafts
from backend.models.constants import BugCategory, TaskKind, TaskStatus

pytestmark = [pytest.mark.unit]


def _task(**overrides):
    values = {
        "id": 143,
        "title": "H6810 全功能测试",
        "task_kind": TaskKind.DEVICE_CONTROL,
        "status": TaskStatus.FAILED,
        "agent_id": 7,
        "created_by": "3",
        "result": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _result(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def test_ui_failure_creates_one_ticket_per_failed_case():
    task = _task(
        result=_result(
            {
                "status": "fail",
                "reason": "用例「A」未完成；用例「B」未完成",
                "failed": ["A", "B"],
            }
        )
    )

    drafts = build_bug_drafts(task)

    assert [draft.category for draft in drafts] == [BugCategory.UI_AUTOMATION] * 2
    assert [draft.title for draft in drafts] == ["UI 自动化失败：A", "UI 自动化失败：B"]
    assert drafts[0].source_ref.startswith("case:")
    assert drafts[0].source_ref != drafts[1].source_ref
    assert "来源任务：#143" in drafts[0].detail
    assert "失败用例：A" in drafts[0].detail
    assert "同任务其他失败用例：B" in drafts[0].detail


def test_ui_failure_without_case_titles_falls_back_to_task_ticket():
    task = _task(
        result=_result(
            {
                "status": "fail",
                "reason": "设备连接超时",
                "failed": [],
            }
        )
    )

    drafts = build_bug_drafts(task)

    assert len(drafts) == 1
    assert drafts[0].source_ref == "task"
    assert drafts[0].title == "UI 自动化任务失败：H6810 全功能测试"
    assert "设备连接超时" in drafts[0].detail


def test_interrupted_task_creates_task_ticket():
    task = _task(status=TaskStatus.INTERRUPTED, result="执行中断：服务重启")

    drafts = build_bug_drafts(task)

    assert len(drafts) == 1
    assert drafts[0].title == "UI 自动化任务中断：H6810 全功能测试"
    assert "执行中断" in drafts[0].detail


def test_cancelled_task_creates_no_ticket():
    assert build_bug_drafts(_task(status=TaskStatus.CANCELLED)) == []


def test_completed_ui_task_creates_no_ticket():
    assert build_bug_drafts(_task(status=TaskStatus.COMPLETED)) == []


def test_case_authoring_failure_includes_verdict_and_module_message():
    task = _task(
        id=162,
        title="H717D 6.4 按键",
        task_kind=TaskKind.CASE_AUTHORING,
        result=_result(
            {
                "status": "fail",
                "passed": False,
                "summary": "测试用例验收未通过",
                "reason": "字段缺失",
                "verdicts": [{"passed": False, "message": "13 字段不完整"}],
                "modules": [
                    {"name": "按键", "passed": False, "message": "缺少前置条件"},
                    {"name": "灯光", "passed": True, "message": "通过"},
                ],
            }
        ),
    )

    drafts = build_bug_drafts(task)

    assert len(drafts) == 1
    assert drafts[0].category == BugCategory.CASE_AUTHORING
    assert drafts[0].source_ref == "task"
    assert drafts[0].title == "测试用例编写未通过：H717D 6.4 按键"
    assert "13 字段不完整" in drafts[0].detail
    assert "缺少前置条件" in drafts[0].detail
    assert "灯光" not in drafts[0].detail


def test_case_import_failure_creates_import_ticket():
    task = _task(
        id=173,
        title="H717D 家电",
        task_kind=TaskKind.CASE_AUTHORING,
        status=TaskStatus.COMPLETED,
        result=_result(
            {
                "status": "success",
                "passed": True,
                "summary": "测试用例已生成并通过验收",
                "case_import": {"status": "failed", "message": "数据库不可用"},
            }
        ),
    )

    drafts = build_bug_drafts(task)

    assert len(drafts) == 1
    assert drafts[0].source_ref == "import"
    assert drafts[0].title == "测试用例入库失败：H717D 家电"
    assert "数据库不可用" in drafts[0].detail


def test_case_import_skipped_creates_no_ticket():
    task = _task(
        task_kind=TaskKind.CASE_AUTHORING,
        status=TaskStatus.COMPLETED,
        result=_result(
            {
                "status": "success",
                "passed": True,
                "case_import": {"status": "skipped", "message": "验收未通过"},
            }
        ),
    )

    assert build_bug_drafts(task) == []


def test_duplicate_failed_titles_are_deduplicated():
    task = _task(result=_result({"status": "fail", "failed": ["A", "A"]}))

    assert len(build_bug_drafts(task)) == 1


def test_long_title_is_clamped():
    task = _task(
        id=1,
        title="标题" * 400,
        result=_result({"status": "fail", "failed": []}),
    )

    draft = build_bug_drafts(task)[0]

    assert len(draft.title) == 500


def test_plain_text_result_is_still_described():
    task = _task(result="执行异常: 设备掉线")

    drafts = build_bug_drafts(task)

    assert len(drafts) == 1
    assert "执行异常: 设备掉线" in drafts[0].detail
