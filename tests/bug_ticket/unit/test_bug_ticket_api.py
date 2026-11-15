"""BUG 单登记、幂等、可见性与任务终态接入。"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.bug_manager import api as bug_api
from backend.apps.bug_manager.models import BugTicket
from backend.apps.task_list import api as task_api
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind, TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _agent(owner, *, name="Agent-01", kind=TaskKind.DEVICE_CONTROL):
    return AIAgent.objects.create(owner=owner, name=name, task_kind=kind)


def _task(agent, *, status=TaskStatus.FAILED, title="H6810 全功能测试", failed=None):
    payload = {
        "status": "fail" if status == TaskStatus.FAILED else status,
        "reason": "设备掉线",
        "failed": failed if failed is not None else ["图片页", "涂鸦页"],
    }
    return Task.objects.create(
        agent=agent,
        title=title,
        task_kind=agent.task_kind,
        status=status,
        result=json.dumps(payload, ensure_ascii=False),
    )


def test_record_task_bugs_creates_one_ticket_per_failed_case():
    owner = get_user_model().objects.create_user(username="bug-owner", password="x")
    task = _task(_agent(owner))

    counts = bug_api.record_task_bugs(task)

    assert counts == {"created": 2, "updated": 0, "skipped": 0}
    rows = list(BugTicket.objects.filter(task_id=task.id).order_by("title"))
    assert len(rows) == 2
    assert {row.category for row in rows} == {"ui_automation"}
    assert all(row.task_id == task.id for row in rows)


def test_record_task_bugs_is_idempotent_and_preserves_status():
    owner = get_user_model().objects.create_user(username="bug-owner-2", password="x")
    task = _task(_agent(owner))
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.filter(task_id=task.id).first()
    ticket.status = BugTicket.STATUS_RESOLVED
    ticket.save(update_fields=["status"])

    counts = bug_api.record_task_bugs(task)

    assert counts["created"] == 0
    assert counts["updated"] == 2
    ticket.refresh_from_db()
    assert ticket.status == BugTicket.STATUS_RESOLVED
    assert BugTicket.objects.filter(task_id=task.id).count() == 2


def test_update_status_sets_and_clears_resolved_at():
    owner = get_user_model().objects.create_user(username="bug-owner-3", password="x")
    task = _task(_agent(owner), failed=[])
    bug_api.record_task_bugs(task)
    ticket = BugTicket.objects.get(task_id=task.id)

    resolved = bug_api.update_bug_status(str(owner.id), ticket.id, "resolved")
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"]

    reopened = bug_api.update_bug_status(str(owner.id), ticket.id, "open")
    assert reopened["status"] == "open"
    assert reopened["resolved_at"] == ""


def test_list_bugs_filters_category_status_and_keyword():
    owner = get_user_model().objects.create_user(username="bug-owner-4", password="x")
    ui_task = _task(_agent(owner), failed=["图片页"])
    case_agent = _agent(owner, name="Agent-02", kind=TaskKind.CASE_AUTHORING)
    case_task = Task.objects.create(
        agent=case_agent,
        title="H717D 按键",
        task_kind=TaskKind.CASE_AUTHORING,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {
                "status": "fail",
                "passed": False,
                "summary": "验收未通过",
                "reason": "字段缺失",
            },
            ensure_ascii=False,
        ),
    )
    bug_api.record_task_bugs(ui_task)
    bug_api.record_task_bugs(case_task)

    payload = bug_api.list_bugs(str(owner.id), category="case_authoring")

    assert payload["summary"]["total"] == 2
    assert payload["summary"]["ui_automation"] == 1
    assert payload["summary"]["case_authoring"] == 1
    assert payload["total"] == 1
    assert payload["items"][0]["task_id"] == case_task.id

    found = bug_api.list_bugs(str(owner.id), keyword=str(case_task.id))
    assert found["total"] == 1

    numeric_bug = bug_api.list_bugs(str(owner.id), keyword=payload["items"][0]["bug_no"])
    assert numeric_bug["total"] == 1


def test_bug_visibility_is_scoped_by_agent_owner():
    owner_a = get_user_model().objects.create_user(username="bug-owner-a", password="x")
    owner_b = get_user_model().objects.create_user(username="bug-owner-b", password="x")
    task_a = _task(_agent(owner_a, name="A"), failed=[])
    task_b = _task(_agent(owner_b, name="B"), failed=[])
    bug_api.record_task_bugs(task_a)
    bug_api.record_task_bugs(task_b)

    payload_a = bug_api.list_bugs(str(owner_a.id))

    assert payload_a["summary"]["total"] == 1
    assert payload_a["items"][0]["task_id"] == task_a.id
    assert bug_api.get_bug(str(owner_a.id), BugTicket.objects.get(task_id=task_b.id).id) is None


def test_sync_visible_tasks_backfills_idempotently():
    owner = get_user_model().objects.create_user(
        username="bug-sync", password="x", is_superuser=True, is_staff=True
    )
    task = _task(_agent(owner))

    first = bug_api.sync_visible_tasks(str(owner.id))
    second = bug_api.sync_visible_tasks(str(owner.id))

    assert first["created"] == 2
    assert second["created"] == 0
    assert BugTicket.objects.filter(task_id=task.id).count() == 2


def test_finalize_task_records_bug_and_ignores_registration_failure(monkeypatch):
    owner = get_user_model().objects.create_user(username="bug-finalize", password="x")
    agent = _agent(owner)
    task = task_api.create_task(agent, title="执行失败", goal="")

    task_api.finalize_task(
        task,
        status=TaskStatus.FAILED,
        result=json.dumps(
            {"status": "fail", "reason": "设备掉线", "failed": []},
            ensure_ascii=False,
        ),
    )

    assert BugTicket.objects.filter(task_id=task.id).count() == 1

    def _boom(_task):
        raise RuntimeError("台账不可用")

    monkeypatch.setattr("backend.apps.bug_manager.api.record_task_bugs", _boom)
    task2 = task_api.create_task(agent, title="执行失败 2", goal="")
    task_api.finalize_task(task2, status=TaskStatus.FAILED, result="执行异常: 设备掉线")

    task2.refresh_from_db()
    assert task2.status == TaskStatus.FAILED


def test_finalize_completed_case_task_records_import_failure():
    owner = get_user_model().objects.create_user(username="bug-import", password="x")
    agent = _agent(owner, name="Agent-02", kind=TaskKind.CASE_AUTHORING)
    task = task_api.create_task(
        agent,
        title="H717D 用例",
        goal="",
        task_kind=TaskKind.CASE_AUTHORING,
    )

    task_api.finalize_task(
        task,
        status=TaskStatus.COMPLETED,
        result=json.dumps(
            {
                "status": "success",
                "passed": True,
                "summary": "测试用例已生成并通过验收",
                "case_import": {"status": "failed", "message": "数据库不可用"},
            },
            ensure_ascii=False,
        ),
    )

    ticket = BugTicket.objects.get(task_id=task.id)
    assert ticket.category == "case_authoring"
    assert "数据库不可用" in ticket.detail
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_deleting_task_keeps_bug_ticket_audit_record():
    owner = get_user_model().objects.create_user(username="bug-delete", password="x")
    task = _task(_agent(owner), failed=[])
    bug_api.record_task_bugs(task)
    task_id = task.id

    task.delete()

    assert BugTicket.objects.filter(task_id=task_id).exists()


def test_recover_orphaned_tasks_records_interrupted_bug():
    owner = get_user_model().objects.create_user(username="bug-recover", password="x")
    task = Task.objects.create(
        agent=_agent(owner),
        title="重启中断",
        task_kind=TaskKind.DEVICE_CONTROL,
        status=TaskStatus.RUNNING,
    )

    task_api.recover_orphaned_tasks()

    task.refresh_from_db()
    ticket = BugTicket.objects.get(task_id=task.id)
    assert task.status == TaskStatus.INTERRUPTED
    assert ticket.category == "ui_automation"
    assert "服务重启" in ticket.detail
