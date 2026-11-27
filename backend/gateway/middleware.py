import logging

from django.contrib.auth import get_user_model
from django.db import DatabaseError, close_old_connections
from django.http import JsonResponse

from backend.shared.auth.jwt_auth import verify_token

logger = logging.getLogger("gateway")

RETIRED_AUTH_PATHS = {
    "/api/ai/auth/login",
    "/api/ai/auth/register",
    "/api/ai/auth/refresh",
    "/api/ai/auth/logout",
    "/api/ai/auth/me",
}

PUBLIC_PREFIXES = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/admin/",
    "/static/",
    "/media/",
    "/api/schema/",
    "/api/swagger/",
]


DRAIN_PATH = "/api/system/drain/"
_LOOPBACK_ADDRS = {"127.0.0.1", "::1"}

ACCOUNT_DISABLED_CODE = "account_disabled"
ACCOUNT_DISABLED_MESSAGE = "你的账号已被超管停用，10 秒后将退出登录"


def _is_public(path: str) -> bool:
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_log_ticket(request) -> bool:
    path = request.path
    return (
        request.method == "GET"
        and path.startswith("/api/ai/assistants/threads/")
        and "/logs/" in path
        and bool(request.GET.get("ticket"))
    )


def _is_loopback(addr: str) -> bool:
    return str(addr or "").strip() in _LOOPBACK_ADDRS


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        close_old_connections()

        path = request.path

        if path in RETIRED_AUTH_PATHS or _is_public(path) or _is_log_ticket(request):
            return self.get_response(request)

        if path == DRAIN_PATH and _is_loopback(request.META.get("REMOTE_ADDR", "")):
            return self.get_response(request)

        if not path.startswith("/api/"):
            return self.get_response(request)

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"status": False, "message": "请先登录"},
                status=401,
            )

        token = auth_header[7:]
        try:
            payload = verify_token(token, expected_type="access")
            request.user_id = payload["sub"]
        except Exception as e:
            logger.warning(f"JWT verify failed for {path}: {e}")
            return JsonResponse(
                {"status": False, "message": "登录已过期或令牌无效"},
                status=401,
            )

        disabled = _disabled_account_response(request.user_id)
        if disabled is not None:
            return disabled

        request._dont_enforce_csrf_checks = True

        return self.get_response(request)


def _disabled_account_response(user_id) -> JsonResponse | None:
    try:
        pk = int(str(user_id))
    except (TypeError, ValueError):
        return None
    try:
        active = get_user_model().objects.filter(pk=pk).values_list("is_active", flat=True).first()
    except DatabaseError as exc:
        logger.error("停用判定失败，放行请求: %s", exc)
        return None
    if active is None:
        return JsonResponse(
            {
                "status": False,
                "message": "登录已过期或令牌无效",
            },
            status=401,
        )
    if active is True:
        return None
    return JsonResponse(
        {
            "status": False,
            "message": ACCOUNT_DISABLED_MESSAGE,
            "code": ACCOUNT_DISABLED_CODE,
        },
        status=403,
    )
