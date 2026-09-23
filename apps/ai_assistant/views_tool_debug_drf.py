"""平台工具调试（JWT）：读 schema + 真实调用。

GET  /api/ai/platform-tools/<name>         登录可读入参 schema（设备候选按请求者收窄）
POST /api/ai/platform-tools/<name>/invoke  只读：登录可调；写：仅超管
不经内部令牌网关 /api/ai/tools/。
"""

from __future__ import annotations

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import _is_superuser
from .tools import TOOLS, ToolNotFoundError, get_tool_debug_schema, invoke_platform_tool

logger = logging.getLogger("ai_assistant")


class ToolExecutionError(APIException):
    """平台工具执行失败（工具/引擎内部故障，非入参问题）→ 5xx。"""

    status_code = 500
    default_detail = "工具执行失败"
    default_code = "tool_execution_failed"


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


_DEVICE_OPTIONS_SOURCE = "devices:available"


def _available_device_options(user_id: str) -> list[dict]:
    """候选设备：对请求者可见、状态在线且当前未被占用。

    可见性口径复用 device_pool 的 api（与设备管理列表同源），本函数不另做可见性判定。
    """
    from apps.device_pool.api import list_devices
    from models.constants import DeviceStatus

    options = []
    for dev in list_devices(user_id=user_id):
        if dev.get("status") != DeviceStatus.ONLINE or dev.get("occupied_by"):
            continue
        serial = str(dev.get("serial") or "")
        if not serial:
            continue
        label = str(dev.get("name") or dev.get("model") or serial)
        options.append({"value": serial, "label": f"{label} ({serial})"})
    return options


def _resolve_param_options(source: str, user_id: str) -> list[dict]:
    """候选来源标识 → 候选项清单；未知来源返回空清单。"""
    if source == _DEVICE_OPTIONS_SOURCE:
        return _available_device_options(user_id)
    return []


class PlatformToolSchemaAPIView(APIView):
    """GET /api/ai/platform-tools/<name> — 调试入参 schema（候选值按请求者收窄）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, name: str):
        try:
            schema = get_tool_debug_schema(name)
        except ToolNotFoundError as exc:
            raise NotFound("tool not found") from exc

        user_id = _user_id(request)
        for param in schema["parameters"]:
            source = param.pop("options_source", None)
            if source:
                param["options"] = _resolve_param_options(source, user_id)
        return Response(schema)


class PlatformToolInvokeAPIView(APIView):
    """POST /api/ai/platform-tools/<name>/invoke — 真实调用平台工具。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, name: str):
        if name not in TOOLS:
            raise NotFound("tool not found")
        _func, read_only = TOOLS[name]
        if not read_only and not _is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")

        body = request.data
        if body is None or body == "":
            params = {}
        elif isinstance(body, dict):
            params = body
        else:
            raise ValidationError({"message": "请求体必须是 JSON 对象"})

        try:
            result = invoke_platform_tool(name, _user_id(request), params)
        except ToolNotFoundError as exc:
            raise NotFound("tool not found") from exc
        except ValueError as exc:
            # 入参 / 前置条件问题：请求者可自行修正 → 4xx
            raise ValidationError({"message": str(exc)}) from exc
        except Exception as exc:
            # 工具或引擎内部故障：与入参错误区分开 → 5xx，并留服务端日志
            logger.exception("平台工具 %s 执行失败（请求者 %s）", name, _user_id(request))
            raise ToolExecutionError(f"工具执行失败: {exc}") from exc

        return Response({"result": result})
