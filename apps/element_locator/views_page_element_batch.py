"""element-locator legacy 平铺端点 — 页面元素批量添加（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api
from .models import Page


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
