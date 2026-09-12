"""device-inspector HTTP 入口 — v1.7 快照化 6 端点（薄层：解析 → 调 api → 信封）。

响应经 EnvelopeJSONRenderer 统一为 {status, data} / {status, message}。
写操作全部下沉 api.py / service.py，本文件不直接 ORM。
"""

import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import api
from .service import CaptureError

logger = logging.getLogger(__name__)


def _user_id(request) -> str:
    return str(getattr(request, "user_id", "") or "")


@api_view(["POST"])
def capture(request):
    """POST /api/inspector/capture — 一键获取（serial + method）→ 快照落库。"""
    serial = (request.data.get("serial") or "").strip()
    method = request.data.get("method") or "dump"
    try:
        return Response(api.capture_snapshot(_user_id(request), serial, method))
    except CaptureError as e:
        return Response({"message": str(e)}, status=e.status_code)
    except Exception:
        logger.exception("capture failed serial=%s", serial)
        return Response({"message": "获取失败"}, status=500)


@api_view(["GET"])
def snapshots(request):
    """GET /api/inspector/snapshots — 快照列表（offset/limit，倒序）。"""
    try:
        offset = int(request.query_params.get("offset", 0))
        limit = min(int(request.query_params.get("limit", 100)), 100)
    except ValueError:
        return Response({"message": "无效的分页参数"}, status=400)
    return Response(api.list_snapshots(_user_id(request), offset, limit))


@api_view(["GET"])
def snapshot_detail(request, snapshot_id: int):
    """GET /api/inspector/snapshots/{id} — 快照详情 JSON。"""
    data = api.get_snapshot(snapshot_id, _user_id(request))
    if data is None:
        return Response({"message": "快照不存在"}, status=404)
    return Response(data)


@api_view(["DELETE"])
def snapshot_delete(request, snapshot_id: int):
    """DELETE /api/inspector/snapshots/{id} — 删除快照 + 文件清理。"""
    if not api.delete_snapshot(snapshot_id, _user_id(request)):
        return Response({"message": "快照不存在"}, status=404)
    return Response({"deleted": True})


@api_view(["POST"])
def save_elements(request, snapshot_id: int):
    """POST /api/inspector/snapshots/{id}/save-elements — 筛减保存到元素定位。"""
    from apps.element_locator.api import ImportConflictError

    body = request.data or {}
    page_label = (body.get("page_label") or "").strip()
    folder_path = (body.get("folder_path") or "").strip()
    page_id = body.get("page_id")
    element_ids = body.get("element_ids")
    include_ocr = bool(body.get("include_ocr", True))
    aliases = body.get("aliases") or None
    try:
        return Response(
            api.save_snapshot_to_elements(
                snapshot_id,
                user_id=_user_id(request),
                page_label=page_label,
                folder_path=folder_path,
                page_id=int(page_id) if page_id else None,
                element_ids=element_ids,
                include_ocr=include_ocr,
                aliases=aliases,
            )
        )
    except ImportConflictError as e:
        return Response({"message": str(e)}, status=409)
    except ValueError as e:
        return Response({"message": str(e)}, status=400)
    except Exception:
        logger.exception("save snapshot %s to elements failed", snapshot_id)
        return Response({"message": "保存失败"}, status=500)


@api_view(["GET"])
def snapshot_analyze(request, snapshot_id: int):
    """GET /api/inspector/snapshots/{id}/analyze — 快照结构分析（纯规则，无设备交互）。"""
    data = api.analyze_snapshot(snapshot_id, _user_id(request))
    if data is None:
        return Response({"message": "快照不存在"}, status=404)
    return Response(data)


@api_view(["GET"])
def page_view(request, page_id: int):
    """GET /api/inspector/pages/{page_id} — 元素定位已保存页面只读视图。"""
    data = api.get_page_view(page_id)
    if data is None:
        return Response({"message": "页面不存在"}, status=404)
    return Response(data)
