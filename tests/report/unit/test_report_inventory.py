"""报告台账聚合：两来源入列口径、身份字段、过滤、限量与报告数量统计。"""

from __future__ import annotations

import json

from datetime import timedelta

import pytest

from django.utils import timezone

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage, AIAssistantThread
from backend.apps.report_generator.report_inventory import (
    assemble_inventory,
    build_report_inventory,
)
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind, TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

_RUN = "20261118_102159"
_NAME = "20261118_102159_sop_bound.html"


def _locator_payload() -> str:
    return json.dumps(
        {"status": "success", "report_run": _RUN, "report_name": _NAME},
        ensure_ascii=False,
    )


def _sop_task(
    *,
    status=TaskStatus.COMPLETED,
    locator=True,
    identity=None,
    title="H6810 全功能测试",
    moment=None,
):
    moment = moment or timezone.now()
    return Task.objects.create(
        title=title,
        task_kind=TaskKind.ASSISTANT_SOP,
        status=status,
        result=_locator_payload() if locator else json.dumps({"status": "fail"}),
        case_identity=identity if identity is not None else {},
        started_at=moment - timedelta(minutes=3),
        finished_at=moment if status in (TaskStatus.COMPLETED, TaskStatus.FAILED) else None,
        created_at=moment - timedelta(minutes=5),
    )


def _assistant(assistant_id="20261116_8PD", name="涂鸦小助手"):
    return AIAssistant.objects.create(
        assistant_id=assistant_id,
        display_name=name,
        marker="#7C6F83",
        role_id="R0000000001",
    )


def _thread(assistant_id="20261116_8PD", thread_id="53c17538d163aeb4"):
    return AIAssistantThread.objects.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        status=AIAssistantThread.STATUS_DONE,
    )


def _turn(thread, *, report_id="20261116_180702", content="已完成回到桌面", role="assistant"):
    return AIAssistantMessage.objects.create(
        thread=thread, role=role, content=content, report_id=report_id
    )


# ── 入列口径：仅已完成的报告 ──


def test_completed_and_failed_sop_tasks_enter_inventory():
    done = _sop_task(status=TaskStatus.COMPLETED)
    failed = _sop_task(status=TaskStatus.FAILED, title="失败任务")

    payload = build_report_inventory("1")

    by_task = {item["task_id"]: item for item in payload["items"]}
    assert set(by_task) == {done.id, failed.id}
    row = by_task[done.id]
    assert row["source"] == "sop"
    assert row["report_run"] == _RUN
    assert row["report_name"] == _NAME
    assert row["status"] == "completed"
    assert row["duration"] == "3m00s"


@pytest.mark.parametrize(
    "status",
    [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.INTERRUPTED],
)
def test_non_terminal_tasks_never_enter_inventory(status):
    _sop_task(status=status)

    payload = build_report_inventory("1")

    assert payload["items"] == []
    assert payload["summary"]["total_reports"] == 0


def test_terminal_task_without_locator_is_not_a_report():
    _sop_task(locator=False)

    assert build_report_inventory("1")["items"] == []


def test_done_assistant_turn_enters_inventory_with_identity():
    _assistant()
    thread = _thread()
    _turn(thread)

    payload = build_report_inventory("1")

    assert len(payload["items"]) == 1
    row = payload["items"][0]
    assert row["source"] == "agent"
    assert row["assistant_id"] == "20261116_8PD"
    assert row["assistant_name"] == "涂鸦小助手"
    assert row["thread_id"] == "53c17538d163aeb4"
    assert row["report_id"] == "20261116_180702"
    assert row["summary"] == "已完成回到桌面"


def test_running_turn_and_user_messages_do_not_enter_inventory():
    _assistant()
    thread = _thread()
    thread.status = AIAssistantThread.STATUS_RUNNING
    thread.save(update_fields=["status"])
    _turn(thread, report_id="")  # 进行中的一轮没有登记
    _turn(thread, report_id="20261116_180703", role="user")

    assert build_report_inventory("1")["items"] == []


def test_deleted_assistant_card_falls_back_to_empty_name():
    card = _assistant()
    thread = _thread()
    _turn(thread)
    card.delete()

    payload = build_report_inventory("1")

    assert len(payload["items"]) == 1
    row = payload["items"][0]
    assert row["assistant_id"] == "20261116_8PD"
    assert row["assistant_name"] == ""


# ── 用例身份口径 ──


def test_case_identity_single_row_shows_title():
    _sop_task(
        identity={"source": "platform", "rows": [{"project": "灯", "id": "1", "title": "定时"}]}
    )

    row = build_report_inventory("1")["items"][0]

    assert row["case_label"] == "定时"


