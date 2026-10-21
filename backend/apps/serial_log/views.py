"""串口日志管理面（JWT）：端口列表 / 监听开关 / 当前日志文件尾部行 / 关键词对照表。

GET  /api/serial-log/ports/                   登录可读：端口列表（三列 + 开关 + 运行时监听状态）
POST /api/serial-log/ports/toggle/            仅超管：开/关某个端口的持续监听
GET  /api/serial-log/ports/<int:port>/lines/  登录可读：当前日志文件尾部若干行（只读）
GET  /api/serial-log/keywords/                登录可读：关键词 → 功能模块 / 功能点（只读）

不经内部令牌网关；日志正文不入库，只从本地当前日志文件读取。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_superuser
from utils.logs import backend_log

from . import keywords, port_service


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


class LogPortListAPIView(APIView):
    """GET /api/serial-log/ports/ — 端口列表（顺带按开关状态校正监听，幂等）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        try:
            port_service.reconcile()
        except Exception as exc:  # 列表不能被采集故障拖垮：照常给出配置与开关状态
            backend_log.warning("device log port reconcile failed on list: %s", exc)
        return Response({"ports": port_service.list_ports()})


class LogPortToggleAPIView(APIView):
    """POST /api/serial-log/ports/toggle/ — 开关某端口的持续监听（仅超级管理员）。

    body: `{"port": 7005, "enabled": true|false}`
    开启即开始监听并落日志文件；关闭即停止监听并释放端口。
    """

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        raw_port = request.data.get("port")
        try:
            port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise ValidationError("port 必填且必须为数字") from exc
        enabled = bool(request.data.get("enabled", True))
        try:
            payload = port_service.set_enabled(port, enabled)
        except port_service.LogPortUnknown as exc:
            # 未登记端口不是服务端故障：给出可读结论（400），由调用方改端口
            raise ValidationError(str(exc)) from exc
        return Response(payload)


class LogPortLinesAPIView(APIView):
    """GET /api/serial-log/ports/<port>/lines/ — 当前日志文件尾部若干行（只读）。

    query: `tail`（行数，默认 2000，夹紧到上限）；未登记端口与关闭态都返回可读结论。
    """

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, port: int):
        try:
            port_service.reconcile()
        except Exception as exc:  # 读日志不依赖采集线程：失败也照常返回文件内容
            backend_log.warning("device log port reconcile failed on read: %s", exc)
        payload = port_service.read_lines(int(port), request.query_params.get("tail"))
        return Response(payload)


class LogKeywordCatalogAPIView(APIView):
    """GET /api/serial-log/keywords/ — 关键词对照表（只读，登录可读）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(keywords.collect_keywords())
