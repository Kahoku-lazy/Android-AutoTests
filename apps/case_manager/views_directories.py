"""case-manager directory endpoints — tree, CRUD, batch-move, permissions."""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api_directories import (
    batch_move_items,
    create_directory,
    delete_directory,
    get_directory_tree,
    update_directory,
)
from .models import CaseDirectory
from .views_helpers import resolve_username as _resolve_username

logger = logging.getLogger(__name__)


def directory_list(request):
    """GET /api/cases/directories — Return full directory tree."""
    if request.method == "GET":
        case_type = request.GET.get("case_type")
        tree = get_directory_tree(case_type=case_type or None)
        return JsonResponse({"status": True, "tree": tree})
    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def directory_create(request):
    """POST /api/cases/directories/create — Create a directory."""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)
    ok, result = create_directory(
        name=data.get("name", ""),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0),
        created_by=_resolve_username(getattr(request, "user_id", None)),
        case_type=data.get("case_type", "ui_automation"),
    )
    if ok:
        return JsonResponse({"status": True, "directory": result})
    return JsonResponse({"status": False, "message": result}, status=400)


@csrf_exempt
def directory_detail(request, dir_id):
    """POST /api/cases/directories/{id} — update or delete."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)
        action = data.get("action", "update")
        if action == "delete":
            ok, result = delete_directory(
                dir_id,
                deleted_by=_resolve_username(getattr(request, "user_id", None)),
            )
        else:
            ok, result = update_directory(
                dir_id,
                name=data.get("name"),
                parent_id=data.get("parent_id"),
                sort_order=data.get("sort_order"),
            )
        if ok:
            return JsonResponse({"status": True, "result": result})
        status = 409 if isinstance(result, dict) else 400
        return JsonResponse(
            {
                "status": False,
                "message": result
                if isinstance(result, str)
                else result.get("message", str(result)),
            },
            status=status,
        )
    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def directory_batch_move(request):
    """POST /api/cases/directories/batch-move — Batch move cases/directories."""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)
    items = data.get("items", [])
    target_id = data.get("target_directory_id")
    if not isinstance(items, list) or not items:
        return JsonResponse({"status": False, "message": "items 必须是非空数组"}, status=400)
    if target_id is None:
        return JsonResponse(
            {"status": False, "message": "target_directory_id 是必填项"}, status=400
        )
    result = batch_move_items(items, target_id)
    return JsonResponse({"status": True, **result})


@csrf_exempt
def directory_permission(request, dir_id):
    """POST /api/cases/directories/{dir_id}/permission — 更新目录权限（仅创建者）。"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, "user_id", None))
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    try:
        d = CaseDirectory.objects.only("id", "created_by").get(id=dir_id)
    except CaseDirectory.DoesNotExist:
        return JsonResponse({"status": False, "message": "目录不存在"}, status=404)

    if not d.created_by or d.created_by != current_user:
        return JsonResponse({"status": False, "message": "只有目录创建者可以修改权限"}, status=403)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    d.allow_create = body.get("allow_create", True)
    d.allow_delete = body.get("allow_delete", False)
    d.save(update_fields=["allow_create", "allow_delete"])
    return JsonResponse({"status": True})
