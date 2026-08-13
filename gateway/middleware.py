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

# Paths that do NOT require authentication
PUBLIC_PREFIXES = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/runner/step-screenshots/",  # img src cannot send Authorization header
    "/api/ai/tools/",  # AgentScope internal service-to-service
    "/admin/",
    "/static/",
    "/media/",
    "/api/docs",
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

        return self.get_response(request)
