"""case-manager public API.

Semi-shared: models (cross-app read), api functions (cross-app write).
"""

import json
from datetime import datetime, date
from .models import TestDefinition, CaseDirectory


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
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


# ── Directory helpers ──


def get_directory_tree():
    """Return the full directory tree as nested dicts with case nodes."""

    def _build_node(dir_obj):
        children = [_build_node(c) for c in dir_obj.children.all().order_by("sort_order", "id")]

        # Query direct test cases and convert to case leaf nodes
        case_nodes = []
        for td in dir_obj.test_definitions.all().order_by("title"):
            try:
                step_count = len(json.loads(td.steps_json or "[]"))
            except Exception:
                step_count = 0
            case_nodes.append(
                {
                    "id": f"case:{td.id}",
                    "name": td.title or td.id,
                    "node_type": "case",
                    "case_id": td.id,
                    "enabled": td.enabled,
                    "priority": td.priority,
                    "category": td.category,
                    "step_count": step_count,
                    "children": [],
                }
            )

        case_count = dir_obj.test_definitions.count()
        return {
            "id": dir_obj.id,
            "name": dir_obj.name,
            "parent_id": dir_obj.parent_id,
            "sort_order": dir_obj.sort_order,
            "node_type": "directory",
            "case_count": case_count + sum(c["case_count"] for c in children),
            "created_by": dir_obj.created_by or "",
            "allow_create": dir_obj.allow_create,
            "allow_delete": dir_obj.allow_delete,
            "children": children + case_nodes,
        }

    roots = CaseDirectory.objects.filter(parent__isnull=True).order_by("sort_order", "id")
    tree = [_build_node(r) for r in roots]

    # Append orphan cases (directory_id=NULL) as root-level case nodes
    orphan_cases = TestDefinition.objects.filter(directory__isnull=True).order_by("title")
    for td in orphan_cases:
        try:
            step_count = len(json.loads(td.steps_json or "[]"))
        except Exception:
            step_count = 0
        tree.append(
            {
                "id": f"case:{td.id}",
                "name": td.title or td.id,
                "node_type": "case",
                "case_id": td.id,
                "enabled": td.enabled,
                "priority": td.priority,
                "category": td.category,
                "step_count": step_count,
                "children": [],
            }
        )

    return tree


def create_directory(name, parent_id=None, sort_order=0, created_by=""):
    """Create a new directory. Returns (ok, data_or_error)."""
    if not name or not name.strip():
        return False, "目录名称不能为空"

    parent = None
    if parent_id is not None:
        try:
            parent = CaseDirectory.objects.get(id=parent_id)
            # Only allow two levels: if parent has a parent, reject
            if parent.parent is not None:
                return False, "只支持两级目录，不能创建三级目录"
        except CaseDirectory.DoesNotExist:
            return False, f"父级目录不存在: {parent_id}"

    # Check uniqueness within same parent
    if CaseDirectory.objects.filter(parent=parent, name=name.strip()).exists():
        return False, f"该层级下已存在同名目录: {name}"

    obj = CaseDirectory.objects.create(
        name=name.strip(),
        parent=parent,
        sort_order=sort_order,
        created_by=created_by or "",
    )
    return True, {
        "id": obj.id,
        "name": obj.name,
        "parent_id": obj.parent_id,
        "sort_order": obj.sort_order,
    }


def update_directory(dir_id, name=None, parent_id=None, sort_order=None):
    """Update a directory. Returns (ok, data_or_error)."""
    try:
        obj = CaseDirectory.objects.get(id=dir_id)
    except CaseDirectory.DoesNotExist:
        return False, f"目录不存在: {dir_id}"

    if name is not None:
        name = name.strip()
        if not name:
            return False, "目录名称不能为空"
        obj.name = name

    if parent_id is not None:
        try:
            new_parent = CaseDirectory.objects.get(id=parent_id) if parent_id else None
        except CaseDirectory.DoesNotExist:
            return False, f"父级目录不存在: {parent_id}"
        obj.parent = new_parent

    if sort_order is not None:
        obj.sort_order = sort_order

    obj.save()
    return True, {
        "id": obj.id,
        "name": obj.name,
        "parent_id": obj.parent_id,
        "sort_order": obj.sort_order,
    }


def delete_directory(dir_id, deleted_by=""):
    """Delete a directory. Only creator or allow_delete users can delete. Returns (ok, data_or_error)."""
    try:
        obj = CaseDirectory.objects.get(id=dir_id)
    except CaseDirectory.DoesNotExist:
        return False, f"目录不存在: {dir_id}"

    # Permission: only creator or allow_delete users can delete
    if obj.created_by and deleted_by and obj.created_by != deleted_by and not obj.allow_delete:
        return False, f"只有目录创建者（{obj.created_by}）可以删除此目录"

    child_count = obj.children.count()
    case_count = obj.test_definitions.count()

    if child_count > 0 or case_count > 0:
        return False, {
            "message": "目录下存在子目录或用例，请先清空后再删除",
            "child_count": child_count,
            "case_count": case_count,
        }

    obj.delete()
    return True, {"id": dir_id, "deleted": True}


# ── Query helpers ──


def get_enabled_definitions(case_ids):
    """Get enabled test definitions by ID list."""
    return list(TestDefinition.objects.filter(id__in=case_ids, enabled=True))


