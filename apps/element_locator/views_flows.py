"""element-locator legacy 平铺端点 — 页面流（Android + Web）（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api
from .models import PageFlow

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
