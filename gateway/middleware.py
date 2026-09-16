"""Gateway middleware — JWT authentication, logging, CORS."""

import logging

from django.db import close_old_connections
from django.http import JsonResponse

from shared.auth.jwt_auth import verify_token

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
    # 工具网关：免 JWT（服务间），由 gateway.internal_token.InternalToolTokenMiddleware
    # 校验 X-Internal-Token；令牌未配置时一律 401（fail-closed）
    "/api/ai/tools/",
    # 后台与静态资源
    "/admin/",
    "/static/",
    "/media/",
    # API 文档面：有意公开（便于外部联调），无敏感数据
    "/api/schema/",  # drf-spectacular OpenAPI schema
    "/api/swagger/",  # drf-spectacular Swagger UI
]


def _is_public(path: str) -> bool:
    """Check if a request path is publicly accessible without JWT."""
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


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

        if path in RETIRED_AUTH_PATHS or _is_public(path):
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

        # 有效 JWT 的请求豁免 CSRF：浏览器无法跨站携带自定义 Authorization 头，
        # 因而不存在 CSRF 场景；CsrfViewMiddleware（排在本中间件之后）读取此标记。
        request._dont_enforce_csrf_checks = True

        return self.get_response(request)
