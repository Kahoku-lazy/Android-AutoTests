from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .jwt_auth import verify_token


class JWTAuthentication(BaseAuthentication):
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

        user_id = getattr(request, "user_id", "")
        if not user_id:
            try:
                payload = verify_token(token, expected_type="access")
            except Exception as exc:
                msg = str(exc) if str(exc) else "Invalid or expired token"
                raise exceptions.AuthenticationFailed(msg) from exc

            user_id = payload["sub"]

        User = get_user_model()
        try:
            user = User.objects.get(pk=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError) as exc:
            raise exceptions.AuthenticationFailed("用户不存在或已删除") from exc
        return (user, token)

    def authenticate_header(self, request):
        return f'{self.keyword} realm="api"'
