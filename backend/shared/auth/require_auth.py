import asyncio

from functools import wraps

from django.http import JsonResponse


def require_auth(view_func):
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
