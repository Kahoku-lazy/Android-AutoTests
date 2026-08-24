"""element-locator HTTP routes — element repository CRUD endpoints."""

import json
import logging

from django.db import IntegrityError
from django.db import models as dm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.device_pool.api import device, ensure_device

from . import api
from .models import Element, Page, PageFlow
from .page_tree import (
    MAX_PAGE_TREE_DEPTH,
    batch_move_pages,
    build_page_maps,
    compute_depth,
    page_depth,
    sibling_label_exists,
    validate_parent_and_depth,
)

logger = logging.getLogger(__name__)


# ── Page CRUD ──


def _page_payload(p, parent_map=None):
    depth = compute_depth(p.id, parent_map) if parent_map is not None else page_depth(p)
    return {
        "id": p.id,
        "device_id": p.device_id,
        "parent_id": p.parent_id,
        "is_folder": p.is_folder,
        "depth": depth,
        "label": p.label,
        "package": p.package,
        "activity": p.activity,
        "screenshot_path": p.screenshot_path,
        "ocr_json": p.ocr_json or None,
        "snapshot_id": p.snapshot_id,
        "element_count": p.element_count,
        "created_at": str(p.created_at),
        "flow_out": getattr(p, "flow_out", 0),
        "flow_in": getattr(p, "flow_in", 0),
    }


def list_pages(request):
    """GET /api/elements/pages — List recorded pages (flat, with parent_id).

    Uses a single-query parent_map to compute depths without N+1 DB round-trips.
    Supports ?offset=N&limit=N for pagination.
    """
    pages = (
        Page.objects.select_related("parent")
        .annotate(
            flow_out=dm.Count("outgoing_flows", distinct=True),
            flow_in=dm.Count("incoming_flows", distinct=True),
        )
        .order_by("is_folder", "label", "-created_at")
    )

    # Build in-memory parent map once to avoid N+1 in _page_payload → page_depth
    parent_map, _ = build_page_maps()
    result = [_page_payload(p, parent_map) for p in pages]
    return JsonResponse({"status": True, "pages": result, "max_depth": MAX_PAGE_TREE_DEPTH})


