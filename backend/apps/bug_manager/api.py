"""BUG ticket read/write services.

All writes in this app go through this module. Task state is read-only here: BUG
registration must never change a task's status or verdict.
"""

from __future__ import annotations

import json
import re

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from backend.apps.bug_manager.extract import BugDraft, build_bug_drafts
from backend.apps.bug_manager.models import BugTicket
from backend.apps.task_list.case_identity import case_identity_label, case_identity_rows
from backend.apps.task_list.models import Task
from utils.logs import backend_log

_CATEGORY_VALUES = {choice[0] for choice in BugTicket.CATEGORY_CHOICES}
_STATUS_VALUES = {choice[0] for choice in BugTicket.STATUS_CHOICES}
_PREVIEW_LIMIT = 240
_LIST_LIMIT = 500
_TASK_STATUSES = ("failed", "interrupted", "completed")


def record_task_bugs(task) -> dict:
    """
    Persist all BUG drafts for one task, idempotently.

    Args:
        task: Task-like object with id/title/task_kind/status/result/agent_id.

    Returns:
        ``{"created": n, "updated": n, "skipped": n}``. A task with no drafts
        contributes zero rows; sync counts those tasks separately.
    """
    drafts = build_bug_drafts(task)
    created_count = 0
    updated_count = 0
    for draft in drafts:
        created, updated = _upsert_draft(task, draft)
        created_count += int(created)
        updated_count += int(updated)
    return {"created": created_count, "updated": updated_count, "skipped": 0}


def sync_visible_tasks(user_id: str | None) -> dict:
    """
    Backfill BUG tickets from tasks visible to a user.

    Args:
        user_id: Current user id; empty means no visible tasks.

    Returns:
        ``{"scanned": n, "created": n, "updated": n, "skipped": n}``.
    """
    result = {"scanned": 0, "created": 0, "updated": 0, "skipped": 0}
    if not user_id:
        return result
    try:
        int(user_id)
    except (TypeError, ValueError):
        return result

    tasks = Task.objects.filter(status__in=_TASK_STATUSES).order_by("id")
    for task in tasks:
        result["scanned"] += 1
        if not build_bug_drafts(task):
            result["skipped"] += 1
            continue
        try:
            counts = record_task_bugs(task)
        except Exception:  # noqa: BLE001 - 单任务失败不阻断整批补录
            backend_log.exception("sync bug tickets failed task=%s", task.id)
            result["skipped"] += 1
            continue
        result["created"] += counts["created"]
        result["updated"] += counts["updated"]
    return result


def list_bugs(
    user_id: str | None,
    *,
    category: str = "",
    status: str = "",
    keyword: str = "",
) -> dict:
    """
    Return BUG tickets visible to a user with summary counters.

    Args:
        user_id: Current user id.
        category: Optional category filter.
        status: Optional status filter.
        keyword: Matches title/detail/task title/task id/BUG id.

    Returns:
        ``{"summary": {...}, "total": n, "items": [...], "truncated": bool}``.

    Raises:
        ValueError: Unknown category or status.
    """
    category = _clean(category)
    status = _clean(status)
    if category and category not in _CATEGORY_VALUES:
        raise ValueError("未知的 BUG 分类")
    if status and status not in _STATUS_VALUES:
        raise ValueError("未知的 BUG 状态")

    visible = _visible_bugs(user_id)
    summary = _summary(visible)
    qs = visible
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    keyword = _clean(keyword)
    if keyword:
        qs = qs.filter(_keyword_q(keyword))
    total = qs.count()
    rows = list(qs.order_by("-created_at", "-id")[:_LIST_LIMIT])
    return {
        "summary": summary,
        "total": total,
        "items": [serialize_bug(row) for row in rows],
        "truncated": total > _LIST_LIMIT,
    }


def get_bug(user_id: str | None, bug_id: int) -> dict | None:
    """
    Return one visible BUG ticket with full detail.

    Args:
        user_id: Current user id.
        bug_id: BUG ticket id.

    Returns:
        Serialized ticket, or None when missing or invisible.
    """
    row = _visible_bugs(user_id).filter(id=bug_id).first()
    return serialize_bug(row, detail=True) if row is not None else None


def update_bug_status(user_id: str | None, bug_id: int, status: str) -> dict | None:
    """
    Update the processing status of a visible BUG ticket.

    Args:
        user_id: Current user id.
        bug_id: BUG ticket id.
        status: open / resolved / ignored.

    Returns:
        Updated ticket, or None when missing or invisible.

    Raises:
        ValueError: Unknown status.
    """
    status = _clean(status)
    if status not in _STATUS_VALUES:
        raise ValueError("BUG 状态只能是 open / resolved / ignored")
    row = _visible_bugs(user_id).filter(id=bug_id).first()
    if row is None:
        return None
    row.status = status
    row.resolved_at = timezone.now() if status == "resolved" else None
    row.save(update_fields=["status", "resolved_at", "updated_at"])
    return serialize_bug(row, detail=True)


def serialize_bug(row: BugTicket, *, detail: bool = False) -> dict:
    """
    Serialize a BUG row for the API.

    Args:
        row: BUG ticket.
        detail: Include full detail instead of a preview.

    Returns:
        Snake_case payload consumed by the frontend.
    """
    labels = dict(BugTicket.CATEGORY_CHOICES)
    status_labels = dict(BugTicket.STATUS_CHOICES)
    payload = {
        "id": row.id,
        "bug_no": row.bug_no,
        "category": row.category,
        "category_label": labels.get(row.category, row.category),
        "title": row.title,
        "status": row.status,
        "status_label": status_labels.get(row.status, row.status),
        "task_id": row.task_id,
        "task_title": row.task_title,
        "case_label": row.case_label or "",
        "case_rows": row.case_rows if isinstance(row.case_rows, list) else [],
        "task_kind": row.task_kind,
        "task_status": row.task_status,
        "agent_id": row.agent_id,
        "created_by": row.created_by,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
        "resolved_at": _iso(row.resolved_at),
        "failure_steps": _failure_steps(row),
    }
    if detail:
        payload["detail"] = row.detail
        payload.update(_report_locator(row.task_id))
    else:
        payload["detail_preview"] = _preview(row.detail)
    return payload


