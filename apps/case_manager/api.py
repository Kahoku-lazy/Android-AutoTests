"""case-manager public API.

Semi-shared: models (cross-app read), api functions (cross-app write).
"""

import json
from .models import TestDefinition, TestCaseCache, CaseDirectory


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
            "children": children + case_nodes,
        }

    roots = CaseDirectory.objects.filter(parent__isnull=True).order_by("sort_order", "id")
    return [_build_node(r) for r in roots]


def create_directory(name, parent_id=None, sort_order=0):
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


def delete_directory(dir_id):
    """Delete a directory. Returns (ok, data_or_error)."""
    try:
        obj = CaseDirectory.objects.get(id=dir_id)
    except CaseDirectory.DoesNotExist:
        return False, f"目录不存在: {dir_id}"

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
    """Create or update a test definition."""
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            pass  # Keep null if not found

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
    }
    obj, _ = TestDefinition.objects.update_or_create(id=case_id, defaults=defaults)
    return obj


def cache_yaml(name, yaml_content):
    """Cache YAML export to DB."""
    return TestCaseCache.objects.create(name=name, yaml_content=yaml_content)


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
    "TestCaseCache",
    "CaseDirectory",
    "get_enabled_definitions",
    "get_definition",
    "save_definition",
    "batch_save_definitions",
    "cache_yaml",
    "get_directory_tree",
    "create_directory",
    "update_directory",
    "delete_directory",
    "batch_move_items",
]