@csrf_exempt
def page_detail(request, page_id):
    """PUT/DELETE /api/elements/pages/{page_id}."""
    if request.method == "PUT":
        data = json.loads(request.body)
        new_label = data.get("label", "").strip()
        if not new_label:
            return JsonResponse({"status": False, "message": "页面名称不能为空"}, status=400)
        # Fetch once for validation, then update in one query
        page = Page.objects.filter(id=page_id).values("parent_id").first()
        if page is None:
            return JsonResponse({"status": False, "message": "页面不存在"}, status=404)
        parent_id = page["parent_id"]
        if sibling_label_exists(new_label, parent_id, exclude_id=page_id):
            return JsonResponse(
                {"status": False, "message": f"同级名称「{new_label}」已存在"}, status=409
            )
        api.rename_page(page_id, new_label)
        return JsonResponse({"status": True})
    elif request.method == "DELETE":
        api.delete_page(page_id)
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def create_page(request):
    """POST /api/elements/pages/create — Manually create a page or folder.

    Body: { label, parent_id?, is_folder?, package?, activity? }
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = json.loads(request.body)
    label = data.get("label", "").strip()
    if not label:
        return JsonResponse({"status": False, "message": "名称(label)必填"})

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None
    is_folder = bool(data.get("is_folder", False))

    try:
        validate_parent_and_depth(parent_id, is_folder=is_folder)
    except ValueError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=400)

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"status": False, "message": "父级目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"status": False, "message": "只能在目录下创建子级"}, status=400)

    if sibling_label_exists(label, parent_id):
        return JsonResponse({"status": False, "message": f"同级名称「{label}」已存在"}, status=409)

    dev_obj = ensure_device(serial=device.current_serial, name="Samsung")
    try:
        page = api.create_page_manually(
            dev_obj,
            parent_id,
            is_folder,
            label,
            package=data.get("package", ""),
            activity=data.get("activity", ""),
        )
    except IntegrityError:
        return JsonResponse(
            {"status": False, "message": f"创建失败，名称「{label}」可能已存在"}, status=409
        )
    return JsonResponse({"status": True, "page": _page_payload(page)})


@csrf_exempt
def pages_batch_move(request):
    """POST /api/elements/pages/batch-move — Move pages/folders to a target parent.

    Body: { page_ids: [1, 2], parent_id: 5 | null }
    parent_id=null moves items to root level.
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = json.loads(request.body)
    page_ids = data.get("page_ids") or []
    if not page_ids:
        return JsonResponse({"status": False, "message": "page_ids 不能为空"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"status": False, "message": "目标目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"status": False, "message": "目标必须是目录"}, status=400)

    try:
        ids = [int(x) for x in page_ids]
    except (TypeError, ValueError):
        return JsonResponse({"status": False, "message": "page_ids 格式无效"}, status=400)

    result = batch_move_pages(ids, parent_id)
    return JsonResponse({"status": True, **result})


def _element_payload(el):
    return {
        "id": el.id,
        "page_id": el.page_id,
        "alias": el.alias,
        "class_name": el.class_name,
        "text_val": el.text_val,
        "content_desc": el.content_desc,
        "resource_id": el.resource_id,
        "clickable": el.clickable,
        "enabled": el.enabled,
        "scrollable": el.scrollable,
        "checked": el.checked,
        "bounds": el.bounds,
        "x": el.x,
        "y": el.y,
        "width": el.width,
        "height": el.height,
        "depth": el.depth,
        "index": el.index,
        "thumbnail_path": el.thumbnail_path,
        "xpath_candidates": el.xpath_candidates,
        "is_test_point": el.is_test_point,
        "notes": el.notes,
    }


@csrf_exempt
def add_element_to_page(request, page_id):
    """POST /api/elements/pages/{page_id}/elements — Manually add element to page.

    Body: { alias, xpath, class_name?, text_val?, resource_id?, bounds?,
            clickable?, content_desc? }

    Same (page, resource_id, bounds) is upserted — duplicate save updates metadata.
    """
    try:
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return JsonResponse({"status": False, "message": "页面不存在"}, status=404)
        if page.is_folder:
            return JsonResponse(
                {"status": False, "message": "目录节点不能添加元素，请选择子页面"}, status=400
            )

        data = json.loads(request.body)
        alias = data.get("alias", "").strip()
        if not alias:
            return JsonResponse({"status": False, "message": "元素名称(alias)必填"})

        xpath = data.get("xpath", "")
        xpath_candidates_data = data.get("xpath_candidates")
        if xpath_candidates_data:
            xpaths = json.dumps(xpath_candidates_data)
        elif xpath:
            xpaths = json.dumps([{"type": "manual", "xpath": xpath, "count": 1}])
        else:
            xpaths = "[]"
        fields = {
            "alias": alias,
            "class_name": data.get("class_name", ""),
            "text_val": data.get("text_val", data.get("text", "")),
            "content_desc": data.get("content_desc", ""),
            "resource_id": data.get("resource_id", ""),
            "bounds": data.get("bounds", ""),
            "xpath_candidates": xpaths,
            "clickable": bool(data.get("clickable", False)),
            "enabled": bool(data.get("enabled", True)),
            "notes": data.get("notes", ""),
        }

        try:
            el, updated = api.upsert_element(page, fields)
        except IntegrityError:
            return JsonResponse(
                {
                    "status": False,
                    "message": "该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看",
                },
                status=409,
            )

        return JsonResponse(
            {
                "status": True,
                "updated": updated,
                "element": _element_payload(el),
            }
        )
    except Exception as e:
        return JsonResponse(
            {
                "status": False,
                "message": "保存元素失败，请稍后重试",
                "detail": str(e),
            },
            status=500,
        )


@csrf_exempt
def batch_add_elements(request, page_id):
    """POST /api/elements/pages/{page_id}/elements/batch — Batch save elements.

    Body: { elements: [{ alias, xpath, xpath_candidates, class_name, text_val,
            resource_id, bounds, clickable, content_desc }], strategy: "resource-id" }

    Each element already has its pre-selected XPath. Same per-element upsert logic.
    """
    try:
        page = Page.objects.get(id=page_id)
    except Page.DoesNotExist:
        return JsonResponse({"status": False, "message": "页面不存在"}, status=400)
    if page.is_folder:
        return JsonResponse({"status": False, "message": "目录节点不能添加元素"}, status=400)

    data = json.loads(request.body)
    items = data.get("elements", [])
    if not items:
        return JsonResponse({"status": False, "message": "elements 不能为空"}, status=400)

    saved = 0
    updated = 0
    skipped = 0
    errors = []

    # Pre-process items and prepare fields
    prepared = []
    for item in items:
        alias = item.get("alias", "").strip()
        if not alias:
            skipped += 1
            continue

        xpath_candidates_data = item.get("xpath_candidates")
        if xpath_candidates_data:
            xpaths = json.dumps(xpath_candidates_data)
        else:
            xpath = item.get("xpath", "")
            if xpath:
                xpaths = json.dumps(
                    [
                        {
                            "type": item.get("xpath_type", "manual"),
                            "xpath": xpath,
                            "count": item.get("xpath_count", 1),
                        }
                    ]
                )
            else:
                xpaths = "[]"

        rid = item.get("resource_id", "")
        bounds = item.get("bounds", "")
        prepared.append(
            {
                "alias": alias,
                "resource_id": rid,
                "bounds": bounds,
                "fields": {
                    "alias": alias,
                    "class_name": item.get("class_name", ""),
                    "text_val": item.get("text_val", ""),
                    "content_desc": item.get("content_desc", ""),
                    "resource_id": rid,
                    "bounds": bounds,
                    "xpath_candidates": xpaths,
                    "clickable": bool(item.get("clickable", False)),
                    "enabled": bool(item.get("enabled", True)),
                    "notes": item.get("notes", ""),
                },
            }
        )

    if not prepared:
        return JsonResponse(
            {
                "status": True,
                "saved": 0,
                "updated": 0,
                "skipped": skipped,
                "errors": errors[:5] if errors else [],
            }
        )

    # Process each element via api.upsert_element（写操作收敛到 api 层）
    for p in prepared:
        try:
            _, was_updated = api.upsert_element(page, p["fields"])
            if was_updated:
                updated += 1
            else:
                saved += 1
        except IntegrityError:
            skipped += 1
            continue
        except Exception as e:
            errors.append(f"{p['alias']}: {e}")
            skipped += 1
            continue

    result = {"status": True, "saved": saved, "updated": updated, "skipped": skipped}
    if errors:
        result["errors"] = errors[:5]
    return JsonResponse(result)


@csrf_exempt
def clear_pages(request):
    """POST /api/elements/pages/clear — Clear all pages/elements/flows."""
    api.clear_all()
    return JsonResponse({"status": True})


def page_elements(request, page_id):
    """GET /api/elements/pages/{page_id}/items — Page elements with filter + pagination.

    Query params: ?filter=all|clickable|text|testpoint&offset=0&limit=50
    """
    filter_type = request.GET.get("filter", "all")
    try:
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 100))
    except (ValueError, TypeError):
        offset, limit = 0, 100
    offset = max(0, offset)
    limit = max(1, min(limit, 500))  # cap at 500 to prevent oversized responses

    qs = Element.objects.filter(page_id=page_id)
    if filter_type == "clickable":
        qs = qs.filter(clickable=True)
    elif filter_type == "text":
        qs = qs.exclude(text_val="")
    elif filter_type == "testpoint":
        qs = qs.filter(is_test_point=True)

    total = qs.count()
    qs = qs.order_by("id")[offset : offset + limit]

    result = [
        {
            "id": e.id,
            "page_id": e.page_id,
            "class_name": e.class_name,
            "text_val": e.text_val,
            "content_desc": e.content_desc,
            "resource_id": e.resource_id,
            "bounds": e.bounds,
            "xpath_candidates": e.xpath_candidates,
            "clickable": e.clickable,
            "enabled": e.enabled,
            "alias": e.alias,
            "tags": e.tags,
            "is_test_point": e.is_test_point,
            "notes": e.notes,
            "created_at": str(e.created_at),
        }
        for e in qs
    ]
    return JsonResponse({"status": True, "elements": result, "total": total})


