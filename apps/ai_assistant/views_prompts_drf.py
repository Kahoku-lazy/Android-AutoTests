"""设备控制三角色系统提示词读写 + 历史存档（工具箱「设备提示词」来源）。

GET  /api/ai/device-prompts                          登录可读
POST /api/ai/device-prompts/update                   仅超管（archive=auto|permanent）
GET  /api/ai/device-prompt-archives/                 仅超管（历史列表）
GET  /api/ai/device-prompt-archives/<pk>/            仅超管（单份全文）
POST /api/ai/device-prompt-archives/<pk>/delete/     仅超管（删永久档）
POST /api/ai/device-prompt-archives/<pk>/restore/    仅超管（用该存档覆盖当前提示词）

写库经 api.py。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api
from .models import AIDevicePromptArchive


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


def _require_superuser(request) -> str:
    """历史存档相关端点一律仅超级管理员；返回操作者 user_id。"""
    from .permissions import _is_superuser

    user_id = _user_id(request)
    if not _is_superuser(user_id):
        raise PermissionDenied("Forbidden")
    return user_id


def _get_platform_agent_or_404():
    agent = api.get_platform_agent()
    if agent is None:
        raise NotFound("platform agent not found")
    return agent


def _get_archive_or_404(pk) -> AIDevicePromptArchive:
    try:
        return api.get_device_prompt_archive(pk)
    except (ValueError, AIDevicePromptArchive.DoesNotExist):
        raise NotFound("archive not found")


class DevicePromptsAPIView(APIView):
    """平台唯一智能体的设备控制三角色系统提示词。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(api.get_device_prompts(_get_platform_agent_or_404()))

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        user_id = _require_superuser(request)
        agent = _get_platform_agent_or_404()
        archive = str(request.data.get("archive") or AIDevicePromptArchive.KIND_AUTO).strip()
        try:
            return Response(
                api.update_device_prompts(agent, request.data, archive=archive, user_id=user_id)
            )
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc


class DevicePromptArchiveListAPIView(APIView):
    """GET /api/ai/device-prompt-archives/ — 历史存档列表（仅超管，不含正文）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_superuser(request)
        return Response({"items": api.list_device_prompt_archives(_get_platform_agent_or_404())})


class DevicePromptArchiveDetailAPIView(APIView):
    """GET /api/ai/device-prompt-archives/<pk>/ — 单份存档全文（仅超管）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        _require_superuser(request)
        return Response(api.read_device_prompt_archive(_get_archive_or_404(pk)))


class DevicePromptArchiveDeleteAPIView(APIView):
    """POST /api/ai/device-prompt-archives/<pk>/delete/ — 删除永久档（仅超管）。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        _require_superuser(request)
        archive = _get_archive_or_404(pk)
        try:
            api.delete_device_prompt_archive(archive)
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc
        return Response({"id": archive.id})


class DevicePromptArchiveRestoreAPIView(APIView):
    """POST /api/ai/device-prompt-archives/<pk>/restore/ — 用该存档覆盖当前提示词（仅超管）。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        user_id = _require_superuser(request)
        archive = _get_archive_or_404(pk)
        try:
            return Response(api.restore_device_prompt_from_archive(archive, user_id=user_id))
        except ValueError as exc:
            raise ValidationError({"message": str(exc)}) from exc