def _upsert_draft(task, draft: BugDraft) -> tuple[bool, bool]:
    """Create or update one draft while preserving the human-owned status."""
    defaults = {
        "title": draft.title,
        "detail": draft.detail,
        "failure": draft.failure,
        "task_title": _task_title(task),
        **_case_snapshot(task),
        "task_kind": str(getattr(task, "task_kind", "") or ""),
        "task_status": str(getattr(task, "status", "") or ""),
        "agent_id": int(getattr(task, "agent_id", 0) or 0),
        "created_by": _created_by(task),
    }
    lookup = {
        "task_id": int(getattr(task, "id", 0) or 0),
        "category": draft.category,
        "source_ref": draft.source_ref,
    }
    try:
        with transaction.atomic():
            row, created = BugTicket.objects.get_or_create(
                **lookup,
                defaults={**defaults, "status": BugTicket.STATUS_OPEN},
            )
    except IntegrityError:
        row = BugTicket.objects.get(**lookup)
        created = False
    if created:
        return True, False
    update_fields: list[str] = []
    for field, value in defaults.items():
        if field in {"case_label", "case_rows"} and not value:
            continue
        if getattr(row, field) != value:
            setattr(row, field, value)
            update_fields.append(field)
    if update_fields:
        row.save(update_fields=[*update_fields, "updated_at"])
    return False, True


def _visible_bugs(user_id: str | None):
    """Base queryset filtered by the agents visible to the current user."""
    if not user_id:
        return BugTicket.objects.none()
    try:
        int(user_id)
    except (TypeError, ValueError):
        return BugTicket.objects.none()
    return BugTicket.objects.all()


def _summary(qs) -> dict:
    """Counters over the full visible set, independent of the active filters."""
    by_category = {
        row["category"]: row["count"] for row in qs.values("category").annotate(count=Count("id"))
    }
    by_status = {
        row["status"]: row["count"] for row in qs.values("status").annotate(count=Count("id"))
    }
    return {
        "total": qs.count(),
        "ui_automation": by_category.get(BugTicket.CATEGORY_UI_AUTOMATION, 0),
        "case_authoring": by_category.get(BugTicket.CATEGORY_CASE_AUTHORING, 0),
        "open": by_status.get(BugTicket.STATUS_OPEN, 0),
        "resolved": by_status.get(BugTicket.STATUS_RESOLVED, 0),
        "ignored": by_status.get(BugTicket.STATUS_IGNORED, 0),
    }


def _keyword_q(keyword: str) -> Q:
    """Build the keyword predicate, including numeric task id and BUG number."""
    q = (
        Q(title__icontains=keyword)
        | Q(detail__icontains=keyword)
        | Q(task_title__icontains=keyword)
        | Q(case_label__icontains=keyword)
    )
    if keyword.isdigit():
        q |= Q(task_id=int(keyword)) | Q(id=int(keyword))
    bug_match = re.fullmatch(r"BUG-0*(\d+)", keyword, flags=re.IGNORECASE)
    if bug_match:
        q |= Q(id=int(bug_match.group(1)))
    return q


def _case_snapshot(task) -> dict:
    """从任务冻结身份抄文案和行。读不到时两处都空，不编造。"""
    identity = getattr(task, "case_identity", None)
    rows = case_identity_rows(identity)
    return {"case_label": case_identity_label(identity), "case_rows": rows}


def _task_title(task) -> str:
    """Task title snapshot, clamped for the model."""
    text = " ".join(str(getattr(task, "title", "") or "").split())
    return (text or "未命名任务")[:500]


def _created_by(task) -> str:
    """Task creator, falling back to the agent owner for historical tasks."""
    created_by = str(getattr(task, "created_by", "") or "").strip()
    if created_by:
        return created_by
    agent = getattr(task, "agent", None)
    return str(getattr(agent, "owner_id", "") or "").strip()


def _report_locator(task_id: int) -> dict:
    """任务还在且结果里有报告定位时才返回。任务删除后两个字段都是空串。"""
    empty = {"report_run": "", "report_name": ""}
    task = Task.objects.filter(pk=task_id).only("result").first()
    if task is None:
        return empty
    try:
        payload = json.loads(task.result or "{}")
    except (TypeError, ValueError):
        return empty
    if not isinstance(payload, dict):
        return empty
    run = str(payload.get("report_run") or "")
    name = str(payload.get("report_name") or "")
    if not run or not name:
        return empty
    return {"report_run": run, "report_name": name}


def _failure_steps(row: BugTicket) -> list[dict]:
    """详情与列表共用的失败步骤。旧单没有快照时为空列表。"""
    raw = row.failure if isinstance(row.failure, dict) else {}
    steps = raw.get("steps")
    if not isinstance(steps, list):
        return []
    return [item for item in steps if isinstance(item, dict)]


def _preview(detail: str) -> str:
    """Short detail for list payloads."""
    text = " ".join(str(detail or "").split())
    if len(text) <= _PREVIEW_LIMIT:
        return text
    return text[:_PREVIEW_LIMIT] + "…"


def _iso(value) -> str:
    """ISO timestamp or empty string."""
    return value.isoformat() if value else ""


def _clean(value: str | None) -> str:
    """Trim and lowercase a filter value."""
    return str(value or "").strip().lower()
