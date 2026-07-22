"""case-manager storage test case API — CRUD, batch."""

import json
from .models import CaseDirectory
from .models_storage import StorageTestCase
from .api_ui import _parse_datetime, ConflictError


def get_storage_definitions(case_ids):
    """Get enabled storage test cases by ID list."""
    return list(StorageTestCase.objects.filter(id__in=case_ids, enabled=True))


def get_storage_definition(case_id):
    """Get a single storage definition by ID, or None."""
    try:
        return StorageTestCase.objects.get(id=case_id)
    except StorageTestCase.DoesNotExist:
        return None


def save_storage_definition(case_id, merge=False, **fields):
    """Create or update a storage test case.

    When merge=True, new rows are appended to existing rows (deduplicated by title).
    Raises ValueError on duplicate title, ConflictError on optimistic lock failure.
    """
    client_updated_at = fields.pop("client_updated_at", None)
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            pass

    title = fields.get("title", "")

    # Optimistic lock
    existing = StorageTestCase.objects.filter(id=case_id).only("id", "updated_at").first()
    if existing and client_updated_at:
        client_ts = _parse_datetime(client_updated_at)
        if client_ts and existing.updated_at:
            db_ts = existing.updated_at.replace(microsecond=0)
            if client_ts != db_ts:
                raise ConflictError(f"存储用例「{title or case_id}」已被他人修改，请刷新后重试")

    # Check duplicate title (skip when merging into existing case)
    if not merge or not existing:
        dup = (StorageTestCase.objects.filter(directory=directory, title=title)
               .exclude(id=case_id).first())
        if dup:
            dir_label = directory.name if directory else "根级（未分类）"
            raise ValueError(f"目录「{dir_label}」下已存在同名存储用例「{title}」")

    new_rows = fields.get("rows", [])
    if merge and existing and new_rows:
        existing_rows = existing.rows if isinstance(existing.rows, list) else []
        existing_titles = {r.get("title", "") for r in existing_rows}
        merged = list(existing_rows)
        for row in new_rows:
            if row.get("title", "") not in existing_titles:
                merged.append(row)
                existing_titles.add(row.get("title", ""))
        # Re-index ids
        for i, row in enumerate(merged):
            row["id"] = i + 1
        fields["rows"] = merged

    defaults = {
        "title": fields.get("title", title),
        "category": fields.get("category", ""),
        "description": fields.get("description", ""),
        "enabled": fields.get("enabled", True),
        "directory": directory,
        "priority": fields.get("priority", "P1"),
        "precondition": fields.get("precondition", ""),
        "steps": fields.get("steps", ""),
        "expected_result": fields.get("expected_result", ""),
        "custom_columns": fields.get("custom_columns", []),
        "rows": fields.get("rows", []),
        "design_method": fields.get("design_method", ""),
        "metrics": fields.get("metrics", ""),
        "visibility": fields.get("visibility", "public"),
        "permitted_users": json.dumps(fields.get("permitted_users", []), ensure_ascii=False),
        "permission": fields.get("permission", "edit"),
        "permitted_editors": json.dumps(fields.get("permitted_editors", []), ensure_ascii=False),
        "case_type": "storage",
    }
    obj, _ = StorageTestCase.objects.update_or_create(id=case_id, defaults=defaults)
    return obj


def batch_save_storage_definitions(cases: list[dict], overwrite: bool = False) -> dict:
    """Batch create/update storage test cases."""
    imported = []
    skipped = []
    failed = []

    for case in cases:
        cid = case.get("case_id") or case.get("id", "")
        if not cid:
            failed.append({"reason": "missing id", "case": case})
            continue
        if not overwrite and StorageTestCase.objects.filter(id=cid).exists():
            skipped.append({"id": cid, "reason": "already exists"})
            continue
        try:
            obj = save_storage_definition(case_id=cid, **case)
            imported.append({"id": obj.id, "title": obj.title})
        except Exception as e:
            failed.append({"id": cid, "reason": str(e)})

    return {"imported": imported, "skipped": skipped, "failed": failed}