def test_case_identity_multiple_rows_shows_first_and_count():
    _sop_task(
        identity={
            "source": "platform",
            "rows": [
                {"project": "灯", "id": "1", "title": "定时"},
                {"project": "灯", "id": "2", "title": "场景"},
            ],
        }
    )

    row = build_report_inventory("1")["items"][0]

    assert row["case_label"] == "定时 · 共 2 条"


def test_case_identity_milestone_and_empty():
    _sop_task(identity={"source": "milestone"})
    _sop_task(identity={}, title="旧任务")

    labels = {
        item["task_title"]: item["case_label"] for item in build_report_inventory("1")["items"]
    }

    assert labels["H6810 全功能测试"] == "里程碑"
    assert labels["旧任务"] == ""


# ── 统计、过滤与排序 ──


def test_summary_counts_reports_not_tasks():
    for index in range(3):
        _sop_task(title=f"任务{index}")
    _assistant()
    thread = _thread()
    _turn(thread, report_id="20261116_180702")
    _turn(thread, report_id="20261116_181947")
    _sop_task(status=TaskStatus.RUNNING, title="执行中")

    payload = build_report_inventory("1")

    assert payload["summary"] == {"total_reports": 5, "sop_reports": 3, "agent_reports": 2}
    assert payload["total"] == 5


def test_source_filter_and_counts():
    _sop_task()
    _assistant()
    _turn(_thread())

    sop_only = build_report_inventory("1", source="sop")
    agent_only = build_report_inventory("1", source="agent")

    assert [item["source"] for item in sop_only["items"]] == ["sop"]
    assert [item["source"] for item in agent_only["items"]] == ["agent"]
    assert sop_only["summary"]["total_reports"] == 1
    assert agent_only["summary"]["total_reports"] == 1


def test_keyword_matches_task_id_and_assistant_identity():
    task = _sop_task(title="全功能测试")
    _assistant(name="涂鸦小助手")
    _turn(_thread())

    by_id = build_report_inventory("1", keyword=str(task.id))
    by_name = build_report_inventory("1", keyword="涂鸦")
    by_code = build_report_inventory("1", keyword="20261116_8pd")

    assert [item["task_id"] for item in by_id["items"]] == [task.id]
    assert [item["source"] for item in by_name["items"]] == ["agent"]
    assert [item["source"] for item in by_code["items"]] == ["agent"]


def test_items_ordered_by_generation_time_desc():
    now = timezone.now()
    _sop_task(title="早", moment=now - timedelta(hours=2))
    _sop_task(title="晚", moment=now)

    titles = [item["task_title"] for item in build_report_inventory("1")["items"]]

    assert titles == ["晚", "早"]


def test_date_range_filters_by_generation_day():
    now = timezone.now()
    _sop_task(title="今天", moment=now)
    _sop_task(title="十天前", moment=now - timedelta(days=10))

    today = now.date().isoformat()
    payload = build_report_inventory("1", start_date=today, end_date=today)

    assert [item["task_title"] for item in payload["items"]] == ["今天"]


def test_missing_or_invalid_user_gets_empty_payload():
    _sop_task()

    for user_id in (None, "", "abc"):
        payload = build_report_inventory(user_id)
        assert payload == {
            "summary": {"total_reports": 0, "sop_reports": 0, "agent_reports": 0},
            "total": 0,
            "items": [],
        }


# ── 限量（platform-load-budget 口径）──


def test_scan_limit_caps_each_source_at_1000():
    now = timezone.now()
    Task.objects.bulk_create(
        [
            Task(
                title=f"任务{index}",
                task_kind=TaskKind.ASSISTANT_SOP,
                status=TaskStatus.COMPLETED,
                result=_locator_payload(),
                finished_at=now - timedelta(seconds=index),
                created_at=now - timedelta(seconds=index + 60),
            )
            for index in range(1005)
        ]
    )

    payload = build_report_inventory("1")

    assert payload["summary"]["total_reports"] == 1000
    assert payload["total"] == 500


def test_return_limit_caps_items_at_500_but_summary_counts_all():
    rows = [
        {
            "assistant_id": "20261116_8PD",
            "thread_id": "t",
            "report_id": f"r{index}",
            "content": "完成",
            "created_at": None,
        }
        for index in range(600)
    ]

    payload = assemble_inventory([], rows, {})

    assert payload["summary"]["total_reports"] == 600
    assert payload["total"] == 500
    assert len(payload["items"]) == 500
    assert all("_moment" not in item for item in payload["items"])
