"""case-manager lock & visibility endpoints — generalized across all three case types."""

import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api_lock import get_case_for_lock
from .views_helpers import resolve_username as _resolve_username

EDIT_LOCK_TIMEOUT_SECONDS = 1800  # 30 min — release if user is idle


@csrf_exempt
def acquire_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/lock — 获取用例编辑锁。

    成功 → 200 {ok, editing_by, editing_since}
    已被他人锁定 → 423 Locked {ok, error, editing_by, editing_since}
    用例不存在 → 404
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    case = get_case_for_lock(case_id)
    if case is None:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    now = datetime.now()

    # Permission check: deny non-authorized users
    if case.created_by != current_user:
        if case.permission == "readonly":
            return JsonResponse({"ok": False, "error": "此用例为只读模式，仅创建者可编辑"}, status=423)
        if case.permission == "restricted":
            editors = json.loads(case.permitted_editors or "[]")
            if current_user not in editors:
                return JsonResponse({"ok": False, "error": "此用例仅限指定用户编辑"}, status=423)

    # Already locked by someone else?
    if case.editing_by and case.editing_by != current_user:
        if case.editing_since:
            elapsed = (now - case.editing_since).total_seconds()
            if elapsed < EDIT_LOCK_TIMEOUT_SECONDS:
                return JsonResponse({
                    "ok": False,
                    "error": f"用例正被 {case.editing_by} 编辑中",
                    "editing_by": case.editing_by,
                    "editing_since": str(case.editing_since),
                }, status=423)

    # Acquire or refresh lock
    case.editing_by = current_user
    case.editing_since = now
    case.save(update_fields=["editing_by", "editing_since"])

    return JsonResponse({
        "ok": True,
        "editing_by": current_user,
        "editing_since": now.isoformat(),
        "created_by": case.created_by,
    })


@csrf_exempt
def release_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/unlock — 释放编辑锁。

    force=true 时：创建者可以强制踢出其他编辑者。
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    case = get_case_for_lock(case_id)
    if case is None:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    force = body.get("force", False)

    if force:
        if case.created_by and case.created_by != current_user:
            return JsonResponse({
                "ok": False,
                "error": "只有用例创建者可以强制解除编辑锁",
            }, status=403)
        case.editing_by = ""
        case.editing_since = None
        case.save(update_fields=["editing_by", "editing_since"])
        return JsonResponse({"ok": True, "force_unlocked": True})

    # Normal unlock: only the lock holder or creator can release
    if case.editing_by and case.editing_by != current_user and case.created_by != current_user:
        return JsonResponse({
            "ok": False,
            "error": "只有编辑者或创建者可以释放编辑锁",
        }, status=403)

    if not case.editing_by:
        return JsonResponse({"ok": True, "already_unlocked": True})

    case.editing_by = ""
    case.editing_since = None
    case.save(update_fields=["editing_by", "editing_since"])
    return JsonResponse({"ok": True, "released": True})


@csrf_exempt
def case_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-lock — 创建者锁定用例（他人只读）。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    case = get_case_for_lock(case_id)
    if case is None:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以锁定用例"}, status=403)

    case.locked = True
    case.save(update_fields=["locked"])
    return JsonResponse({"ok": True, "locked": True})


@csrf_exempt
def case_unlock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-unlock — 创建者解除用例锁。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    case = get_case_for_lock(case_id)
    if case is None:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以解除锁定"}, status=403)

    if not case.locked:
        return JsonResponse({"ok": True, "already_unlocked": True})

    case.locked = False
    case.save(update_fields=["locked"])
    return JsonResponse({"ok": True, "unlocked": True})


@csrf_exempt
def set_visibility(request, case_id):
    """POST /api/cases/definitions/{case_id}/visibility — 更新可见性（仅创建者）。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    case = get_case_for_lock(case_id)
    if case is None:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以修改可见性"}, status=403)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    case.visibility = body.get("visibility", "public")
    case.permitted_users = json.dumps(body.get("permitted_users", []), ensure_ascii=False)
    case.save(update_fields=["visibility", "permitted_users"])
    return JsonResponse({"ok": True, "visibility": case.visibility})
