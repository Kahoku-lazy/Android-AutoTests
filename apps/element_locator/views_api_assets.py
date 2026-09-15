"""element-locator legacy 平铺端点 — API 分组与端点（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api

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
def api_group_detail(request, group_id):
    """GET keep; PUT/DELETE → 410."""
    from .models import ApiGroup

    if request.method in ("PUT", "PATCH", "DELETE"):
        return JsonResponse(
            {"status": False, "message": "分组树写接口已停用，请改用项目目录 API"},
            status=410,
        )

    try:
        g = ApiGroup.objects.get(id=group_id)
    except ApiGroup.DoesNotExist:
        return JsonResponse({"status": False, "message": "分组不存在"}, status=404)

    if request.method == "GET":
        return JsonResponse({"status": True, "group": _api_group_payload(g)})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


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
            directory_id=_optional_directory_id(data, project_code="api"),
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