@csrf_exempt
def update_element(request, el_id):
    """PUT /api/elements/items/{el_id} — Update element metadata."""
    data = json.loads(request.body)
    updates = {}
    for k in ["alias", "tags", "notes"]:
        if k in data:
            updates[k] = data[k]
    if "is_test_point" in data:
        updates["is_test_point"] = bool(data["is_test_point"])
    api.update_element(el_id, updates)
    return JsonResponse({"status": True})


# ── Flow CRUD ──


@csrf_exempt
def flows_handler(request):
    """GET/POST /api/elements/flows."""
    if request.method == "GET":
        flows = PageFlow.objects.select_related("from_page", "to_page", "trigger_element").order_by(
            "-created_at"
        )
        result = [
            {
                "id": f.id,
                "from_page_id": f.from_page_id,
                "to_page_id": f.to_page_id,
                "trigger_element_id": f.trigger_element_id,
                "trigger_action": f.trigger_action,
                "created_at": str(f.created_at),
                "from_label": f.from_page.label if f.from_page_id else "",
                "to_label": f.to_page.label if f.to_page_id else "",
                "trigger_text": f.trigger_element.text_val if f.trigger_element_id else "",
                "trigger_rid": f.trigger_element.resource_id if f.trigger_element_id else "",
            }
            for f in flows
        ]
        return JsonResponse({"status": True, "flows": result})

    elif request.method == "POST":
        data = json.loads(request.body)
        api.create_flow(
            data["from_page_id"],
            data["to_page_id"],
            trigger_element_id=data.get("trigger_element_id"),
            trigger_action=data.get("trigger_action", "click"),
        )
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def delete_flow(request, flow_id):
    """DELETE /api/elements/flows/{flow_id}."""
    api.delete_flow(flow_id)
    return JsonResponse({"status": True})


