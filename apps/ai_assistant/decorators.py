"""ai-assistant view decorators — authentication helpers."""

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
