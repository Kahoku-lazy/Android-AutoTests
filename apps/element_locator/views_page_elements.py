"""element-locator legacy 平铺端点 — 页面元素（单个增改 + 列取）（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api
from .models import Element, Page


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

    page = Page.objects.filter(pk=page_id).only("screenshot_path").first()
    if page is None:
        return JsonResponse({"status": False, "message": "page not found"}, status=404)

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
            "x": e.x,
            "y": e.y,
            "width": e.width,
            "height": e.height,
            "depth": e.depth,
            "index": e.index,
            "scrollable": e.scrollable,
            "checked": e.checked,
            "thumbnail_path": e.thumbnail_path,
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
    return JsonResponse(
        {
            "status": True,
            "elements": result,
            "total": total,
            "screenshot_path": page.screenshot_path or "",
        }
    )


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