# ── Web Element CRUD ──

LOCATOR_TYPE_CHOICES = [
    "css_selector",
    "xpath",
    "id",
    "class_name",
    "name",
    "tag_name",
    "link_text",
    "partial_link_text",
    "text",
    "test_id",
    "role",
    "placeholder",
]


def _web_element_payload(el):
    return {
        "id": el.id,
        "name": el.name,
        "locator_type": el.locator_type,
        "locator_value": el.locator_value,
        "page_url": el.page_url,
        "description": el.description,
        "tags": el.tags,
        "is_test_point": el.is_test_point,
        "group_id": el.group_id,
        "created_at": str(el.created_at),
        "updated_at": str(el.updated_at),
    }


def list_web_elements(request):
    """GET /api/elements/web/ — List web elements with filters."""
    from .models import WebElement

    qs = WebElement.objects.all()

    search = request.GET.get("search", "").strip()
    if search:
        from django.db.models import Q

        qs = qs.filter(
            Q(name__icontains=search)
            | Q(locator_value__icontains=search)
            | Q(description__icontains=search)
            | Q(tags__icontains=search)
        )

    locator_type = request.GET.get("locator_type", "").strip()
    if locator_type:
        qs = qs.filter(locator_type=locator_type)

    page_url = request.GET.get("page_url", "").strip()
    if page_url:
        qs = qs.filter(page_url__icontains=page_url)

    is_test_point = request.GET.get("is_test_point")
    if is_test_point is not None:
        qs = qs.filter(is_test_point=is_test_point == "1" or is_test_point == "true")

    group_id = request.GET.get("group_id")
    if group_id is not None:
        if group_id == "" or group_id == "null":
            qs = qs.filter(group__isnull=True)
        else:
            try:
                qs = qs.filter(group_id=int(group_id))
            except (ValueError, TypeError):
                pass

    qs = qs.order_by("-updated_at")
    result = [_web_element_payload(el) for el in qs]
    return JsonResponse({"status": True, "elements": result, "total": len(result)})


@csrf_exempt
def create_web_element(request):
    """POST /api/elements/web/ — Create a web element."""

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "元素名称(name)必填"}, status=400)

    locator_type = data.get("locator_type", "css_selector")
    if locator_type not in LOCATOR_TYPE_CHOICES:
        return JsonResponse(
            {
                "status": False,
                "message": f"无效的定位方式, 必须是: {', '.join(LOCATOR_TYPE_CHOICES)}",
            },
            status=400,
        )

    locator_value = data.get("locator_value", "").strip()
    if not locator_value:
        return JsonResponse({"status": False, "message": "定位值(locator_value)必填"}, status=400)

    try:
        group_id = data.get("group_id")
        group = None
        if group_id is not None and group_id != "":
            from .models import WebGroup

            try:
                group = WebGroup.objects.get(id=int(group_id))
            except (WebGroup.DoesNotExist, ValueError, TypeError):
                pass

        el = api.create_web_element(
            group,
            name,
            locator_type,
            locator_value,
            page_url=data.get("page_url", ""),
            description=data.get("description", ""),
            tags=data.get("tags", ""),
            is_test_point=bool(data.get("is_test_point", False)),
        )
    except Exception as e:
        return JsonResponse({"status": False, "message": f"创建失败: {e}"}, status=500)

    return JsonResponse({"status": True, "element": _web_element_payload(el)})


