from __future__ import annotations

import json

from datetime import datetime, timezone

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage
from backend.apps.task_list.case_identity import case_identity_label
from backend.apps.task_list.models import Task
from backend.models.constants import TaskStatus

_SCAN_LIMIT = 1000
_LIST_LIMIT = 500

_TERMINAL_STATUSES = frozenset({TaskStatus.COMPLETED, TaskStatus.FAILED, "success"})

_SUMMARY_LIMIT = 80

_EMPTY_SUMMARY = {"total_reports": 0, "sop_reports": 0, "agent_reports": 0}


def build_report_inventory(
    user_id: str | None,
    *,
    source: str = "",
    keyword: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    if not user_id:
        return {"summary": dict(_EMPTY_SUMMARY), "total": 0, "items": []}
    try:
        int(user_id)
    except (ValueError, TypeError):
        return {"summary": dict(_EMPTY_SUMMARY), "total": 0, "items": []}

    sop_rows = _fetch_sop_candidates()
    agent_rows, assistant_names = _fetch_agent_candidates()
    return assemble_inventory(
        sop_rows,
        agent_rows,
        assistant_names,
        source=source,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )


def assemble_inventory(
    sop_rows: list[dict],
    agent_rows: list[dict],
    assistant_names: dict[str, str],
    *,
    source: str = "",
    keyword: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    items: list[dict] = []
    for row in sop_rows:
        item = _sop_item(row)
        if item is not None:
            items.append(item)
    for row in agent_rows:
        item = _agent_item(row, assistant_names)
        if item is not None:
            items.append(item)

    needle = keyword.strip().lower()
    kept = [
        item
        for item in items
        if _source_ok(item, source)
        and _keyword_ok(item, needle)
        and _date_ok(item, start_date, end_date)
    ]
    kept.sort(key=_moment_key, reverse=True)

    n_sop = sum(1 for item in kept if item["source"] == "sop")
    n_agent = len(kept) - n_sop
    returned = kept[:_LIST_LIMIT]
    for item in returned:
        item.pop("_moment", None)
    return {
        "summary": {
            "total_reports": len(kept),
            "sop_reports": n_sop,
            "agent_reports": n_agent,
        },
        "total": len(returned),
        "items": returned,
    }


def _fetch_sop_candidates() -> list[dict]:
    rows = (
        Task.objects.filter(status__in=sorted(_TERMINAL_STATUSES))
        .only(
            "id",
            "title",
            "status",
            "device_serial",
            "device_label",
            "case_identity",
            "kind",
            "result",
            "started_at",
            "finished_at",
            "created_at",
        )
        .order_by("-finished_at", "-id")[:_SCAN_LIMIT]
    )
    return [
        {
            "task_id": row.id,
            "title": row.title or "",
            "status": row.status or "",
            "device_serial": row.device_serial or "",
            "device_label": row.device_label or "",
            "case_identity": row.case_identity,
            "kind": row.kind or "",
            "result": row.result or "",
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _fetch_agent_candidates() -> tuple[list[dict], dict[str, str]]:
    messages = (
        AIAssistantMessage.objects.filter(role=AIAssistantMessage.ROLE_ASSISTANT)
        .exclude(report_id="")
        .select_related("thread")
        .order_by("-created_at", "-id")[:_SCAN_LIMIT]
    )
    rows = [
        {
            "assistant_id": message.thread.assistant_id,
            "thread_id": message.thread.thread_id,
            "report_id": message.report_id,
            "content": message.content or "",
            "created_at": message.created_at,
        }
        for message in messages
    ]
    ids = {row["assistant_id"] for row in rows}
    names = dict(
        AIAssistant.objects.filter(assistant_id__in=ids).values_list("assistant_id", "display_name")
    )
    return rows, names


def _sop_item(row: dict) -> dict | None:
    status = str(row.get("status") or "").lower()
    if status not in _TERMINAL_STATUSES:
        return None
    run, name = _report_locator(row.get("result"))
    if not run or not name:
        return None
    started = row.get("started_at")
    finished = row.get("finished_at")
    return {
        "source": "sop",
        "report_run": run,
        "report_name": name,
        "task_id": row.get("task_id"),
        "task_title": row.get("title") or "",
        "case_label": ""
        if row.get("kind") == "requirement_breakdown"
        else case_identity_label(row.get("case_identity")),
        "device": ""
        if row.get("kind") in {"case_authoring", "requirement_breakdown"}
        else (row.get("device_label") or "").strip() or (row.get("device_serial") or "").strip(),
        "workflow_kind": row.get("kind") or "",
        "module_count": _module_count(row.get("result")),
        "status": status,
        "started_at": _iso(started or row.get("created_at")),
        "finished_at": _iso(finished),
        "duration": _duration(started, finished),
        "_moment": finished or row.get("created_at") or started,
    }


def _agent_item(row: dict, assistant_names: dict[str, str]) -> dict | None:
    report_id = str(row.get("report_id") or "").strip()
    if not report_id:
        return None
    assistant_id = str(row.get("assistant_id") or "")
    content = " ".join(str(row.get("content") or "").split())
    return {
        "source": "agent",
        "assistant_id": assistant_id,
        "assistant_name": assistant_names.get(assistant_id, ""),
        "thread_id": str(row.get("thread_id") or ""),
        "report_id": report_id,
        "summary": content[:_SUMMARY_LIMIT],
        "created_at": _iso(row.get("created_at")),
        "_moment": row.get("created_at"),
    }


def _module_count(result: object) -> int:
    try:
        payload = json.loads(result or "{}")
    except (TypeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        return int(payload.get("module_count") or 0)
    except (TypeError, ValueError):
        return 0


def _report_locator(result: object) -> tuple[str, str]:
    try:
        payload = json.loads(result or "{}")
    except (TypeError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return str(payload.get("report_run") or ""), str(payload.get("report_name") or "")


def _source_ok(item: dict, source: str) -> bool:
    if source in ("sop", "agent"):
        return item["source"] == source
    return True


def _keyword_ok(item: dict, needle: str) -> bool:
    if not needle:
        return True
    if needle.isdigit():
        return item["source"] == "sop" and str(item.get("task_id") or "") == needle
    if item["source"] == "sop":
        haystack = " ".join([item.get("case_label") or "", item.get("task_title") or ""])
    else:
        haystack = " ".join([item.get("assistant_name") or "", item.get("assistant_id") or ""])
    return needle in haystack.lower()


def _date_ok(item: dict, start_date: str, end_date: str) -> bool:
    if not start_date and not end_date:
        return True
    moment = item.get("_moment")
    if moment is None:
        return False
    day = moment.date().isoformat()
    if start_date and day < start_date:
        return False
    if end_date and day > end_date:
        return False
    return True


def _moment_key(item: dict) -> datetime:
    moment = item.get("_moment")
    if moment is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return moment


def _iso(value) -> str:
    return value.isoformat() if value else ""


def _duration(started, finished) -> str:
    if not started or not finished:
        return "—"
    total = max(int((finished - started).total_seconds()), 0)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{seconds:02d}s"
    return f"{seconds}s"
