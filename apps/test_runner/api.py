"""test-runner public API."""

__all__ = [
    "delete_task_card",
    "get_active_run",
    "get_active_runs_info",
    "get_run_results",
    "list_active_runs",
    "persist_results",
    "resolve_creator",
    "save_task_card",
    "stop_run",
    "TestRunner",
    "TestRunnerCallback",
]

from .models import TaskCard, TestResult, TestRunRecord
from .runner import (
    TestRunner,
    TestRunnerCallback,
    get_active_run,
    get_active_runs_info,
    list_active_runs,
    stop_run,
)


def resolve_creator(creator) -> str:
    """Convert numeric Django user ID to username; real usernames pass through.

    Historical bug: frontend stored JWT ``sub`` (user id) as creator.
    """
    if not creator:
        return ""
    s = str(creator).strip()
    if not s.isdigit():
        return s
    try:
        from django.contrib.auth.models import User

        return User.objects.get(id=int(s)).username
    except Exception:
        return s


# ── Query helpers ──


def get_run_results(run_id: str) -> list[dict]:
    """获取某次执行的所有测试结果。返回 dict 列表，不返回 ORM 对象。"""
    return list(
        TestResult.objects.filter(run_id=run_id)
        .order_by("created_at")
        .values(
            "id",
            "case_id",
            "case_type",
            "iteration",
            "result",
            "duration_ms",
            "detail",
            "step_details",
            "created_at",
        )
    )


# ── Write helpers ──


def persist_results(run_record, case_results: list) -> list[dict]:
    """批量持久化测试结果。返回写入记录的 dict 列表。"""
    objs = [
        TestResult(
            run=run_record,
            case_id=r.case_id,
            case_type=getattr(r, "case_type", "ui_automation"),
            iteration=r.iteration,
            result=r.result,
            duration_ms=r.duration_ms,
            detail=getattr(r, "detail", "") or "",
        )
        for r in case_results
    ]
    created = TestResult.objects.bulk_create(objs)
    return [{"id": obj.id, "case_id": obj.case_id, "result": obj.result} for obj in created]


# ── TaskCard write helpers ──


def save_task_card(task_data: dict) -> dict:
    """Create or update a TaskCard. Returns dict with task_id.

    Args:
        task_data: Dict with task card fields (uses frontend camelCase keys).

    Returns:
        dict: {"id": task_id}

    Raises:
        ValueError: if task_id is missing or empty.
    """
    task_id = (task_data.get("id") or "").strip()
    if not task_id:
        raise ValueError("task_id is required")

    creator = resolve_creator(task_data.get("creator", ""))
    defaults = {
        "name": task_data.get("name", ""),
        "creator": creator,
        "mode": task_data.get("mode", "immediate"),
        "task_type": task_data.get("taskType", "ui_automation"),
        "device_serial": task_data.get("deviceSerial", ""),
        "case_ids": task_data.get("caseIds", []),
        "loop_count": task_data.get("loopCount", 1),
        "interval_seconds": task_data.get("intervalSeconds", 5),
        "case_items": task_data.get("caseItems", []),
        "step_states": task_data.get("stepStates", []),
        "overall_pass": task_data.get("overallPass", 0),
        "overall_fail": task_data.get("overallFail", 0),
        "logs": (task_data.get("logs") or [])[-200:],
        "outcome": task_data.get("outcome", ""),
        "round": task_data.get("round", 0),
        "conclusion": task_data.get("conclusion", ""),
        "bug_ticket": task_data.get("bugTicket", ""),
        "failed_steps": (task_data.get("failedSteps") or [])[-200:],
        "current_case_title": task_data.get("currentCaseTitle", ""),
        "current_iteration": int(task_data.get("currentIteration") or 0),
        "start_at": task_data.get("startAt") or "",
        "end_at": task_data.get("endAt") or "",
    }

    try:
        task = TaskCard.objects.get(task_id=task_id)
        # ── Protect state-machine-managed fields from frontend auto-save ──
        # When the backend has set status to "done" or "running", the
        # frontend's 3-second auto-save must not overwrite these fields
        # with stale in-memory values.
        _sm_managed = task.status in ("done", "running")
        for k, v in defaults.items():
            if _sm_managed and k in (
                "status",
                "outcome",
                "case_items",
                "overall_pass",
                "overall_fail",
            ):
                continue
            setattr(task, k, v)
        # running flag: only set by state machine, never by frontend save
        if not _sm_managed:
            task.running = task_data.get("running", False)
        task.save()
    except TaskCard.DoesNotExist:
        task = TaskCard(
            task_id=task_id,
            name=task_data.get("name", ""),
            creator=creator,
            mode=task_data.get("mode", "immediate"),
            task_type=task_data.get("taskType", "ui_automation"),
            device_serial=task_data.get("deviceSerial", ""),
            case_ids=task_data.get("caseIds", []),
            loop_count=task_data.get("loopCount", 1),
            interval_seconds=task_data.get("intervalSeconds", 5),
            running=False,
            case_items=task_data.get("caseItems", []),
            step_states=task_data.get("stepStates", []),
            overall_pass=task_data.get("overallPass", 0),
            overall_fail=task_data.get("overallFail", 0),
            logs=(task_data.get("logs") or [])[-200:],
            outcome=task_data.get("outcome", ""),
            round=task_data.get("round", 0),
            conclusion=task_data.get("conclusion", ""),
            bug_ticket=task_data.get("bugTicket", ""),
            failed_steps=(task_data.get("failedSteps") or [])[-200:],
            current_case_title=task_data.get("currentCaseTitle", ""),
            current_iteration=int(task_data.get("currentIteration") or 0),
            start_at=task_data.get("startAt") or "",
            end_at=task_data.get("endAt") or "",
            status="idle",
        )
        task.save()

    return {"id": task_id}


def delete_task_card(task_id: str) -> None:
    """Delete a TaskCard by task_id. No-op if not found."""
    TaskCard.objects.filter(task_id=task_id).delete()


__all__ = [
    "TaskCard",
    "TestRunRecord",
    "TestResult",
    "TestRunner",
    "TestRunnerCallback",
    "get_active_run",
    "stop_run",
    "list_active_runs",
    "get_active_runs_info",
    "get_run_results",
    "persist_results",
    "save_task_card",
    "delete_task_card",
]
