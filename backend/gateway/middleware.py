"""
模块功能：➡️ Gateway middleware — JWT authentication, logging, CORS. 🏁
Python 调试：➡️ python -m backend.gateway.middleware 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/ai_assistant/api/test_roles.py: 覆盖本模块
2. tests/arch/unit/test_auth_frontend_contract.py: 同上
🏁
"""

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

# Paths that do NOT require JWT authentication
PUBLIC_PREFIXES = [
    # 登录类：必须公开
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    # 后台与静态资源
    "/admin/",
    "/static/",
    "/media/",
    # API 文档面：有意公开（便于外部联调），无敏感数据
    "/api/schema/",  # drf-spectacular OpenAPI schema
    "/api/swagger/",  # drf-spectacular Swagger UI
]


# 停机排空端点：只允许本机回环调用（run.py stop 使用），因此不要求 JWT。
DRAIN_PATH = "/api/system/drain/"
_LOOPBACK_ADDRS = {"127.0.0.1", "::1"}

# 停用或已注销账号的专用拒绝。前端靠 code 与普通 401 区分，不走续期。
ACCOUNT_DISABLED_CODE = "account_disabled"
ACCOUNT_DISABLED_MESSAGE = "你的账号已被超管停用，10 秒后将退出登录"


def _is_public(path: str) -> bool:
    """Check if a request path is publicly accessible without JWT."""
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_log_ticket(request) -> bool:
    """助手报告只在带一次性 ticket 时免登录头。列表仍要登录。"""
    path = request.path
    return (
        request.method == "GET"
        and path.startswith("/api/ai/assistants/threads/")
        and "/logs/" in path
        and bool(request.GET.get("ticket"))
    )


def _is_loopback(addr: str) -> bool:
    """来源地址是否为 IPv4/IPv6 回环。"""
    return str(addr or "").strip() in _LOOPBACK_ADDRS


class JWTAuthenticationMiddleware:
    """Django middleware that validates JWT tokens on protected /api/ routes.

    Extracts user_id from Authorization: Bearer <token> header and attaches
    it to request.user_id.  Public paths (auth, admin, static) are skipped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Close expired database connections before each request to prevent
        # connection accumulation in long-running async/threaded environments.
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

        # 有效 JWT 的请求豁免 CSRF：浏览器无法跨站携带自定义 Authorization 头，
        # 因而不存在 CSRF 场景；CsrfViewMiddleware（排在本中间件之后）读取此标记。
        request._dont_enforce_csrf_checks = True

        return self.get_response(request)


def _disabled_account_response(user_id) -> JsonResponse | None:
    """停用或已注销的账号返回专用 403；查库失败时放行，避免抖动踢全员。

    Args:
        user_id: 令牌里的账号主键。

    Returns:
        专用拒绝；账号仍启用时返回 None。
    """
    try:
        pk = int(str(user_id))
    except (TypeError, ValueError):
        return None
    try:
        active = get_user_model().objects.filter(pk=pk).values_list("is_active", flat=True).first()
    except DatabaseError as exc:
        logger.error("停用判定失败，放行请求: %s", exc)
        return None
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
