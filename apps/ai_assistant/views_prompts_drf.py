"""设备控制三角色系统提示词读写（工具箱「设备提示词」来源）。

GET  /api/ai/device-prompts         登录可读
POST /api/ai/device-prompts/update  仅超级管理员
写库经 api.py。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


class DevicePromptsAPIView(APIView):
    """平台唯一智能体的设备控制三角色系统提示词。"""

    def _get_agent_or_404(self):
        agent = api.get_platform_agent()
        if agent is None:
            raise NotFound("platform agent not found")
        return agent

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        agent = self._get_agent_or_404()
        return Response(api.get_device_prompts(agent))

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        from .permissions import _is_superuser

        if not _is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        agent = self._get_agent_or_404()
        try:
            return Response(api.update_device_prompts(agent, request.data))
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc
