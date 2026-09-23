"""element-locator legacy 平铺端点 — 页面元素批量添加（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api
from .element_fields import CREATE_FIELDS, normalize_element_fields
from .models import Page


@csrf_exempt
def batch_add_elements(request, page_id):
    """POST /api/elements/pages/{page_id}/elements/batch — Batch save elements.

    Body（收敛口径）: { elements: [{ alias, text_val?, primary_xpath?, resource_id?,
            bounds?, notes?, is_test_point? }] }

    逐条按与工作台「新增一行」相同的字段集规整（越界字段计入 errors 并跳过），
    命中同页 (resource_id, bounds) 的按 upsert 更新。
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

    # 逐条按收敛后的新增字段集规整（与工作台「新增一行」同一口径）
    prepared = []
    for item in items:
        alias = str(item.get("alias") or "").strip()
        if not alias:
            skipped += 1
            continue
        try:
            fields = normalize_element_fields({**item, "alias": alias}, CREATE_FIELDS)
        except ValueError as exc:
            errors.append(f"{alias}: {exc}")
            skipped += 1
            continue
        prepared.append(
            {
                "alias": alias,
                "resource_id": fields.get("resource_id", ""),
                "bounds": fields.get("bounds", ""),
                "fields": fields,
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
def batch_delete_elements(request):
    """POST /api/elements/items/batch-delete — 批量删除元素（原子）。

    Body: { ids: [int, ...] }；空集合 → 400，元素不存在 → 404（整批不落库）。
    """
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON 请求体"}, status=400)
    try:
        result = api.delete_elements(body.get("ids") or [])
    except LookupError as exc:
        return JsonResponse({"status": False, "message": str(exc)}, status=404)
    except ValueError as exc:
        return JsonResponse({"status": False, "message": str(exc)}, status=400)
    return JsonResponse({"status": True, "data": result})
