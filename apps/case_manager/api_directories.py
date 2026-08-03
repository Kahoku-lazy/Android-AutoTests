"""case-manager directory API — tree, CRUD, batch-move."""

__all__ = [
    "batch_move_items",
    "create_directory",
    "delete_directory",
    "get_directory_tree",
    "update_directory",
]

import json
import logging

from .models import CaseDirectory, TestDefinition

logger = logging.getLogger(__name__)


def get_directory_tree(case_type=None):
    """Return the full directory tree as nested dicts with case nodes.

    Args:
        case_type: None (backward-compat, queries TestDefinition only),
                   or one of 'ui_automation', 'storage', 'api_testing'.
    """
    # Select the correct model and related_name based on case_type
    if case_type == "storage":
        _CaseModel = _get_storage_model()
        _related = "storage_testcases"
    elif case_type == "api_testing":
        _CaseModel = _get_api_model()
        _related = "api_testcases"
    elif case_type == "web_automation":
        _CaseModel = _get_web_model()
        _related = "web_testcases"
    else:
        _CaseModel = TestDefinition
        _related = "test_definitions"

    def _build_node(dir_obj):
        children = [_build_node(c) for c in dir_obj.children.all().order_by("sort_order", "id")]

        case_nodes = []
        case_qs = getattr(dir_obj, _related).all().order_by("title")

        for td in case_qs:
            try:
                if hasattr(td, "steps_json"):
                    step_count = len(json.loads(td.steps_json or "[]"))
                else:
                    # StorageTestCase uses a plain-text 'steps' field
                    step_count = len([l for l in (td.steps or "").split("\n") if l.strip()])
            except (json.JSONDecodeError, TypeError):
                step_count = 0
            case_nodes.append(
                {
                    "id": f"case:{td.id}",
                    "name": td.title or td.id,
                    "node_type": "case",
                    "case_id": td.id,
                    "case_type": case_type or "ui_automation",
                    "enabled": td.enabled,
                    "priority": td.priority,
                    "category": td.category,
                    "step_count": step_count,
                    "children": [],
                }
            )

        case_count = getattr(dir_obj, _related).count()

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

    resolved_type = case_type or "ui_automation"
    roots = CaseDirectory.objects.filter(parent__isnull=True, case_type=resolved_type).order_by(
        "sort_order", "id"
    )
    tree = [_build_node(r) for r in roots]

    # Append orphan cases (directory_id=NULL) as root-level case nodes
    orphan_qs = _CaseModel.objects.filter(directory__isnull=True).order_by("title")
    for td in orphan_qs:
        tree.append(
            {
                "id": f"case:{td.id}",
                "name": td.title or td.id,
                "node_type": "case",
                "case_id": td.id,
                "case_type": case_type or "ui_automation",
                "enabled": td.enabled,
                "priority": td.priority,
                "category": td.category,
                "children": [],
            }
        )

    return tree


def _get_storage_model():
    """Lazy-load storage model (may not exist yet in early phases)."""
    try:
        from .models_storage import StorageTestCase

        return StorageTestCase
    except ImportError:
        return TestDefinition


def _get_web_model():
    """Lazy-load web model."""
    try:
        from .models_web import WebTestCase

        return WebTestCase
    except ImportError:
        return TestDefinition


def _get_api_model():
    """Lazy-load API model (may not exist yet in early phases)."""
    try:
        from .models_api import ApiTestCase

        return ApiTestCase
    except ImportError:
        return TestDefinition


def create_directory(name, parent_id=None, sort_order=0, created_by="", case_type="ui_automation"):
    """Create a new directory. Returns (ok, data_or_error)."""
    if not name or not name.strip():
        return False, "目录名称不能为空"

    parent = None
    if parent_id is not None:
        try:
            parent = CaseDirectory.objects.get(id=parent_id)
            if parent.parent is not None:
                return False, "只支持两级目录，不能创建三级目录"
            # Inherit case_type from parent
            case_type = parent.case_type
        except CaseDirectory.DoesNotExist:
            return False, f"父级目录不存在: {parent_id}"

    # Check uniqueness within same parent + case_type
    if CaseDirectory.objects.filter(parent=parent, name=name.strip(), case_type=case_type).exists():
        return False, f"该层级下已存在同名目录: {name}"

    obj = CaseDirectory.objects.create(
        name=name.strip(),
        parent=parent,
        sort_order=sort_order,
        created_by=created_by or "",
        case_type=case_type,
    )
    return True, {
        "id": obj.id,
        "name": obj.name,
        "parent_id": obj.parent_id,
        "sort_order": obj.sort_order,
        "case_type": obj.case_type,
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

    if obj.created_by and deleted_by and obj.created_by != deleted_by and not obj.allow_delete:
        return False, f"只有目录创建者（{obj.created_by}）可以删除此目录"

    child_count = obj.children.count()
    case_count = obj.test_definitions.count()
    if hasattr(obj, "storage_testcases"):
        case_count += obj.storage_testcases.count()
    if hasattr(obj, "api_testcases"):
        case_count += obj.api_testcases.count()
    if hasattr(obj, "web_testcases"):
        case_count += obj.web_testcases.count()

    if child_count > 0 or case_count > 0:
        return False, {
            "message": "目录下存在子目录或用例，请先清空后再删除",
            "child_count": child_count,
            "case_count": case_count,
        }

    obj.delete()
    return True, {"id": dir_id, "deleted": True}


def batch_move_items(items: list[dict], target_directory_id: int) -> dict:
    """Batch move cases and/or directories to a target directory.

    Args:
        items: list of {"type": "case", "id": "TC-001"} or {"type": "directory", "id": 5}
        target_directory_id: destination directory ID

    Returns:
        {"moved": N, "errors": [...]}
    """
    moved = 0
    errors = []

    try:
        target_dir = CaseDirectory.objects.get(id=target_directory_id)
    except CaseDirectory.DoesNotExist:
        return {
            "moved": 0,
            "errors": [{"id": "target", "reason": f"目标目录不存在: {target_directory_id}"}],
        }

    for item in items:
        item_type = item.get("type")
        item_id = item.get("id")
        try:
            if item_type == "case":
                # Look up case across all three tables
                case = _find_case_across_types(item_id)
                if case is None:
                    errors.append({"id": item_id, "reason": f"用例不存在: {item_id}"})
                    continue
                case.directory = target_dir
                case.save()
                moved += 1
            elif item_type == "directory":
                if int(item_id) == int(target_directory_id):
                    errors.append({"id": item_id, "reason": "不能将目录移动到自身"})
                    continue
                dir_obj = CaseDirectory.objects.get(id=item_id)
                if target_dir.parent is not None:
                    errors.append({"id": item_id, "reason": "只支持两级目录，目标目录已是二级目录"})
                    continue
                if CaseDirectory.objects.filter(parent=target_dir, name=dir_obj.name).exists():
                    errors.append(
                        {"id": item_id, "reason": f"目标位置已存在同名目录: {dir_obj.name}"}
                    )
                    continue
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
        except CaseDirectory.DoesNotExist:
            errors.append({"id": item_id, "reason": f"目录不存在: {item_id}"})
        except Exception as e:
            errors.append({"id": item_id, "reason": str(e)})

    return {"moved": moved, "errors": errors}


def _find_case_across_types(case_id):
    """Look up a case ID across all four test case tables. Returns the model instance or None."""
    from .api_lock import find_case_across_types

    instance, _ = find_case_across_types(case_id)
    return instance
