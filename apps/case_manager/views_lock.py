"""case-manager lock & visibility endpoints — generalized across all case types.

写操作走 api_lock.py，本文件只做 request 解析 + 状态码映射。
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api_lock
from .views_helpers import resolve_username as _resolve_username


def _current_user(request):
    return _resolve_username(getattr(request, "user_id", None))


def _respond(ok, result):
    """将 api_lock 的 (ok, result) 转为 JsonResponse。"""
    if ok:
        return JsonResponse({"status": True, **result})
    code = result.get("code", 400)
    payload = {"status": False, **result}
    payload.pop("code", None)
    return JsonResponse(payload, status=code)


@csrf_exempt
def acquire_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/lock — 获取用例编辑锁。

    成功 → 200 {status, editing_by, editing_since, created_by}
    已被他人锁定 → 423；用例不存在 → 404
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _current_user(request)
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    return _respond(*api_lock.acquire_edit_lock(case_id, current_user))


@csrf_exempt
def release_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/unlock — 释放编辑锁。

    force=true 时：创建者可以强制踢出其他编辑者。
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _current_user(request)
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    return _respond(
        *api_lock.release_edit_lock(case_id, current_user, force=body.get("force", False))
    )


@csrf_exempt
def case_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-lock — 创建者锁定用例（他人只读）。"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _current_user(request)
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    return _respond(*api_lock.set_case_lock(case_id, current_user, locked=True))


@csrf_exempt
def case_unlock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-unlock — 创建者解除用例锁。"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _current_user(request)
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    return _respond(*api_lock.set_case_lock(case_id, current_user, locked=False))


@csrf_exempt
def set_visibility(request, case_id):
    """POST /api/cases/definitions/{case_id}/visibility — 更新可见性（仅创建者）。"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)

    current_user = _current_user(request)
    if not current_user:
        return JsonResponse({"status": False, "message": "未登录"}, status=401)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    return _respond(
        *api_lock.set_case_visibility(
            case_id,
            current_user,
            visibility=body.get("visibility", "public"),
            permitted_users=body.get("permitted_users"),
            permitted_editors=body.get("permitted_editors"),
            permission=body.get("permission"),
        )
    )