@csrf_exempt
def web_element_detail(request, el_id):
    """PUT/DELETE /api/elements/web/{el_id}/ — Update or delete a web element."""
    from .models import WebElement

    try:
        el = WebElement.objects.get(id=el_id)
    except WebElement.DoesNotExist:
        return JsonResponse({"status": False, "message": "元素不存在"}, status=404)

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

        if "name" in data and not data["name"].strip():
            return JsonResponse({"status": False, "message": "名称不能为空"}, status=400)
        if "locator_type" in data and data["locator_type"] not in LOCATOR_TYPE_CHOICES:
            return JsonResponse({"status": False, "message": "无效的定位方式"}, status=400)

        updates = dict(data)
        if "locator_value" in updates:
            updates["locator_value"] = updates["locator_value"].strip()
        if "is_test_point" in updates:
            updates["is_test_point"] = bool(updates["is_test_point"])
        if "group_id" in updates:
            gid = updates.pop("group_id")
            from .models import WebGroup

            if gid in (None, "", "null"):
                updates["group"] = None
            else:
                try:
                    updates["group"] = WebGroup.objects.get(id=int(gid))
                except (WebGroup.DoesNotExist, ValueError, TypeError):
                    updates.pop("group", None)

        el = api.update_web_element(el_id, updates)
        return JsonResponse({"status": True, "element": _web_element_payload(el)})

    elif request.method == "DELETE":
        api.delete_web_element(el_id)
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def batch_import_web_elements(request):
    """POST /api/elements/web/batch/ — Batch import web elements."""

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    items = data.get("elements", [])
    if not items:
        return JsonResponse({"status": False, "message": "elements 不能为空"}, status=400)

    saved, skipped, errors = 0, 0, []
    for item in items:
        name = item.get("name", "").strip()
        if not name:
            skipped += 1
            continue
        lt = item.get("locator_type", "css_selector")
        if lt not in LOCATOR_TYPE_CHOICES:
            skipped += 1
            continue
        lv = item.get("locator_value", "").strip()
        if not lv:
            skipped += 1
            continue
        try:
            api.create_web_element(
                None,
                name,
                lt,
                lv,
                page_url=item.get("page_url", ""),
                description=item.get("description", ""),
                tags=item.get("tags", ""),
                is_test_point=bool(item.get("is_test_point", False)),
            )
            saved += 1
        except Exception as e:
            errors.append(f"{name}: {e}")
            skipped += 1

    result = {"status": True, "saved": saved, "skipped": skipped}
    if errors:
        result["errors"] = errors[:5]
    return JsonResponse(result)


# ── Web Group CRUD ──


def _web_group_payload(g):
    children = getattr(g, "children", None)
    child_count = children.count() if children is not None else 0
    return {
        "id": g.id,
        "name": g.name,
        "parent_id": g.parent_id,
        "is_folder": g.is_folder,
        "sort_order": g.sort_order,
        "element_count": getattr(g, "_element_count", 0),
        "child_count": child_count,
        "created_at": str(g.created_at),
    }


def list_web_groups(request):
    """GET /api/elements/web-groups/ — Flat list of all groups with element_count."""
    from django.db.models import Count

    from .models import WebGroup

    groups = list(
        WebGroup.objects.annotate(_element_count=Count("elements")).order_by("sort_order", "name")
    )

    return JsonResponse(
        {
            "status": True,
            "groups": [_web_group_payload(g) for g in groups],
        }
    )


@csrf_exempt
def create_web_group(request):
    """POST /api/elements/web-groups/create/ — Create a group or folder."""
    from .models import WebGroup

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "分组名称必填"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None

    if parent_id:
        try:
            parent = WebGroup.objects.get(pk=parent_id)
            if not parent.is_folder:
                return JsonResponse(
                    {"status": False, "message": "只能将分组添加在目录下"}, status=400
                )
        except WebGroup.DoesNotExist:
            return JsonResponse({"status": False, "message": "父级分组不存在"}, status=404)

    is_folder = bool(data.get("is_folder", False))

    try:
        g = api.create_web_group(
            name,
            parent_id=parent_id,
            is_folder=is_folder,
            sort_order=data.get("sort_order", 0),
        )
    except Exception as e:
        return JsonResponse({"status": False, "message": f"创建失败: {e}"}, status=500)

    return JsonResponse({"status": True, "group": _web_group_payload(g)})


