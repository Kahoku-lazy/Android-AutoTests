"""element-locator legacy 平铺端点 — 页面元素（单个增改 + 列取）（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api
from .models import Element, Page


def _element_payload(el):
    """元素 payload —— 收敛口径：呈现字段 + 去重键（候选 XPath 与坐标分量不再返回）。"""
    return {
        "id": el.id,
        "page_id": el.page_id,
        "alias": el.alias,
        "text_val": el.text_val,
        "resource_id": el.resource_id,
        "bounds": el.bounds,
        "seq": el.seq,
        "primary_xpath": el.primary_xpath,
        "primary_stable": el.primary_stable,
        "thumbnail_path": el.thumbnail_path,
        "clickable": el.clickable,
        "long_clickable": el.long_clickable,
        "scrollable": el.scrollable,
        "checkable": el.checkable,
        "checked": el.checked,
        "enabled": el.enabled,
        "focusable": el.focusable,
        "is_test_point": el.is_test_point,
        "notes": el.notes,
        "created_at": str(el.created_at),
    }


@csrf_exempt
def add_element_to_page(request, page_id):
    """POST /api/elements/pages/{page_id}/elements — Manually add element to page.

    Body（收敛口径）: { alias, text_val?, primary_xpath?, notes?, is_test_point?,
                        resource_id?, bounds? }

    仅新增：命中同页既有 (resource_id, bounds) → 409；`alias` 必填、`resource_id` 与
    `bounds` 至少一个；越界字段或非法输入 → 400。
    """
    try:
        page = Page.objects.get(id=page_id)
    except Page.DoesNotExist:
        return JsonResponse({"status": False, "message": "页面不存在"}, status=404)
    if page.is_folder:
        return JsonResponse(
            {"status": False, "message": "目录节点不能添加元素，请选择子页面"}, status=400
        )

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON 请求体"}, status=400)

    try:
        element = api.create_element(page, data)
    except api.ConflictError as exc:
        return JsonResponse({"status": False, "message": exc.message}, status=409)
    except ValueError as exc:
        return JsonResponse({"status": False, "message": str(exc)}, status=400)
    return JsonResponse({"status": True, "element": _element_payload(element)})


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

    page = Page.objects.filter(pk=page_id).only("id").first()
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

    # 元素定位不再保存也不关联整屏截图，响应只给收敛后的元素字段（无候选 XPath、无截图路径）
    return JsonResponse(
        {
            "status": True,
            "elements": [_element_payload(e) for e in qs],
            "total": total,
        }
    )


@csrf_exempt
def update_element(request, el_id):
    """PUT /api/elements/items/{el_id} — 更新元素行可编辑字段。

    可写字段见 api.UPDATE_FIELDS（元素名称 / 文本 / 主定位 / 测试点）；越界字段与非法输入
    → 400，元素不存在 → 404。
    """
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON 请求体"}, status=400)

    try:
        api.update_element(el_id, data)
    except LookupError as exc:
        return JsonResponse({"status": False, "message": str(exc)}, status=404)
    except ValueError as exc:
        return JsonResponse({"status": False, "message": str(exc)}, status=400)
    return JsonResponse({"status": True})
