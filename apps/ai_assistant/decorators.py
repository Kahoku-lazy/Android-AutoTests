"""ai-assistant view decorators — authentication helpers."""

from functools import wraps

from django.http import JsonResponse


def require_auth(view_func):
    """Reject unauthenticated requests (request.user_id must be set by middleware)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, "user_id", None):
            return JsonResponse({"status": False, "message": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper
