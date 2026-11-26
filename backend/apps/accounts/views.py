from typing import ClassVar

from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.accounts.api import user_revoked_before
from backend.shared.auth.jwt_auth import (
    BlacklistUnavailableError,
    blacklist_token,
    create_access_token,
    create_token_pair,
    revoke_session,
    session_id_of,
    verify_token,
)
from backend.shared.users import is_assistant_author, is_operator

from . import api
from .serializers import LoginSerializer, RefreshSerializer, RegisterSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: ClassVar[list] = []

    @extend_schema(
        request=LoginSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            msg = _first_error(ser.errors)
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

    @extend_schema(
        request=RegisterSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {"detail": _first_error(ser.errors)}, status=status.HTTP_400_BAD_REQUEST
            )

        data = ser.validated_data
        try:
            user = api.create_user(
                username=data["username"],
                password=data["password"],
                email=data["email"],
            )
        except api.ConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
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

    @extend_schema(
        request=RefreshSerializer,
        responses=OpenApiTypes.OBJECT,
    )
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
            if _refresh_blocked(payload):
                return Response(
                    {"detail": "刷新令牌无效或已过期"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            new_access = create_access_token(payload["sub"], sid=payload.get("sid"))
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

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return Response({})

        token = auth_header[7:]
        try:
            sid = session_id_of(token)
            if sid:
                revoke_session(sid)
            blacklist_token(token)
        except BlacklistUnavailableError:
            return Response(
                {"detail": "吊销服务不可用，请稍后重试", "retry": True},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
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
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                    "is_operator": is_operator(user.id),
                    "is_assistant_author": is_assistant_author(user.id),
                }
            }
        )


def _refresh_blocked(payload: dict) -> bool:
    try:
        user_id = int(str(payload.get("sub") or ""))
    except (TypeError, ValueError):
        return True
    user = User.objects.filter(pk=user_id).only("is_active").first()
    if user is None or not user.is_active:
        return True
    return user_revoked_before(user_id, int(payload.get("iat") or 0))


def _first_error(errors) -> str:
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
