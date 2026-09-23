"""element-locator public API.

写操作铁律：views 调用本模块写函数写 DB，禁止直接 ORM INSERT/UPDATE/DELETE。
跨 App 读 Model 放开（读函数），跨 App 写必须走本模块函数。
"""

__all__ = [
    "Page",
    "Element",
    "PageFlow",
    "ImportConflictError",
    "get_page_full",
    "import_snapshot_page",
    "simple_yaml_dump",
    "get_test_points",
    "get_flows",
    "create_page",
    "create_page_manually",
    "rename_page",
    "delete_page",
    "update_page_parent",
    "upsert_element",
    "create_element",
    "update_element",
    "delete_elements",
    "CREATE_FIELDS",
    "UPDATE_FIELDS",
    "normalize_element_fields",
    "create_flow",
    "get_or_create_flow",
    "delete_flow",
    "clear_all",
    # projects / directories
    "ConflictError",
    "ensure_system_projects",
    "list_projects",
    "get_project_by_code",
    "get_project_tree",
    "serialize_project",
    "create_directory",
    "update_directory",
    "delete_directory",
    "move_item",
    "batch_move_items",
    "batch_delete_files",
    "batch_delete_items",
    "serialize_directory",
]

from django.db import transaction

from .api_directories import (
    batch_delete_files,
    batch_delete_items,
    batch_move_items,
    create_directory,
    delete_directory,
    move_item,
    serialize_directory,
    update_directory,
)
from .api_projects import (
    ConflictError,
    ensure_system_projects,
    get_project_by_code,
    get_project_tree,
    list_projects,
    serialize_project,
)
from .api_snapshot import ImportConflictError, get_page_full, import_snapshot_page
from .element_fields import (
    CREATE_FIELDS,
    UPDATE_FIELDS,
    normalize_element_fields,
)
from .models import Element, Page, PageFlow
from .service import simple_yaml_dump

# ── Query helpers (cross-app read — allowed per 读放开规则) ──


def get_test_points(page_ids=None):
    """Get elements marked as test points, optionally filtered by page."""
    qs = Element.objects.filter(is_test_point=True).select_related("page")
    if page_ids:
        qs = qs.filter(page_id__in=page_ids)
    return list(qs.order_by("page_id", "id"))


def get_flows():
    """Get all page flows with page labels."""
    return list(PageFlow.objects.select_related("from_page", "to_page", "trigger_element"))


# ── Page 写操作 ──


def create_page(device, package="", activity="", screenshot_path="", element_count=0):
    """Create a page snapshot record."""
    return Page.objects.create(
        device=device,
        package=package,
        activity=activity,
        screenshot_path=screenshot_path,
        element_count=element_count,
    )


def create_page_manually(
    device,
    parent_id,
    is_folder,
    label,
    package="",
    activity="",
    directory_id=None,
):
    """Create a page or folder manually (distinct from snapshot create_page).

    项目化后：工作台新建页面传 directory_id，is_folder 应为 False。
    """
    return Page.objects.create(
        device=device,
        parent_id=parent_id,
        is_folder=is_folder,
        label=label,
        package=package,
        activity=activity,
        directory_id=directory_id,
    )


def rename_page(page_id, label):
    """Rename a page."""
    Page.objects.filter(id=page_id).update(label=label)


def delete_page(page_id):
    """Delete a page."""
    Page.objects.filter(id=page_id).delete()


def update_page_parent(page_id, parent_id):
    """Update a page's parent (移动后写库)。供 page_tree.move_page 调用，校验在 page_tree 层。"""
    Page.objects.filter(id=page_id).update(parent_id=parent_id)


# ── Element 写操作 ──


def upsert_element(page, fields):
    """Upsert an element on a page (by resource_id+bounds). 返回 (element, updated)。"""
    existing = Element.objects.filter(
        page=page,
        resource_id=fields.get("resource_id", ""),
        bounds=fields.get("bounds", ""),
    ).first()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.save()
        return existing, True
    el = Element.objects.create(page=page, **fields)
    page.element_count = Element.objects.filter(page=page).count()
    page.save(update_fields=["element_count"])
    return el, False


