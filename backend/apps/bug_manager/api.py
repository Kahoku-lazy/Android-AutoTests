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
    drafts = build_bug_drafts(task)
    created_count = 0
    updated_count = 0
    for draft in drafts:
        created, updated = _upsert_draft(task, draft)
        created_count += int(created)
        updated_count += int(updated)
    return {"created": created_count, "updated": updated_count, "skipped": 0}


def sync_visible_tasks(user_id: str | None) -> dict:
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
    row = _visible_bugs(user_id).filter(id=bug_id).first()
    return serialize_bug(row, detail=True) if row is not None else None


def update_bug_status(user_id: str | None, bug_id: int, status: str) -> dict | None:
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
    if not user_id:
        return BugTicket.objects.none()
    try:
        int(user_id)
    except (TypeError, ValueError):
        return BugTicket.objects.none()
    return BugTicket.objects.all()


def _summary(qs) -> dict:
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
        "requirement_breakdown": by_category.get(BugTicket.CATEGORY_REQUIREMENT_BREAKDOWN, 0),
        "open": by_status.get(BugTicket.STATUS_OPEN, 0),
        "resolved": by_status.get(BugTicket.STATUS_RESOLVED, 0),
        "ignored": by_status.get(BugTicket.STATUS_IGNORED, 0),
    }


def _keyword_q(keyword: str) -> Q:
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
    identity = getattr(task, "case_identity", None)
    rows = case_identity_rows(identity)
    return {"case_label": case_identity_label(identity), "case_rows": rows}


def _task_title(task) -> str:
    text = " ".join(str(getattr(task, "title", "") or "").split())
    return (text or "未命名任务")[:500]


def _created_by(task) -> str:
    created_by = str(getattr(task, "created_by", "") or "").strip()
    if created_by:
        return created_by
    agent = getattr(task, "agent", None)
    return str(getattr(agent, "owner_id", "") or "").strip()


def _report_locator(task_id: int) -> dict:
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
    raw = row.failure if isinstance(row.failure, dict) else {}
    steps = raw.get("steps")
    if not isinstance(steps, list):
        return []
    return [item for item in steps if isinstance(item, dict)]


def _preview(detail: str) -> str:
    text = " ".join(str(detail or "").split())
    if len(text) <= _PREVIEW_LIMIT:
        return text
    return text[:_PREVIEW_LIMIT] + "…"


def _iso(value) -> str:
    return value.isoformat() if value else ""


def _clean(value: str | None) -> str:
    return str(value or "").strip().lower()
