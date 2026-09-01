"""通用鉴权装饰器 — 检查 request.user_id（由 gateway JWT 中间件注入）。

shared 层：跨 App 可 import；与 gateway/middleware.py 同语义（中间件拦 /api/* 全局，
本装饰器供裸 Django view 做防御性二次检查）。
"""

import asyncio

from functools import wraps

from django.http import JsonResponse


def require_auth(view_func):
    """Reject unauthenticated requests (request.user_id must be set by middleware).

    Supports both sync and async Django views. When wrapping an async view,
    returns an async wrapper that properly awaits the view function.
    """

    if asyncio.iscoroutinefunction(view_func):

        @wraps(view_func)
        async def async_wrapper(request, *args, **kwargs):
            if not getattr(request, "user_id", None):
                return JsonResponse({"status": False, "message": "Unauthorized"}, status=401)
            return await view_func(request, *args, **kwargs)

        return async_wrapper

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, "user_id", None):
            return JsonResponse({"status": False, "message": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper


def require_superuser(view_func):
    """仅超级管理员可访问（读 request.user_id → User.is_superuser）。

    Supports both sync and async Django views, mirroring ``require_auth``.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def _is_superuser(request) -> bool:
        uid = getattr(request, "user_id", None)
        if not uid:
            return False
        try:
            return User.objects.filter(pk=int(uid), is_superuser=True).exists()
        except (ValueError, TypeError):
            return False

    if asyncio.iscoroutinefunction(view_func):

        @wraps(view_func)
        async def async_wrapper(request, *args, **kwargs):
            if not _is_superuser(request):
                return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
            return await view_func(request, *args, **kwargs)

        return async_wrapper

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _is_superuser(request):
            return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper
