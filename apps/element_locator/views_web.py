"""element-locator legacy 平铺端点 — Web 元素（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api

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
            directory_id=_optional_directory_id(data, project_code="web"),
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
