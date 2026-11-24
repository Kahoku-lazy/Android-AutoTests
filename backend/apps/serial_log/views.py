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
        except Exception as exc:
            backend_log.warning("device log port reconcile failed: %s", exc)
        _reconcile_at = now


class LogPortListAPIView(APIView):
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
            raise ValidationError(str(exc)) from exc
        return Response(payload)


class LogPortLinesAPIView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, port: int):
        _reconcile_throttled()
        payload = port_service.read_lines(int(port), request.query_params.get("tail"))
        return Response(payload)


class LogKeywordCatalogAPIView(APIView):
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