def create_element(page, fields):
    """仅新增一条元素（不做 upsert）。

    必填口径：`alias` 非空，且 `resource_id` 与 `bounds` 至少一个非空——两者皆空时
    多行会撞 `(page, resource_id, bounds)` 唯一约束。命中同页既有时抛 ConflictError。
    """
    normalized = normalize_element_fields(fields, CREATE_FIELDS)
    if not normalized.get("alias"):
        raise ValueError("元素名称(alias)必填")
    if not normalized.get("resource_id") and not normalized.get("bounds"):
        raise ValueError("resource-id 与坐标至少填一个")
    duplicated = Element.objects.filter(
        page=page,
        resource_id=normalized.get("resource_id", ""),
        bounds=normalized.get("bounds", ""),
    ).exists()
    if duplicated:
        raise ConflictError("该元素已在当前页面中（相同 resource-id 与位置）")
    element = Element.objects.create(page=page, **normalized)
    page.element_count = Element.objects.filter(page=page).count()
    page.save(update_fields=["element_count"])
    return element


def update_element(el_id, updates):
    """按元素 id 定点更新呈现列里可编辑的四项（元素名称/文本/主定位/测试点）。

    越界字段与非法值抛 ValueError（视图映射 400），元素不存在抛 LookupError（视图映射 404）。
    """
    normalized = normalize_element_fields(updates, UPDATE_FIELDS)
    if not normalized:
        return
    if not Element.objects.filter(id=el_id).update(**normalized):
        raise LookupError("元素不存在")


def delete_elements(element_ids):
    """按元素 id 整批删除（原子），并回写受影响页面的 element_count。

    空集合抛 ValueError（视图映射 400）；任一 id 不存在抛 LookupError（视图映射 404），
    此时整批不落库。
    """
    try:
        ids = sorted({int(item) for item in element_ids})
    except (TypeError, ValueError):
        raise ValueError("元素 id 必须是整数") from None
    if not ids:
        raise ValueError("元素 id 不能为空")
    rows = list(Element.objects.filter(id__in=ids).values_list("id", "page_id"))
    if len(rows) != len(ids):
        raise LookupError("元素不存在")
    page_ids = {page_id for _, page_id in rows}
    with transaction.atomic():
        Element.objects.filter(id__in=ids).delete()
        for page_id in page_ids:
            remaining = Element.objects.filter(page_id=page_id).count()
            Page.objects.filter(id=page_id).update(element_count=remaining)
    return {"deleted": len(ids)}


# ── Flow 写操作 ──


def create_flow(from_page_id, to_page_id, trigger_element_id=None, trigger_action="click"):
    """Create a page flow record."""
    return PageFlow.objects.create(
        from_page_id=from_page_id,
        to_page_id=to_page_id,
        trigger_element_id=trigger_element_id,
        trigger_action=trigger_action,
    )


def get_or_create_flow(from_page_id, to_page_id, trigger_element_id=None, trigger_action="click"):
    """幂等建边：按 (from, to, trigger_element) 去重，复用已有记录。返回 (flow, created)。"""
    existing = PageFlow.objects.filter(
        from_page_id=from_page_id,
        to_page_id=to_page_id,
        trigger_element_id=trigger_element_id,
    ).first()
    if existing:
        return existing, False
    flow = PageFlow.objects.create(
        from_page_id=from_page_id,
        to_page_id=to_page_id,
        trigger_element_id=trigger_element_id,
        trigger_action=trigger_action,
    )
    return flow, True


def delete_flow(flow_id):
    """Delete a page flow."""
    PageFlow.objects.filter(id=flow_id).delete()


def clear_all():
    """Clear all pages, elements, and flows."""
    Element.objects.all().delete()
    PageFlow.objects.all().delete()
    Page.objects.all().delete()