@csrf_exempt
def web_group_detail(request, group_id):
    """PUT/DELETE /api/elements/web-groups/{id}/ — Rename or delete a group."""
    from .models import WebGroup

    try:
        g = WebGroup.objects.get(id=group_id)
    except WebGroup.DoesNotExist:
        return JsonResponse({"status": False, "message": "分组不存在"}, status=404)

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

        if "name" in data:
            name = data["name"].strip()
            if not name:
                return JsonResponse({"status": False, "message": "名称不能为空"}, status=400)
            api.rename_web_group(group_id, name)
            g.name = name

        return JsonResponse({"status": True, "group": _web_group_payload(g)})

    elif request.method == "DELETE":
        api.delete_web_group(group_id)
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def batch_move_web_groups(request):
    """POST /api/elements/web-groups/batch-move/ — Batch move groups to a target parent."""
    from .models import WebGroup

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    group_ids = data.get("group_ids") or []
    if not group_ids:
        return JsonResponse({"status": False, "message": "group_ids 不能为空"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0", "__root__"):
        parent_id = None

    if parent_id:
        try:
            parent = WebGroup.objects.get(pk=parent_id)
            if not parent.is_folder:
                return JsonResponse({"status": False, "message": "目标必须是目录"}, status=400)
        except WebGroup.DoesNotExist:
            return JsonResponse({"status": False, "message": "目标分组不存在"}, status=404)

    api.batch_move_web_groups(group_ids, parent_id)
    return JsonResponse({"status": True, "moved": len(group_ids)})


# ── Web Page Flow CRUD ──


@csrf_exempt
def web_flows_handler(request):
    """GET/POST /api/elements/web-flows/ — List or create web page flows."""
    from .models import WebElement, WebGroup, WebPageFlow

    if request.method == "GET":
        flows = WebPageFlow.objects.select_related(
            "from_group", "to_group", "trigger_element"
        ).order_by("-created_at")
        result = [
            {
                "id": f.id,
                "from_group_id": f.from_group_id,
                "to_group_id": f.to_group_id,
                "trigger_element_id": f.trigger_element_id,
                "trigger_action": f.trigger_action,
                "created_at": str(f.created_at),
                "from_label": f.from_group.name if f.from_group_id else "",
                "to_label": f.to_group.name if f.to_group_id else "",
                "trigger_name": f.trigger_element.name if f.trigger_element_id else "",
            }
            for f in flows
        ]
        return JsonResponse({"status": True, "flows": result})

    elif request.method == "POST":
        data = json.loads(request.body)
        from_id = data.get("from_group_id")
        to_id = data.get("to_group_id")
        if not from_id or not to_id:
            return JsonResponse(
                {"status": False, "message": "from_group_id 和 to_group_id 必填"}, status=400
            )

        # Validate both IDs are WebGroup (not Android Page)
        from .models import WebGroup

        try:
            from_g = WebGroup.objects.get(pk=from_id)
            to_g = WebGroup.objects.get(pk=to_id)
        except WebGroup.DoesNotExist:
            return JsonResponse(
                {"status": False, "message": "分组不存在，只能使用 Web 元素分组（el_web_groups）"},
                status=400,
            )

        if from_g.is_folder or to_g.is_folder:
            return JsonResponse(
                {
                    "status": False,
                    "message": "目录节点不能作为流的端点，请选择具体的页面（非目录）",
                },
                status=400,
            )

        trigger_id = data.get("trigger_element_id")
        if trigger_id:
            try:
                trigger_el = WebElement.objects.get(pk=trigger_id)
                if trigger_el.group_id not in (from_id, to_id):
                    return JsonResponse(
                        {"status": False, "message": "触发元素必须属于源页面或目标页面"}, status=400
                    )
            except WebElement.DoesNotExist:
                return JsonResponse({"status": False, "message": "触发元素不存在"}, status=400)

        api.create_web_page_flow(
            from_g,
            to_g,
            trigger_element_id=trigger_id,
            trigger_action=data.get("trigger_action", "click"),
        )
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def delete_web_flow(request, flow_id):
    """DELETE /api/elements/web-flows/{id}/."""

    api.delete_web_page_flow(flow_id)
    return JsonResponse({"status": True})


# ── API Group CRUD ──


def _api_group_payload(g):
    children = getattr(g, "children", None)
    child_count = children.count() if children is not None else 0
    return {
        "id": g.id,
        "name": g.name,
        "parent_id": g.parent_id,
        "is_folder": g.is_folder,
        "sort_order": g.sort_order,
        "endpoint_count": getattr(g, "_endpoint_count", 0),
        "child_count": child_count,
        "created_at": str(g.created_at),
    }


def list_api_groups(request):
    """GET /api/elements/api-groups/ — Flat list of all groups with endpoint_count."""
    from django.db.models import Count

    from .models import ApiGroup

    groups = list(
        ApiGroup.objects.annotate(_endpoint_count=Count("endpoints")).order_by("sort_order", "name")
    )

    return JsonResponse(
        {
            "status": True,
            "groups": [_api_group_payload(g) for g in groups],
        }
    )


@csrf_exempt
def create_api_group(request):
    """POST /api/elements/api-groups/create/ — Create a group or folder."""
    from .models import ApiGroup

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "分组名称必填"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None

    if parent_id:
        try:
            parent = ApiGroup.objects.get(pk=parent_id)
            if not parent.is_folder:
                return JsonResponse(
                    {"status": False, "message": "只能将分组添加在目录下"}, status=400
                )
        except ApiGroup.DoesNotExist:
            return JsonResponse({"status": False, "message": "父级分组不存在"}, status=404)

    is_folder = bool(data.get("is_folder", False))

    try:
        g = api.create_api_group(
            name,
            parent_id=parent_id,
            is_folder=is_folder,
            sort_order=data.get("sort_order", 0),
        )
    except Exception as e:
        return JsonResponse({"status": False, "message": f"创建失败: {e}"}, status=500)

    return JsonResponse({"status": True, "group": _api_group_payload(g)})


@csrf_exempt
def api_group_detail(request, group_id):
    """PUT/DELETE /api/elements/api-groups/{id}/ — Rename or delete a group."""
    from .models import ApiGroup

    try:
        g = ApiGroup.objects.get(id=group_id)
    except ApiGroup.DoesNotExist:
        return JsonResponse({"status": False, "message": "分组不存在"}, status=404)

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

        if "name" in data:
            name = data["name"].strip()
            if not name:
                return JsonResponse({"status": False, "message": "名称不能为空"}, status=400)
            api.rename_api_group(group_id, name)
            g.name = name

        return JsonResponse({"status": True, "group": _api_group_payload(g)})

    elif request.method == "DELETE":
        api.delete_api_group(group_id)
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def batch_move_api_groups(request):
    """POST /api/elements/api-groups/batch-move/ — Batch move groups to a target parent."""
    from .models import ApiGroup

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    group_ids = data.get("group_ids") or []
    if not group_ids:
        return JsonResponse({"status": False, "message": "group_ids 不能为空"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0", "__root__"):
        parent_id = None

    if parent_id:
        try:
            parent = ApiGroup.objects.get(pk=parent_id)
            if not parent.is_folder:
                return JsonResponse({"status": False, "message": "目标必须是目录"}, status=400)
        except ApiGroup.DoesNotExist:
            return JsonResponse({"status": False, "message": "目标分组不存在"}, status=404)

    api.batch_move_api_groups(group_ids, parent_id)
    return JsonResponse({"status": True, "moved": len(group_ids)})


# ── API Endpoint CRUD ──


def _api_endpoint_payload(e):
    return {
        "id": e.id,
        "name": e.name,
        "method": e.method,
        "url": e.url,
        "headers": e.headers,
        "request_body_schema": e.request_body_schema,
        "response_body_schema": e.response_body_schema,
        "description": e.description,
        "tags": e.tags,
        "is_test_point": e.is_test_point,
        "group_id": e.group_id,
        "created_at": str(e.created_at),
        "updated_at": str(e.updated_at),
    }


def list_api_endpoints(request):
    """GET /api/elements/api-endpoints/ — List API endpoints with search."""
    from .models import ApiEndpoint

    qs = ApiEndpoint.objects.all()

    search = request.GET.get("search", "").strip()
    if search:
        from django.db.models import Q

        qs = qs.filter(
            Q(name__icontains=search)
            | Q(url__icontains=search)
            | Q(description__icontains=search)
            | Q(tags__icontains=search)
        )

    method = request.GET.get("method", "").strip().upper()
    if method:
        qs = qs.filter(method=method)

    is_test_point = request.GET.get("is_test_point")
    if is_test_point is not None:
        qs = qs.filter(is_test_point=is_test_point in ("1", "true"))

    group_id = request.GET.get("group_id")
    if group_id is not None:
        if group_id == "" or group_id == "null":
            qs = qs.filter(group__isnull=True)
        else:
            try:
                qs = qs.filter(group_id=int(group_id))
            except (ValueError, TypeError):
                pass

    qs = qs.order_by("-updated_at")
    return JsonResponse(
        {"status": True, "endpoints": [_api_endpoint_payload(e) for e in qs], "total": qs.count()}
    )


@csrf_exempt
def create_api_endpoint(request):
    """POST /api/elements/api-endpoints/ — Create API endpoint."""

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "接口名称必填"}, status=400)
    method = data.get("method", "GET").upper()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        return JsonResponse({"status": False, "message": "无效的请求方法"}, status=400)
    url = data.get("url", "").strip()
    if not url:
        return JsonResponse({"status": False, "message": "接口 URL 必填"}, status=400)

    try:
        group_id = data.get("group_id")
        group = None
        if group_id is not None and group_id != "":
            from .models import ApiGroup

            try:
                group = ApiGroup.objects.get(id=int(group_id))
            except (ApiGroup.DoesNotExist, ValueError, TypeError):
                pass

        el = api.create_api_endpoint(
            group,
            name,
            method,
            url,
            headers=data.get("headers") or {},
            request_body_schema=data.get("request_body_schema") or {},
            response_body_schema=data.get("response_body_schema") or {},
            description=data.get("description", ""),
            tags=data.get("tags", ""),
            is_test_point=bool(data.get("is_test_point", False)),
        )
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)
    return JsonResponse({"status": True, "endpoint": _api_endpoint_payload(el)})


@csrf_exempt
def api_endpoint_detail(request, el_id):
    """PUT/DELETE /api/elements/api-endpoints/{id}/."""
    from .models import ApiEndpoint

    try:
        e = ApiEndpoint.objects.get(id=el_id)
    except ApiEndpoint.DoesNotExist:
        return JsonResponse({"status": False, "message": "接口不存在"}, status=404)

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"status": False, "message": "invalid JSON"}, status=400)

        updates = dict(data)
        if "is_test_point" in updates:
            updates["is_test_point"] = bool(updates["is_test_point"])
        if "group_id" in updates:
            gid = updates.pop("group_id")
            if gid in (None, "", "null"):
                updates["group"] = None
            else:
                from .models import ApiGroup

                try:
                    updates["group"] = ApiGroup.objects.get(id=int(gid))
                except (ApiGroup.DoesNotExist, ValueError, TypeError):
                    updates.pop("group", None)

        e = api.update_api_endpoint(el_id, updates)
        return JsonResponse({"status": True, "endpoint": _api_endpoint_payload(e)})

    elif request.method == "DELETE":
        api.delete_api_endpoint(el_id)
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


# ── 快照导入（v7.2：供设备检查器 / AI 保存工具调用）──


@csrf_exempt
def import_snapshot(request):
    """POST /api/elements/pages/import-snapshot — 快照导入（检查器 / AI 保存工具）。

    Body: { page_label, folder_path?, package?, activity?, screenshot_path?,
            ocr_json?, snapshot_id?, elements[] }
    响应统一信封 {status, data} / {status, message}（新端点新契约）。
    """
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON 请求体"}, status=400)
    try:
        result = api.import_snapshot_page(
            page_label=(body.get("page_label") or "").strip(),
            folder_path=(body.get("folder_path") or "").strip(),
            package=body.get("package", ""),
            activity=body.get("activity", ""),
            screenshot_path=body.get("screenshot_path", ""),
            ocr_json=body.get("ocr_json"),
            snapshot_id=body.get("snapshot_id"),
            elements=body.get("elements") or [],
        )
        return JsonResponse({"status": True, "data": result})
    except api.ImportConflictError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=409)
    except ValueError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=400)
    except Exception:
        logger.exception("import_snapshot failed")
        return JsonResponse({"status": False, "message": "导入失败"}, status=500)
