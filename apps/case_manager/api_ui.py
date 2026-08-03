"""case-manager UI automation case API — CRUD, batch, helpers."""

__all__ = [
    "ConflictError",
    "batch_save_definitions",
    "get_definition",
    "get_enabled_definitions",
    "save_definition",
]

import json
import logging

from datetime import date, datetime

from .models import CaseDirectory, TestDefinition

logger = logging.getLogger(__name__)


class ConflictError(ValueError):
    """Raised when optimistic lock check fails — caller should return HTTP 409."""


def _parse_datetime(val):
    """Parse a datetime value from ISO string, datetime object, or date object.
    Returns a datetime or None. Microseconds are stripped for cross-DB consistency.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(microsecond=0)
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    if not isinstance(val, str):
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(val, fmt).replace(microsecond=0)
        except ValueError:
            continue
    return None


def get_enabled_definitions(case_ids):
    """Get enabled test definitions by ID list (UI automation cases only)."""
    return list(TestDefinition.objects.filter(id__in=case_ids, enabled=True))


def get_definition(case_id):
    """Get a single UI automation definition by ID, or None."""
    try:
        return TestDefinition.objects.get(id=case_id)
    except TestDefinition.DoesNotExist:
        return None


def save_definition(case_id, **fields):
    """Create or update a UI automation test definition.

    Raises ValueError on duplicate title, ConflictError on optimistic lock failure.
    """
    client_updated_at = fields.pop("client_updated_at", None)
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            logger.warning(
                "Directory %s not found when saving UI case, saving without directory", directory_id
            )

    title = fields.get("title", "")

    # Optimistic lock: check updated_at before overwriting
    existing = TestDefinition.objects.filter(id=case_id).only("id", "updated_at").first()
    if existing and client_updated_at:
        client_ts = _parse_datetime(client_updated_at)
        if client_ts and existing.updated_at:
            db_ts = existing.updated_at.replace(microsecond=0)
            if client_ts != db_ts:
                raise ConflictError(f"用例「{title or case_id}」已被他人修改，请刷新后重试")

    # Check for duplicate title in the same directory
    dup = (
        TestDefinition.objects.filter(directory=directory, title=title).exclude(id=case_id).first()
    )
    if dup:
        dir_label = directory.name if directory else "根级（未分类）"
        raise ValueError(f"目录「{dir_label}」下已存在同名用例「{title}」")

    defaults = {
        "title": title,
        "category": fields.get("category", ""),
        "description": fields.get("description", ""),
        "steps": fields.get("steps", ""),
        "steps_json": json.dumps(fields.get("steps_data", []), ensure_ascii=False),
        "enabled": fields.get("enabled", True),
        "package_name": fields.get("package_name", ""),
        "directory": directory,
        "priority": fields.get("priority", "P1"),
        "design_method": fields.get("design_method", ""),
        "precondition": fields.get("precondition", ""),
        "expected_result": fields.get("expected_result", ""),
        "metrics": fields.get("metrics", ""),
        "visibility": fields.get("visibility", "public"),
        "permitted_users": json.dumps(fields.get("permitted_users", []), ensure_ascii=False),
        "permission": fields.get("permission", "edit"),
        "permitted_editors": json.dumps(fields.get("permitted_editors", []), ensure_ascii=False),
        "case_type": fields.get("case_type", "ui_automation"),
    }
    obj, _ = TestDefinition.objects.update_or_create(id=case_id, defaults=defaults)
    return obj


def batch_save_definitions(cases: list[dict], overwrite: bool = False) -> dict:
    """Batch create/update test definitions.

    Args:
        cases: list of dicts, each with keys matching save_definition fields.
        overwrite: if False, skip cases whose id already exists.

    Returns:
        {"imported": [...], "skipped": [...], "failed": [...]}
    """
    imported = []
    skipped = []
    failed = []

    for case in cases:
        cid = case.get("case_id") or case.get("id", "")
        if not cid:
            failed.append({"reason": "missing id", "case": case})
            continue

        if not overwrite and TestDefinition.objects.filter(id=cid).exists():
            skipped.append({"id": cid, "reason": "already exists"})
            continue

        try:
            obj = save_definition(case_id=cid, **case)
            imported.append({"id": obj.id, "title": obj.title})
        except Exception as e:
            failed.append({"id": cid, "reason": str(e)})

    return {"imported": imported, "skipped": skipped, "failed": failed}
