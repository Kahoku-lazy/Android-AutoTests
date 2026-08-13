"""Platform auth APIViews — login / register / refresh / logout / me."""

from typing import ClassVar

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.auth.jwt_auth import (
    BlacklistUnavailableError,
    blacklist_token,
    create_access_token,
    create_token_pair,
    verify_token,
)

from . import api
from .serializers import LoginSerializer, RefreshSerializer, RegisterSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: ClassVar[list] = []

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            msg = _first_error(ser.errors)
            # 认证失败保持 401；其余校验 400
            code = (
                status.HTTP_401_UNAUTHORIZED
                if msg == "用户名或密码错误"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response({"detail": msg}, status=code)

        user = ser.validated_data["user"]
        tokens = create_token_pair(str(user.id))
        return Response(
            {
                **tokens,
                "user": {"id": user.id, "username": user.username},
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: ClassVar[list] = []

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            msg = _first_error(ser.errors)
            code = (
                status.HTTP_409_CONFLICT if msg == "用户名已存在" else status.HTTP_400_BAD_REQUEST
            )
            return Response({"detail": msg}, status=code)

        data = ser.validated_data
        user = api.create_user(
            username=data["username"],
            password=data["password"],
            email=data["email"],
        )
        tokens = create_token_pair(str(user["id"]))
        return Response(
            {
                **tokens,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                },
            }
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: ClassVar[list] = []

    def post(self, request):
        ser = RefreshSerializer(data=request.data)
        ser.is_valid(raise_exception=False)
        token = (ser.validated_data or {}).get("refresh_token") or request.data.get(
            "refresh_token", ""
        )
        try:
            payload = verify_token(token, expected_type="refresh")
            if payload.get("type") != "refresh":
                return Response(
                    {"detail": "令牌类型错误，需要刷新令牌"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            new_access = create_access_token(payload["sub"])
            return Response({"access_token": new_access, "token_type": "bearer"})
        except Exception as exc:
            msg = str(exc) or ""
            if "expected refresh" in msg or "Invalid token type" in msg:
                detail = "令牌类型错误，需要刷新令牌"
            else:
                detail = "刷新令牌无效或已过期"
            return Response(
                {"detail": detail},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            try:
                blacklist_token(auth_header[7:])
            except BlacklistUnavailableError:
                return Response(
                    {"detail": "Redis 不可用，无法撤销令牌", "retry": True},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        return Response({})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return Response(
                {"detail": "未登录"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = User.objects.filter(id=user_id).first()
        if user is None:
            return Response(
                {"detail": "用户不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"user": {"id": user.id, "username": user.username}})


def _first_error(errors) -> str:
    """Extract first user-facing message from DRF error dict/list."""
    if isinstance(errors, dict):
        non_field = errors.get("non_field_errors")
        if isinstance(non_field, list) and non_field:
            return str(non_field[0])
        for value in errors.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return "请求无效"
