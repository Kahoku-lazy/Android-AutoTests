"""element-locator legacy 平铺端点 — Android 页面 CRUD（自 views.py 拆分）。

信封：legacy 平铺（登记特例，勿改造为 {status,data}）；路由真相源 urls.py。
"""

import json

from django.db import IntegrityError
from django.db import models as dm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.device_pool.api import device, ensure_device

from . import api
from .models import Page
from .page_tree import (
    MAX_PAGE_TREE_DEPTH,
    batch_move_pages,
    build_page_maps,
    compute_depth,
    page_depth,
    sibling_label_exists,
    validate_parent_and_depth,
)

# ── Page CRUD ──


def _page_payload(p, parent_map=None):
    depth = compute_depth(p.id, parent_map) if parent_map is not None else page_depth(p)
    return {
        "id": p.id,
        "device_id": p.device_id,
        "parent_id": p.parent_id,
        "is_folder": p.is_folder,
        "depth": depth,
        "label": p.label,
        "package": p.package,
        "activity": p.activity,
        "screenshot_path": p.screenshot_path,
        "ocr_json": p.ocr_json or None,
        "snapshot_id": p.snapshot_id,
        "element_count": p.element_count,
        "created_at": str(p.created_at),
        "flow_out": getattr(p, "flow_out", 0),
        "flow_in": getattr(p, "flow_in", 0),
    }


def list_pages(request):
    """GET /api/elements/pages — List recorded pages (flat, with parent_id).

    Uses a single-query parent_map to compute depths without N+1 DB round-trips.
    Supports ?offset=N&limit=N for pagination.
    """
    pages = (
        Page.objects.select_related("parent")
        .annotate(
            flow_out=dm.Count("outgoing_flows", distinct=True),
            flow_in=dm.Count("incoming_flows", distinct=True),
        )
        .order_by("is_folder", "label", "-created_at")
    )

    # Build in-memory parent map once to avoid N+1 in _page_payload → page_depth
    parent_map, _ = build_page_maps()
    result = [_page_payload(p, parent_map) for p in pages]
    return JsonResponse({"status": True, "pages": result, "max_depth": MAX_PAGE_TREE_DEPTH})


@csrf_exempt
def page_detail(request, page_id):
    """PUT/DELETE /api/elements/pages/{page_id}."""
    if request.method == "PUT":
        data = json.loads(request.body)
        new_label = data.get("label", "").strip()
        if not new_label:
            return JsonResponse({"status": False, "message": "页面名称不能为空"}, status=400)
        # Fetch once for validation, then update in one query
        page = Page.objects.filter(id=page_id).values("parent_id").first()
        if page is None:
            return JsonResponse({"status": False, "message": "页面不存在"}, status=404)
        parent_id = page["parent_id"]
        if sibling_label_exists(new_label, parent_id, exclude_id=page_id):
            return JsonResponse(
                {"status": False, "message": f"同级名称「{new_label}」已存在"}, status=409
            )
        api.rename_page(page_id, new_label)
        return JsonResponse({"status": True})
    elif request.method == "DELETE":
        api.delete_page(page_id)
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def create_page(request):
    """POST /api/elements/pages/create — Manually create a page (or legacy folder).

    Body: { label, directory_id?, parent_id?, is_folder?, package?, activity? }
    项目化：传 directory_id 时创建页面文件（is_folder 强制 False）。
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = json.loads(request.body)
    label = data.get("label", "").strip()
    if not label:
        return JsonResponse({"status": False, "message": "名称(label)必填"})

    directory_id = data.get("directory_id", "__missing__")
    # 工作台：显式传 directory_id（含 null=项目根）则走目录挂接，不建旧文件夹树
    if directory_id != "__missing__":
        if directory_id in ("", 0, "0"):
            directory_id = None
        elif directory_id is not None:
            directory_id = int(directory_id)
            from .models import LocatorDirectory

            if not LocatorDirectory.objects.filter(
                id=directory_id, project__code="android"
            ).exists():
                return JsonResponse({"status": False, "message": "目录不存在"}, status=404)
        if Page.objects.filter(label=label, directory_id=directory_id, is_folder=False).exists():
            return JsonResponse(
                {"status": False, "message": f"同级名称「{label}」已存在"}, status=409
            )
        try:
            page = api.create_page_manually(
                None,
                None,
                False,
                label,
                package=data.get("package", ""),
                activity=data.get("activity", ""),
                directory_id=directory_id,
            )
        except IntegrityError:
            return JsonResponse(
                {"status": False, "message": f"创建失败，名称「{label}」可能已存在"}, status=409
            )
        return JsonResponse(
            {
                "status": True,
                "page": {
                    "id": page.id,
                    "label": page.label,
                    "directory_id": page.directory_id,
                },
            }
        )

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None
    is_folder = bool(data.get("is_folder", False))
    if is_folder:
        return JsonResponse(
            {"status": False, "message": "请改用项目目录 API 新建目录"},
            status=410,
        )

    try:
        validate_parent_and_depth(parent_id, is_folder=is_folder)
    except ValueError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=400)

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"status": False, "message": "父级目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"status": False, "message": "只能在目录下创建子级"}, status=400)

    if sibling_label_exists(label, parent_id):
        return JsonResponse({"status": False, "message": f"同级名称「{label}」已存在"}, status=409)

    dev_obj = ensure_device(serial=device.current_serial, name="Samsung")
    try:
        page = api.create_page_manually(
            dev_obj,
            parent_id,
            is_folder,
            label,
            package=data.get("package", ""),
            activity=data.get("activity", ""),
            directory_id=None,
        )
    except IntegrityError:
        return JsonResponse(
            {"status": False, "message": f"创建失败，名称「{label}」可能已存在"}, status=409
        )
    return JsonResponse({"status": True, "page": _page_payload(page)})


@csrf_exempt
def pages_batch_move(request):
    """POST /api/elements/pages/batch-move — Move pages/folders to a target parent.

    Body: { page_ids: [1, 2], parent_id: 5 | null }
    parent_id=null moves items to root level.
    """
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = json.loads(request.body)
    page_ids = data.get("page_ids") or []
    if not page_ids:
        return JsonResponse({"status": False, "message": "page_ids 不能为空"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"status": False, "message": "目标目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"status": False, "message": "目标必须是目录"}, status=400)

    try:
        ids = [int(x) for x in page_ids]
    except (TypeError, ValueError):
        return JsonResponse({"status": False, "message": "page_ids 格式无效"}, status=400)

    result = batch_move_pages(ids, parent_id)
    return JsonResponse({"status": True, **result})


@csrf_exempt
def clear_pages(request):
    """POST /api/elements/pages/clear — Clear all pages/elements/flows."""
    api.clear_all()
    return JsonResponse({"status": True})
