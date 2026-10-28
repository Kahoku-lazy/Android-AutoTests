"""
平台认证接口：登录、注册、续期、登出、当前用户。

业务：
1. 登录：账号密码正确则发本次会话；账号或密码不对则拒绝进入。
2. 注册：校验通过则创建用户并直接登录；用户名已有则拒绝。
3. 续期：用续期凭证换新的访问凭证，仍属同一次登录。
4. 登出：作废这次登录的访问凭证和续期凭证；服务暂不可用时拒绝登出，请稍后重试。
5. 当前用户：返回账号，以及是否管理员。
"""

from typing import ClassVar

from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.auth.jwt_auth import (
    BlacklistUnavailableError,
    blacklist_token,
    create_access_token,
    create_token_pair,
    revoke_session,
    session_id_of,
    verify_token,
)

from . import api
from .serializers import LoginSerializer, RefreshSerializer, RegisterSerializer


class LoginView(APIView):
    """POST /api/auth/login — 账号密码正确则发本次会话。"""

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
    """POST /api/auth/register — 创建用户并直接登录。用户名已有则拒绝。"""

    permission_classes = [AllowAny]
    authentication_classes: ClassVar[list] = []

    @extend_schema(
        request=RegisterSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            # 409 只由写口的 ConflictError 产生（唯一性由写口保证），输入校验一律 400
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
    """POST /api/auth/refresh — 用续期凭证换新的访问凭证，仍属同一次登录。"""

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
            # 透传 sid：续期后的 access 仍属同一会话，登出时一并失效
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
    """POST /api/auth/logout — 作废这次登录。服务暂不可用时拒绝登出。"""

    permission_classes = [IsAuthenticated]

    # 仅读取 Authorization 头完成登出，不接收请求体
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return Response({})

        token = auth_header[7:]
        try:
            # 会话粒度：同一 sid 的 access 与 refresh 一起失效
            sid = session_id_of(token)
            if sid:
                revoke_session(sid)
            # 兜底：本变更部署前签发的令牌没有 sid，只能按 jti 吊销
            blacklist_token(token)
        except BlacklistUnavailableError:
            return Response(
                {"detail": "Redis 不可用，无法撤销令牌", "retry": True},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({})


class MeView(APIView):
    """GET /api/auth/me — 当前登录用户，含是否管理员。"""

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
                }
            }
        )


def _first_error(errors) -> str:
    """取出第一条给用户看的校验说明。"""
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
