"""BUG 单登记、幂等与任务终态接入。"""

from __future__ import annotations

import json

import pytest

from backend.apps.bug_manager import api as bug_api
from backend.apps.bug_manager.models import BugTicket
from backend.apps.task_list import api as task_api
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind, TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _task(
    *, status=TaskStatus.FAILED, title="H6810 全功能测试", failed=None, kind=TaskKind.DEVICE_CONTROL
):
    payload = {
        "status": "fail" if status == TaskStatus.FAILED else status,
        "reason": "设备掉线",
        "failed": failed if failed is not None else ["图片页", "涂鸦页"],
    }
    return Task.objects.create(
        title=title,
        task_kind=kind,
        status=status,
        result=json.dumps(payload, ensure_ascii=False),
    )


def test_record_task_bugs_creates_one_ticket_per_failed_case():
    task = _task()

    counts = bug_api.record_task_bugs(task)

    assert counts == {"created": 2, "updated": 0, "skipped": 0}
    rows = list(BugTicket.objects.filter(task_id=task.id).order_by("title"))
    assert len(rows) == 2
    assert {row.category for row in rows} == {"ui_automation"}
    assert all(row.failure is None for row in rows)


def test_workflow_snapshot_is_one_ticket_and_preserves_status():
    task = Task.objects.create(
        title="工作流",
        task_kind=TaskKind.ASSISTANT_SOP,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {
                "failure_kind": "verdict",
                "reason": "回到桌面：没看到 dock",
                "failed_steps": [
                    {
                        "seq": 1,
                        "name": "回到桌面",
                        "expected": "能看见 dock",
                        "actual": "没看到 dock",
                        "attempts": 3,
                        "kind": "verdict",
                    }
                ],
            },
            ensure_ascii=False,
        ),
    )
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.get(task_id=task.id)
    ticket.status = BugTicket.STATUS_RESOLVED
    ticket.save(update_fields=["status"])

    counts = bug_api.record_task_bugs(task)

    assert counts == {"created": 0, "updated": 1, "skipped": 0}
    ticket.refresh_from_db()
    assert ticket.status == BugTicket.STATUS_RESOLVED
    assert ticket.source_ref == "task"
    assert ticket.failure["steps"][0]["expected"] == "能看见 dock"
    assert ticket.case_label == ""
    assert BugTicket.objects.filter(task_id=task.id).count() == 1


def test_record_copies_case_identity_and_empty_rerun_does_not_erase_it():
    task = Task.objects.create(
        title="工作流",
        task_kind=TaskKind.ASSISTANT_SOP,
        status=TaskStatus.FAILED,
        case_identity={
            "source": "platform",
            "rows": [
                {"project": "灯", "id": "1", "title": "定时"},
                {"project": "灯", "id": "2", "title": "场景"},
            ],
        },
        result=json.dumps(
            {"failed_steps": [{"seq": 1, "name": "定时 · 第 1 步", "kind": "verdict"}]},
            ensure_ascii=False,
        ),
    )
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.get(task_id=task.id)
    assert ticket.title.startswith("步骤未通过")
    assert ticket.case_label == "定时 · 共 2 条"
    assert ticket.case_rows[1]["title"] == "场景"
    ticket.status = BugTicket.STATUS_RESOLVED
    ticket.save(update_fields=["status"])

    task.case_identity = {}
    task.save(update_fields=["case_identity"])
    bug_api.record_task_bugs(task)
    ticket.refresh_from_db()
    assert ticket.case_label == "定时 · 共 2 条"
    assert ticket.status == BugTicket.STATUS_RESOLVED
    assert BugTicket.objects.filter(task_id=task.id).count() == 1


def test_keyword_matches_case_label_when_title_does_not():
    task = Task.objects.create(
        title="工作流",
        task_kind=TaskKind.ASSISTANT_SOP,
        status=TaskStatus.FAILED,
        case_identity={
            "source": "platform",
            "rows": [{"project": "灯", "id": "1", "title": "独有用例"}],
        },
        result=json.dumps(
            {"failed_steps": [{"seq": 1, "name": "模型拒绝", "kind": "provider"}]},
            ensure_ascii=False,
        ),
    )
    bug_api.record_task_bugs(task)
    found = bug_api.list_bugs("1", keyword="独有用例")
    assert found["total"] == 1


def test_update_status_sets_and_clears_resolved_at():
    task = _task(failed=[])
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.get(task_id=task.id)

    resolved = bug_api.update_bug_status("1", ticket.id, "resolved")
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"]

    reopened = bug_api.update_bug_status("1", ticket.id, "open")
    assert reopened["status"] == "open"
    assert reopened["resolved_at"] == ""


def test_list_bugs_filters_category_and_keyword():
    ui_task = _task(failed=["图片页"])
    case_task = Task.objects.create(
        title="H717D 按键",
        task_kind=TaskKind.CASE_AUTHORING,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {"status": "fail", "passed": False, "summary": "验收未通过", "reason": "字段缺失"},
            ensure_ascii=False,
        ),
    )
    bug_api.record_task_bugs(ui_task)
    bug_api.record_task_bugs(case_task)

    payload = bug_api.list_bugs("1", category="case_authoring")

    assert payload["summary"]["total"] == 2
    assert payload["total"] == 1
    assert payload["items"][0]["task_id"] == case_task.id
    assert payload["items"][0]["failure_steps"] == []

    found = bug_api.list_bugs("1", keyword=str(case_task.id))
    assert found["total"] == 1


def test_sync_visible_tasks_backfills_idempotently():
    task = _task()

    first = bug_api.sync_visible_tasks("1")
    second = bug_api.sync_visible_tasks("1")

    assert first["created"] == 2
    assert second["created"] == 0
    assert BugTicket.objects.filter(task_id=task.id).count() == 2


def test_finalize_task_records_bug_and_ignores_registration_failure(monkeypatch):
    task = task_api.create_task(title="执行失败", goal="")
    task.status = TaskStatus.RUNNING
    task.save(update_fields=["status"])

    task_api.finalize_task(
        task,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {"status": "fail", "reason": "设备掉线", "failed": []}, ensure_ascii=False
        ),
    )

    assert BugTicket.objects.filter(task_id=task.id).count() == 1

    def _boom(_task):
        raise RuntimeError("台账不可用")

    monkeypatch.setattr("backend.apps.bug_manager.api.record_task_bugs", _boom)
    task2 = task_api.create_task(title="执行失败 2", goal="")
    task2.status = TaskStatus.RUNNING
    task2.save(update_fields=["status"])
    task_api.finalize_task(task2, status=TaskStatus.FAILED, result="执行异常: 设备掉线")

    task2.refresh_from_db()
    assert task2.status == TaskStatus.FAILED


def test_deleting_task_keeps_bug_ticket_audit_record():
    task = _task(failed=[])
    bug_api.record_task_bugs(task)
    task_id = task.id

    task.delete()

    assert BugTicket.objects.filter(task_id=task_id).exists()
