"""DRF authentication bridge — reuses the existing PyJWT verify_token().

This module provides a DRF ``BaseAuthentication`` subclass that delegates
to ``shared.auth.jwt_auth.verify_token()``, the same function used by the
Django middleware (``gateway.middleware.JWTAuthenticationMiddleware``).

The two authentication paths coexist during the DRF migration:
  - Middleware: continues to protect all existing plain-Django views
  - This class: protects new DRF ViewSets (opt-in via DEFAULT_AUTHENTICATION_CLASSES)
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .jwt_auth import verify_token


class JWTAuthentication(BaseAuthentication):
    """DRF authentication class that validates JWT Bearer tokens.

    Uses the project-wide ``verify_token()`` from ``shared.auth.jwt_auth``,
    which checks:
      - Token signature (HS256, shared SECRET_KEY)
      - Expiry (access token TTL)
      - Token type (must be "access")
      - Blacklist status (Redis-backed jti revocation)

    Returns the real ``auth.User`` resolved by the token's ``sub`` claim so
    DRF permission classes (``IsAdminUser``) and ``request.user.is_superuser``
    work. ``User.DoesNotExist`` (deleted user) is raised as 401.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        try:
            prefix, _, token = auth_header.partition(" ")
            if prefix.lower() != self.keyword.lower():
                return None
        except (AttributeError, ValueError):
            return None

        if not token:
            return None

        try:
            payload = verify_token(token, expected_type="access")
        except Exception as exc:
            msg = str(exc) if str(exc) else "Invalid or expired token"
            raise exceptions.AuthenticationFailed(msg)

        User = get_user_model()
        try:
            user = User.objects.get(pk=int(payload["sub"]))
        except (User.DoesNotExist, ValueError, TypeError):
            raise exceptions.AuthenticationFailed("用户不存在或已删除")
        return (user, token)

    def authenticate_header(self, request):
        return f'{self.keyword} realm="{settings.SECRET_KEY[:8]}…"'
