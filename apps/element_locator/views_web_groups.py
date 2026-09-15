"""element-locator legacy 平铺端点 — Web 分组（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
def web_group_detail(request, group_id):
    """GET keep; PUT/DELETE → 410."""
    from .models import WebGroup

    if request.method in ("PUT", "PATCH", "DELETE"):
        return JsonResponse(
            {"status": False, "message": "分组树写接口已停用，请改用项目目录 API"},
            status=410,
        )

    try:
        g = WebGroup.objects.get(id=group_id)
    except WebGroup.DoesNotExist:
        return JsonResponse({"status": False, "message": "分组不存在"}, status=404)

    if request.method == "GET":
        return JsonResponse({"status": True, "group": _web_group_payload(g)})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
