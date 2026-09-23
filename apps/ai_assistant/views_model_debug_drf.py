"""单模型调试台（工具箱「模型调试」）— 角色只读配置 + 单角色调试对话。

GET  /api/ai/model-debug/<role>/       仅超管：该角色此刻生效的只读配置
POST /api/ai/model-debug/<role>/chat   仅超管：单角色调试对话（挂该角色真实工具子集）

装配复用 apps/ai_assistant/model_debug.py；对话挂真实工具、不挂 Skill、不落库。
需要设备的角色必须先在请求里给出可用设备 serial。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api, model_debug


def _require_superuser(request) -> str:
    """模型调试（读配置 + 对话）仅超级管理员可用。"""
    from .permissions import _is_superuser

    user_id = str(getattr(request, "user_id", "") or "")
    if not _is_superuser(user_id):
        raise PermissionDenied("Forbidden")
    return user_id


def _platform_agent_or_404():
    agent = api.get_platform_agent()
    if agent is None:
        raise NotFound("platform agent not found")
    return agent


class ModelDebugConfigAPIView(APIView):
    """GET /api/ai/model-debug/<role>/ — 该角色只读配置 + 技能/知识库归属（仅超管）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, role):
        _require_superuser(request)
        try:
            name = model_debug.normalize_role(role)
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc
        configs = model_debug.build_role_debug_configs(_platform_agent_or_404())
        return Response(
            {
                "agent_id": configs["agent_id"],
                "agent_name": configs["agent_name"],
                "role": next(item for item in configs["roles"] if item["role"] == name),
                "skills": configs["skills"],
                "knowledge": configs["knowledge"],
            }
        )


class ModelDebugChatAPIView(APIView):
    """POST /api/ai/model-debug/<role>/chat — 单角色调试对话（仅超管，超时 5 分钟）。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, role):
        user_id = _require_superuser(request)
        try:
            return Response(
                model_debug.run_role_chat(
                    _platform_agent_or_404(),
                    role,
                    str(request.data.get("text") or ""),
                    user_id=user_id,
                    serial=str(request.data.get("serial") or ""),
                )
            )
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc
