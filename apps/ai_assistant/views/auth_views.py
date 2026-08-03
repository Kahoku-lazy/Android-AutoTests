"""Auth endpoints — login, register, refresh, logout, me."""

import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from shared.auth.jwt_auth import (
    BlacklistUnavailableError,
    blacklist_token,
    create_access_token,
    create_token_pair,
    verify_token,
)

from ..decorators import require_auth


@csrf_exempt
def login(request):
    """POST /api/ai/auth/login — authenticate and return JWT token pair.

    Validation returns 400 with specific Chinese messages for each failure mode:
      - Both fields empty → "请输入用户名和密码"
      - Username empty       → "请输入用户名"
      - Password empty       → "请输入密码"
      - Username whitespace  → "用户名不能为空白"
      - Username too long    → "用户名过长"
      - Auth failure         → "用户名或密码错误" (401, deliberate — does not
        reveal whether the username exists)
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "请求格式错误"}, status=400)

    username = data.get("username", "")
    password = data.get("password", "")

    # ── 逐层校验，返回对应中文错误 ──
    if not username and not password:
        return JsonResponse(
            {"ok": False, "error": "请输入用户名和密码"},
            status=400,
        )
    if not username:
        return JsonResponse(
            {"ok": False, "error": "请输入用户名"},
            status=400,
        )
    if not password:
        return JsonResponse(
            {"ok": False, "error": "请输入密码"},
            status=400,
        )
    if not username.strip():
        return JsonResponse(
            {"ok": False, "error": "用户名不能为空白"},
            status=400,
        )
    if len(username) > 150:
        return JsonResponse(
            {"ok": False, "error": "用户名过长，最多150个字符"},
            status=400,
        )

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse(
            {"ok": False, "error": "用户名或密码错误"},
            status=401,
        )

    tokens = create_token_pair(str(user.id))
    return JsonResponse(
        {
            "ok": True,
            **tokens,
            "user": {"id": user.id, "username": user.username},
        }
    )


@csrf_exempt
def register(request):
    """POST /api/ai/auth/register — create a new user.

    Validation returns 400 with specific Chinese messages:
      - Both fields empty → "请输入用户名和密码"
      - Username empty       → "请输入用户名"
      - Password empty       → "请输入密码"
      - Duplicate username   → "用户名已存在" (409)
    """
    from django.contrib.auth.models import User

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "请求格式错误"}, status=400)

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username and not password:
        return JsonResponse(
            {"ok": False, "error": "请输入用户名和密码"},
            status=400,
        )
    if not username:
        return JsonResponse(
            {"ok": False, "error": "请输入用户名"},
            status=400,
        )
    if not password:
        return JsonResponse(
            {"ok": False, "error": "请输入密码"},
            status=400,
        )
    if len(username) < 3:
        return JsonResponse(
            {"ok": False, "error": "用户名至少 3 个字符"},
            status=400,
        )
    if len(username) > 20:
        return JsonResponse(
            {"ok": False, "error": "用户名最多 20 个字符"},
            status=400,
        )
    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"ok": False, "error": "用户名已存在"},
            status=409,
        )

    user = User.objects.create_user(username=username, password=password)
    tokens = create_token_pair(str(user.id))
    return JsonResponse(
        {
            "ok": True,
            **tokens,
            "user": {"id": user.id, "username": user.username},
        }
    )


@csrf_exempt
def refresh_token(request):
    """POST /api/ai/auth/refresh — refresh access token using refresh token."""
    data = json.loads(request.body)
    token = data.get("refresh_token", "")
    try:
        payload = verify_token(token, expected_type="refresh")
        if payload.get("type") != "refresh":
            return JsonResponse({"ok": False, "error": "Not a refresh token"}, status=401)
        new_access = create_access_token(payload["sub"])
        return JsonResponse({"ok": True, "access_token": new_access, "token_type": "bearer"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=401)


@csrf_exempt
@require_auth
def logout(request):
    """POST /api/ai/auth/logout — blacklist the current token.

    Returns 503 if Redis is unavailable (token revocation cannot be persisted).
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        try:
            blacklist_token(auth_header[7:])
        except BlacklistUnavailableError as e:
            return JsonResponse(
                {
                    "ok": False,
                    "error": str(e),
                    "retry": True,
                },
                status=503,
            )
    return JsonResponse({"ok": True})


def me(request):
    """GET /api/ai/auth/me — return current user info from JWT."""
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return JsonResponse({"ok": False, "error": "Not authenticated"}, status=401)
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({"ok": True, "user": {"id": user.id, "username": user.username}})
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "User not found"}, status=404)