def get_definition(case_id):
    """Get a single definition by ID, or None."""
    try:
        return TestDefinition.objects.get(id=case_id)
    except TestDefinition.DoesNotExist:
        return None


# ── Write helpers ──


def save_definition(case_id, **fields):
    """Create or update a test definition. Raises ValueError on duplicate title or conflict.

    Optimistic locking: if client_updated_at is provided and doesn't match the
    current record's updated_at, raises ConflictError (409) to prevent lost updates.
    """
    from datetime import datetime

    client_updated_at = fields.pop("client_updated_at", None)
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            pass  # Keep null if not found

    title = fields.get("title", "")

    # Optimistic lock: check updated_at before overwriting
    existing = TestDefinition.objects.filter(id=case_id).only("id", "updated_at").first()
    if existing and client_updated_at:
        # Parse client_updated_at (ISO or "YYYY-MM-DD HH:MM:SS" from serialization)
        client_ts = _parse_datetime(client_updated_at)
        if client_ts and existing.updated_at:
            # Normalize both to second precision for comparison (MySQL truncates microseconds)
            db_ts = existing.updated_at.replace(microsecond=0)
            if client_ts != db_ts:
                raise ConflictError(
                    f"用例「{title or case_id}」已被他人修改，请刷新后重试"
                )

    # Check for duplicate title in the same directory
    dup = TestDefinition.objects.filter(
        directory=directory, title=title
    ).exclude(id=case_id).first()
    if dup:
        dir_label = directory.name if directory else "根级（未分类）"
        raise ValueError(f"目录「{dir_label}」下已存在同名用例「{title}」")

    defaults = {
        "title": fields.get("title", ""),
        "category": fields.get("category", ""),
        "description": fields.get("description", ""),
        "steps": fields.get("steps", ""),
        "steps_json": json.dumps(fields.get("steps_data", []), ensure_ascii=False),
        "enabled": fields.get("enabled", True),
        "package_name": fields.get("package_name", ""),
        "directory": directory,
        # IoT PRD fields (from iot-test-case-agent)
        "priority": fields.get("priority", "P1"),
        "design_method": fields.get("design_method", ""),
        "precondition": fields.get("precondition", ""),
        "expected_result": fields.get("expected_result", ""),
        "metrics": fields.get("metrics", ""),
        "visibility": fields.get("visibility", "public"),
        "permitted_users": json.dumps(fields.get("permitted_users", []), ensure_ascii=False),
        "permission": fields.get("permission", "edit"),
        "permitted_editors": json.dumps(fields.get("permitted_editors", []), ensure_ascii=False),
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


def batch_move_items(items: list[dict], target_directory_id: int) -> dict:
    """Batch move cases and/or directories to a target directory.

    Args:
        items: list of {"type": "case"|"directory", "id": "TC-001"|5}
        target_directory_id: destination directory ID

    Returns:
        {"moved": N, "errors": [{"id": ..., "reason": ...}]}
    """
    moved = 0
    errors = []

    try:
        target_dir = CaseDirectory.objects.get(id=target_directory_id)
    except CaseDirectory.DoesNotExist:
        return {"moved": 0, "errors": [{"id": "target", "reason": f"目标目录不存在: {target_directory_id}"}]}

    for item in items:
        item_type = item.get("type")
        item_id = item.get("id")
        try:
            if item_type == "case":
                case = TestDefinition.objects.get(id=item_id)
                case.directory = target_dir
                case.save()
                moved += 1
            elif item_type == "directory":
                if int(item_id) == int(target_directory_id):
                    errors.append({"id": item_id, "reason": "不能将目录移动到自身"})
                    continue
                dir_obj = CaseDirectory.objects.get(id=item_id)
                # Two-level enforcement
                if target_dir.parent is not None:
                    errors.append({"id": item_id, "reason": "只支持两级目录，目标目录已是二级目录"})
                    continue
                # Duplicate name check
                if CaseDirectory.objects.filter(parent=target_dir, name=dir_obj.name).exists():
                    errors.append({"id": item_id, "reason": f"目标位置已存在同名目录: {dir_obj.name}"})
                    continue
                # Prevent moving a directory into its own descendant
                ancestor = target_dir
                while ancestor is not None:
                    if ancestor.id == dir_obj.id:
                        errors.append({"id": item_id, "reason": "不能将目录移动到其子目录下"})
                        break
                    ancestor = ancestor.parent
                else:
                    dir_obj.parent = target_dir
                    dir_obj.save()
                    moved += 1
            else:
                errors.append({"id": item_id, "reason": f"未知类型: {item_type}"})
        except TestDefinition.DoesNotExist:
            errors.append({"id": item_id, "reason": f"用例不存在: {item_id}"})
        except CaseDirectory.DoesNotExist:
            errors.append({"id": item_id, "reason": f"目录不存在: {item_id}"})
        except Exception as e:
            errors.append({"id": item_id, "reason": str(e)})

    return {"moved": moved, "errors": errors}


__all__ = [
    "TestDefinition",
    "CaseDirectory",
    "get_enabled_definitions",
    "get_definition",
    "save_definition",
    "batch_save_definitions",
    "get_directory_tree",
    "create_directory",
    "update_directory",
    "delete_directory",
    "batch_move_items",
]
