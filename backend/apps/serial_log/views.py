"""串口日志管理面（JWT）：端口列表 / 新增端口 / 监听开关 / 编辑删除 / 日志尾部行 / 关键词目录与维护。

GET    /api/serial-log/ports/                   登录可读：端口列表（含本机监听 IP、来源与运行时状态）
POST   /api/serial-log/ports/                   仅超管：新增自定义端口（保存即增量开启监听）
POST   /api/serial-log/ports/toggle/            仅超管：开/关某个端口的持续监听
PATCH  /api/serial-log/ports/<int:port>/        仅超管：编辑自定义端口（SKU / 波特率）
DELETE /api/serial-log/ports/<int:port>/        仅超管：删除自定义端口（保留日志文件）
GET    /api/serial-log/ports/<int:port>/lines/  登录可读：当前日志文件尾部若干行（只读）
GET    /api/serial-log/keywords/                登录可读：关键词 → 功能模块 / 功能点（带 row_id）
POST   /api/serial-log/keywords/                仅超管：新建关键词条目
PATCH  /api/serial-log/keywords/<int:row_id>/   仅超管：部分更新关键词条目
DELETE /api/serial-log/keywords/<int:row_id>/   仅超管：删除关键词条目（不影响日志文件）

不经内部令牌网关；日志正文不入库，只从本地当前日志文件读取。
"""

from __future__ import annotations

import threading
import time

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_superuser
from utils.logs import backend_log

from . import api, keywords, port_service
from .models import LogKeyword


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


_RECONCILE_TTL_SECONDS = 10.0
_reconcile_lock = threading.Lock()
_reconcile_at = 0.0


def _reconcile_throttled() -> None:
    """按开关状态校正监听：10 秒内只做一次，GET 不再每条请求都启停线程。"""
    global _reconcile_at
    now = time.monotonic()
    if now - _reconcile_at < _RECONCILE_TTL_SECONDS:
        return
    with _reconcile_lock:
        now = time.monotonic()
        if now - _reconcile_at < _RECONCILE_TTL_SECONDS:
            return
        try:
            port_service.reconcile()
        except Exception as exc:  # 采集故障不能拖垮读接口：记日志后照常返回
            backend_log.warning("device log port reconcile failed: %s", exc)
        _reconcile_at = now


class LogPortListAPIView(APIView):
    """GET /api/serial-log/ports/ — 端口列表（顺带按开关状态校正监听，10 秒节流）。

    POST /api/serial-log/ports/ — 新增自定义端口（仅超级管理员），保存即增量开启监听。
    body: `{"port": 7008, "sku": "H717D", "baud": 115200}`
    """

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _reconcile_throttled()
        return Response({"ports": port_service.list_ports(), "listen_ip": port_service.listen_ip()})

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        try:
            payload = port_service.create_port(
                request.data.get("port"), request.data.get("sku"), request.data.get("baud")
            )
        except (port_service.LogPortInvalid, port_service.LogPortCapReached) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload, status=201)


class LogPortDetailAPIView(APIView):
    """PATCH / DELETE /api/serial-log/ports/<port>/ — 编辑 / 删除自定义端口（仅超级管理员）。

    PATCH body: `{"sku": "H717D-V2", "baud": 460800}`（至少一个字段；端口号不可改）。
    编辑只重启被编辑的端口；删除停监听并移除登记，历史日志文件保留。
    """

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, port: int):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        try:
            payload = port_service.update_port(
                int(port), sku=request.data.get("sku"), baud=request.data.get("baud")
            )
        except (port_service.LogPortUnknown, port_service.LogPortInvalid) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, port: int):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        try:
            payload = port_service.delete_port(int(port))
        except (port_service.LogPortUnknown, port_service.LogPortInvalid) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload)


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
        _reconcile_throttled()
        payload = port_service.read_lines(int(port), request.query_params.get("tail"))
        return Response(payload)


class LogKeywordCatalogAPIView(APIView):
    """GET /api/serial-log/keywords/ — 关键词对照表（登录可读，功能点带 row_id）。

    POST /api/serial-log/keywords/ — 新建关键词条目（仅超级管理员）。
    body: `{"keyword": "h6601_boot", "module": "设备开关", "feature": "H6601开机完成", "scope": "H6601"}`
    （scope 缺省通用；feature_id 缺省续编）。
    """

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(keywords.collect_keywords())

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        try:
            row = api.create_keyword(
                request.data.get("keyword"),
                module=request.data.get("module"),
                feature=request.data.get("feature"),
                scope=request.data.get("scope") or LogKeyword.SCOPE_GENERAL,
                feature_id=request.data.get("feature_id"),
            )
        except (ValueError, TypeError) as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"row": keywords.row_payload(row)}, status=201)


class LogKeywordDetailAPIView(APIView):
    """PATCH / DELETE /api/serial-log/keywords/<row_id>/ — 编辑 / 删除关键词条目（仅超级管理员）。

    PATCH body: 部分字段 `{"keyword"?, "module"?, "feature"?, "scope"?, "feature_id"?, "sort_order"?}`。
    删除只移除登记条目，不影响日志文件与采集。
    """

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, row_id: int):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        data = request.data
        try:
            row = api.update_keyword(
                int(row_id),
                keyword=data.get("keyword"),
                module=data.get("module"),
                feature=data.get("feature"),
                scope=data.get("scope"),
                feature_id=data.get("feature_id"),
                sort_order=data.get("sort_order"),
            )
        except (ValueError, TypeError) as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"row": keywords.row_payload(row)})

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, row_id: int):
        if not is_superuser(_user_id(request)):
            raise PermissionDenied("Forbidden")
        if not api.delete_keyword(int(row_id)):
            raise ValidationError(f"关键词条目 {int(row_id)} 不存在")
        return Response(
            {"deleted": True, "note": f"关键词条目 {int(row_id)} 已删除，日志文件不受影响"}
        )
