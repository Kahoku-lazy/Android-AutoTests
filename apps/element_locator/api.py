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
    "get_web_elements",
    "get_web_groups",
    "create_page",
    "create_page_manually",
    "rename_page",
    "delete_page",
    "update_page_parent",
    "upsert_element",
    "update_element",
    "create_flow",
    "get_or_create_flow",
    "delete_flow",
    "clear_all",
    "create_web_group",
    "rename_web_group",
    "delete_web_group",
    "batch_move_web_groups",
    "create_web_element",
    "update_web_element",
    "delete_web_element",
    "batch_import_web_elements",
    "create_web_page_flow",
    "delete_web_page_flow",
    "create_api_group",
    "rename_api_group",
    "delete_api_group",
    "batch_move_api_groups",
    "create_api_endpoint",
    "update_api_endpoint",
    "delete_api_endpoint",
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
    "batch_delete_files",
    "serialize_directory",
]

from .api_directories import (
    batch_delete_files,
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


def get_web_elements(locator_type=None, is_test_point=None):
    """Get web elements, optionally filtered."""
    from .models import WebElement

    qs = WebElement.objects.all()
    if locator_type:
        qs = qs.filter(locator_type=locator_type)
    if is_test_point is not None:
        qs = qs.filter(is_test_point=is_test_point)
    return list(qs.order_by("name"))


def get_web_groups():
    """Get all web groups ordered by name."""
    from .models import WebGroup

    return list(WebGroup.objects.order_by("sort_order", "name"))


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


def update_element(el_id, updates):
    """Update element metadata fields."""
    if updates:
        Element.objects.filter(id=el_id).update(**updates)


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


# ── WebGroup 写操作 ──


def create_web_group(name, parent_id=None, is_folder=False, sort_order=0):
    """Create a web group or folder."""
    from .models import WebGroup

    return WebGroup.objects.create(
        name=name,
        parent_id=parent_id,
        is_folder=is_folder,
        sort_order=sort_order,
    )


def rename_web_group(group_id, name):
    """Rename a web group."""
    from .models import WebGroup

    WebGroup.objects.filter(id=group_id).update(name=name)


def delete_web_group(group_id):
    """Delete a web group; descendant elements become unclassified (group=None)."""
    from .models import WebElement, WebGroup

    ids = {group_id}

    def _descendant_ids(node_id):
        for child in WebGroup.objects.filter(parent_id=node_id):
            ids.add(child.id)
            _descendant_ids(child.id)

    _descendant_ids(group_id)
    WebElement.objects.filter(group_id__in=ids).update(group=None)
    WebGroup.objects.filter(id=group_id).delete()


def batch_move_web_groups(group_ids, parent_id):
    """Batch move web groups to a target parent."""
    from .models import WebGroup

    WebGroup.objects.filter(id__in=group_ids).update(parent_id=parent_id)


# ── WebElement 写操作 ──


def create_web_element(
    group,
    name,
    locator_type,
    locator_value,
    page_url="",
    description="",
    tags="",
    is_test_point=False,
    directory_id=None,
):
    """Create a web element."""
    from .models import WebElement

    return WebElement.objects.create(
        group=group,
        directory_id=directory_id,
        name=name,
        locator_type=locator_type,
        locator_value=locator_value,
        page_url=page_url,
        description=description,
        tags=tags,
        is_test_point=is_test_point,
    )


def update_web_element(el_id, updates):
    """Update a web element's fields (partial, by field presence)."""
    from .models import WebElement

    try:
        el = WebElement.objects.get(id=el_id)
    except WebElement.DoesNotExist:
        return None
    update_fields = []
    for k in [
        "name",
        "locator_type",
        "locator_value",
        "page_url",
        "description",
        "tags",
        "is_test_point",
        "group",
    ]:
        if k in updates:
            setattr(el, k, updates[k])
            update_fields.append(k)
    if update_fields:
        el.save(update_fields=update_fields + ["updated_at"])
    return el


def delete_web_element(el_id):
    """Delete a web element."""
    from .models import WebElement

    WebElement.objects.filter(id=el_id).delete()


def batch_import_web_elements(items):
    """Batch import web elements. Returns (saved, skipped, errors)."""
    from .models import WebElement

    saved = 0
    skipped = 0
    errors = []
    for item in items:
        name = (item.get("name") or "").strip()
        locator_type = item.get("locator_type", "css_selector")
        locator_value = (item.get("locator_value") or "").strip()
        if not name or not locator_value:
            skipped += 1
            continue
        try:
            WebElement.objects.create(
                name=name,
                locator_type=locator_type,
                locator_value=locator_value,
                page_url=item.get("page_url", ""),
                description=item.get("description", ""),
                tags=item.get("tags", ""),
                is_test_point=bool(item.get("is_test_point", False)),
            )
            saved += 1
        except Exception as e:
            errors.append(f"{name}: {e}")
            skipped += 1
    return saved, skipped, errors


# ── WebPageFlow 写操作 ──


def create_web_page_flow(from_group, to_group, trigger_element_id=None, trigger_action="click"):
    """Create a web page flow."""
    from .models import WebPageFlow

    return WebPageFlow.objects.create(
        from_group=from_group,
        to_group=to_group,
        trigger_element_id=trigger_element_id,
        trigger_action=trigger_action,
    )


def delete_web_page_flow(flow_id):
    """Delete a web page flow."""
    from .models import WebPageFlow

    WebPageFlow.objects.filter(id=flow_id).delete()


# ── ApiGroup 写操作 ──


def create_api_group(name, parent_id=None, is_folder=False, sort_order=0):
    """Create an api group or folder."""
    from .models import ApiGroup

    return ApiGroup.objects.create(
        name=name,
        parent_id=parent_id,
        is_folder=is_folder,
        sort_order=sort_order,
    )


def rename_api_group(group_id, name):
    """Rename an api group."""
    from .models import ApiGroup

    ApiGroup.objects.filter(id=group_id).update(name=name)


def delete_api_group(group_id):
    """Delete an api group; descendant endpoints become unclassified (group=None)."""
    from .models import ApiEndpoint, ApiGroup

    ids = {group_id}

    def _descendant_ids(node_id):
        for child in ApiGroup.objects.filter(parent_id=node_id):
            ids.add(child.id)
            _descendant_ids(child.id)

    _descendant_ids(group_id)
    ApiEndpoint.objects.filter(group_id__in=ids).update(group=None)
    ApiGroup.objects.filter(id=group_id).delete()


def batch_move_api_groups(group_ids, parent_id):
    """Batch move api groups to a target parent."""
    from .models import ApiGroup

    ApiGroup.objects.filter(id__in=group_ids).update(parent_id=parent_id)


# ── ApiEndpoint 写操作 ──


def create_api_endpoint(
    group,
    name,
    method,
    url,
    headers=None,
    request_body_schema=None,
    response_body_schema=None,
    description="",
    tags="",
    is_test_point=False,
    directory_id=None,
):
    """Create an api endpoint."""
    from .models import ApiEndpoint

    return ApiEndpoint.objects.create(
        group=group,
        directory_id=directory_id,
        name=name,
        method=method,
        url=url,
        headers=headers or {},
        request_body_schema=request_body_schema or {},
        response_body_schema=response_body_schema or {},
        description=description,
        tags=tags,
        is_test_point=is_test_point,
    )


def update_api_endpoint(el_id, updates):
    """Update an api endpoint's fields (partial, by field presence)."""
    from .models import ApiEndpoint

    try:
        e = ApiEndpoint.objects.get(id=el_id)
    except ApiEndpoint.DoesNotExist:
        return None
    for k in [
        "name",
        "method",
        "url",
        "headers",
        "request_body_schema",
        "response_body_schema",
        "description",
        "tags",
        "is_test_point",
        "group",
    ]:
        if k in updates:
            setattr(e, k, updates[k])
    e.save()
    return e


def delete_api_endpoint(el_id):
    """Delete an api endpoint."""
    from .models import ApiEndpoint

    ApiEndpoint.objects.filter(id=el_id).delete()
