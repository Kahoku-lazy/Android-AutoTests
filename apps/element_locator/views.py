"""element-locator HTTP routes — 11 endpoints under /api/elements/*."""
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import IntegrityError, models as dm

from apps.device_pool.models import Device
from apps.device_pool.api import device
from apps.device_pool.api import ensure_device
from .models import Page, Element, PageFlow
from .page_tree import (
    MAX_PAGE_TREE_DEPTH,
    page_depth,
    validate_parent_and_depth,
    sibling_label_exists,
    batch_move_pages,
)
from .service import gen_xpath_candidates

# Process prefixes that indicate execution engine occupation
_EXECUTION_OCCUPY_PREFIXES = ('runner-', 'ai_agent', 'task-', 'run-')


def _check_device_available(serial: str) -> tuple[bool, str, str]:
    """Check if a device is available for element-locator operations.

    Returns (available, error_message, occupied_by).
    """
    if not serial:
        return False, "未选择设备，请先连接设备", ""
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return False, "设备未注册", ""
    if dev.status == 'OFFLINE':
        return False, "设备已离线", ""
    if dev.status == 'BUSY' and dev.occupied_by:
        for prefix in _EXECUTION_OCCUPY_PREFIXES:
            if dev.occupied_by.startswith(prefix):
                return False, f"设备正被执行引擎占用（{dev.occupied_by}），请等待执行完毕", dev.occupied_by
    return True, "", dev.occupied_by or ""


@csrf_exempt
def dump_page(request):
    """POST /api/elements/dump — Dump current UI hierarchy (no persistence).

    Pages and elements are now managed manually via the element-manager.
    This endpoint only returns the live hierarchy for the locator UI.
    """
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"ok": False, "error": err_msg}, status=409)

    nodes = device.dump_hierarchy()

    # Save screenshot for visual reference (keep last 3)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_dir = settings.SCREENSHOT_DIR
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_file = shot_dir / f"page_{ts}.png"
    device.screenshot_file(str(shot_file))
    pngs = sorted(shot_dir.glob("page_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in pngs[3:]:
        try: old.unlink()
        except Exception: pass

    info = device.info()
    package = info.get("currentPackageName", "")
    cur = device.app_current()
    activity = cur.get("activity", "")

    # Generate XPath candidates for actionable elements
    xpath_count = 0
    for e in nodes:
        if e["resource_id"] or e["text"] or e["content_desc"] or e["clickable"]:
            e["xpaths"] = gen_xpath_candidates(e, nodes)
            xpath_count += 1

    actionable = [e for e in nodes if e["clickable"] or e["text"] or e["resource_id"] or e["content_desc"]]

    print(f"[dump] total={len(nodes)} xpath={xpath_count} actionable={len(actionable)} "
          f"package={package} activity={activity}")
    return JsonResponse({
        "ok": True, "serial": device.current_serial,
        "package": package, "activity": activity,
        "element_count": len(nodes),
        "actionable_count": len(actionable), "elements": nodes,
        "actionable": actionable,
    })


@csrf_exempt
def do_action(request):
    """POST /api/elements/action — Execute click or input on device."""
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"ok": False, "error": err_msg}, status=409)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})

    action = data.get("action", "")
    try:
        if action == "click":
            device.action_click(int(data["x"]), int(data["y"]))
        elif action == "longclick":
            device.action_longclick(int(data["x"]), int(data["y"]))
        elif action == "swipe":
            device.action_swipe(data.get("direction", "up"), int(data.get("distance", 500)))
        elif action == "drag":
            device.action_drag(int(data["x"]), int(data["y"]), data.get("direction", "up"), int(data.get("distance", 300)))
        elif action == "input":
            device.action_input(
                data.get("text", ""), data.get("x"), data.get("y"),
                clear_first=data.get("clear_first", True),
            )
        else:
            return JsonResponse({"ok": False, "error": f"unknown action: {action}"})
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


def device_info_view(request):
    """GET /api/elements/device-info — Current device info with resolution.

    Combines DB cached fields with live u2 info for the active device.
    Includes occupation status for frontend awareness.
    """
    info = device.info()
    serial = device.current_serial
    # Check occupation status from DB
    occupied_by = ""
    is_occupied = False
    try:
        dev = Device.objects.get(serial=serial)
        if dev.status == 'BUSY' and dev.occupied_by:
            occupied_by = dev.occupied_by
            is_occupied = True
    except Device.DoesNotExist:
        pass

    try:
        dev = Device.objects.get(serial=serial)
        return JsonResponse({
            "ok": True,
            "serial": serial,
            "model": dev.model or info.get("productName", ""),
            "brand": dev.brand or "",
            "screen_w": dev.screen_w or info.get("displayWidth", 1440),
            "screen_h": dev.screen_h or info.get("displayHeight", 3040),
            "connection_type": device.get_connection_type(serial),
            "package": info.get("currentPackageName", ""),
            "occupied": is_occupied,
            "occupied_by": occupied_by,
        })
    except Device.DoesNotExist:
        return JsonResponse({
            "ok": True,
            "serial": serial,
            "model": info.get("productName", ""),
            "brand": "",
            "screen_w": info.get("displayWidth", 1440),
            "screen_h": info.get("displayHeight", 3040),
            "connection_type": device.get_connection_type(serial),
            "package": info.get("currentPackageName", ""),
        })


def screenshot_snapshot(request):
    """GET /api/elements/screenshot — Single JPEG snapshot for fast first paint."""
    if not device.current_serial:
        return JsonResponse({"ok": False, "error": "未选择设备"})
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"ok": False, "error": err_msg}, status=409)
    try:
        b64 = device.screenshot_b64(quality=50, max_width=720)
        info = device.info()
        return JsonResponse({
            "ok": True,
            "image": b64,
            "format": "jpeg",
            "serial": device.current_serial,
            "screen_w": info.get("displayWidth", 0),
            "screen_h": info.get("displayHeight", 0),
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


# ── Page CRUD ──

def _page_payload(p):
  return {
      "id": p.id,
      "device_id": p.device_id,
      "parent_id": p.parent_id,
      "is_folder": p.is_folder,
      "depth": page_depth(p),
      "label": p.label,
      "package": p.package,
      "activity": p.activity,
      "screenshot_path": p.screenshot_path,
      "element_count": p.element_count,
      "created_at": str(p.created_at),
      "flow_out": getattr(p, "flow_out", 0),
      "flow_in": getattr(p, "flow_in", 0),
  }


def list_pages(request):
    """GET /api/elements/pages — List recorded pages (flat, with parent_id)."""
    pages = Page.objects.select_related("parent").annotate(
        flow_out=dm.Count('outgoing_flows', distinct=True),
        flow_in=dm.Count('incoming_flows', distinct=True),
    ).order_by('is_folder', 'label', '-created_at')

    result = [_page_payload(p) for p in pages]
    return JsonResponse({"ok": True, "pages": result, "max_depth": MAX_PAGE_TREE_DEPTH})


@csrf_exempt
def page_detail(request, page_id):
    """PUT/DELETE /api/elements/pages/{page_id}."""
    if request.method == 'PUT':
        data = json.loads(request.body)
        new_label = data.get("label", "").strip()
        if not new_label:
            return JsonResponse({"ok": False, "error": "页面名称不能为空"}, status=400)
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return JsonResponse({"ok": False, "error": "页面不存在"}, status=404)
        if sibling_label_exists(new_label, page.parent_id, exclude_id=page_id):
            return JsonResponse({"ok": False, "error": f"同级名称「{new_label}」已存在"}, status=409)
        Page.objects.filter(id=page_id).update(label=new_label)
        return JsonResponse({"ok": True})
    elif request.method == 'DELETE':
        Page.objects.filter(id=page_id).delete()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def create_page(request):
    """POST /api/elements/pages/create — Manually create a page or folder.

    Body: { label, parent_id?, is_folder?, package?, activity? }
    """
    if request.method != 'POST':
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = json.loads(request.body)
    label = data.get("label", "").strip()
    if not label:
        return JsonResponse({"ok": False, "error": "名称(label)必填"})

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None
    is_folder = bool(data.get("is_folder", False))

    try:
        validate_parent_and_depth(parent_id, is_folder=is_folder)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"ok": False, "error": "父级目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"ok": False, "error": "只能在目录下创建子级"}, status=400)

    if sibling_label_exists(label, parent_id):
        return JsonResponse({"ok": False, "error": f"同级名称「{label}」已存在"}, status=409)

    dev_obj = ensure_device(serial=device.current_serial, name="Samsung")
    try:
        page = Page.objects.create(
            device=dev_obj,
            parent_id=parent_id,
            is_folder=is_folder,
            label=label,
            package=data.get("package", ""),
            activity=data.get("activity", ""),
        )
    except IntegrityError:
        return JsonResponse({"ok": False, "error": f"创建失败，名称「{label}」可能已存在"}, status=409)
    return JsonResponse({"ok": True, "page": _page_payload(page)})


@csrf_exempt
def pages_batch_move(request):
    """POST /api/elements/pages/batch-move — Move pages/folders to a target parent.

    Body: { page_ids: [1, 2], parent_id: 5 | null }
    parent_id=null moves items to root level.
    """
    if request.method != 'POST':
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = json.loads(request.body)
    page_ids = data.get("page_ids") or []
    if not page_ids:
        return JsonResponse({"ok": False, "error": "page_ids 不能为空"}, status=400)

    parent_id = data.get("parent_id")
    if parent_id in ("", 0, "0"):
        parent_id = None

    if parent_id:
        try:
            parent = Page.objects.get(pk=parent_id)
        except Page.DoesNotExist:
            return JsonResponse({"ok": False, "error": "目标目录不存在"}, status=404)
        if not parent.is_folder:
            return JsonResponse({"ok": False, "error": "目标必须是目录"}, status=400)

    try:
        ids = [int(x) for x in page_ids]
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "page_ids 格式无效"}, status=400)

    result = batch_move_pages(ids, parent_id)
    return JsonResponse({"ok": True, **result})


def _element_payload(el):
    return {
        "id": el.id, "page_id": el.page_id, "alias": el.alias,
        "class_name": el.class_name, "text_val": el.text_val,
        "resource_id": el.resource_id, "clickable": el.clickable,
        "bounds": el.bounds, "xpath_candidates": el.xpath_candidates,
        "is_test_point": el.is_test_point, "notes": el.notes,
    }


@csrf_exempt
def add_element_to_page(request, page_id):
    """POST /api/elements/pages/{page_id}/elements — Manually add element to page.

    Body: { alias, xpath, class_name?, text_val?, resource_id?, bounds?,
            clickable?, content_desc? }

    Same (page, resource_id, bounds) is upserted — duplicate save updates metadata.
    """
    try:
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return JsonResponse({"ok": False, "error": "页面不存在"}, status=404)
        if page.is_folder:
            return JsonResponse({"ok": False, "error": "目录节点不能添加元素，请选择子页面"}, status=400)

        data = json.loads(request.body)
        alias = data.get("alias", "").strip()
        if not alias:
            return JsonResponse({"ok": False, "error": "元素名称(alias)必填"})

        xpath = data.get("xpath", "")
        xpath_candidates_data = data.get("xpath_candidates")
        if xpath_candidates_data:
            xpaths = json.dumps(xpath_candidates_data)
        elif xpath:
            xpaths = json.dumps([{"type": "manual", "xpath": xpath, "count": 1}])
        else:
            xpaths = "[]"
        fields = {
            "alias": alias,
            "class_name": data.get("class_name", ""),
            "text_val": data.get("text_val", data.get("text", "")),
            "content_desc": data.get("content_desc", ""),
            "resource_id": data.get("resource_id", ""),
            "bounds": data.get("bounds", ""),
            "xpath_candidates": xpaths,
            "clickable": bool(data.get("clickable", False)),
            "enabled": bool(data.get("enabled", True)),
            "notes": data.get("notes", ""),
        }

        existing = Element.objects.filter(
            page=page,
            resource_id=fields["resource_id"],
            bounds=fields["bounds"],
        ).first()
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            existing.save()
            el = existing
            updated = True
        else:
            try:
                el = Element.objects.create(page=page, **fields)
                updated = False
            except IntegrityError:
                return JsonResponse({
                    "ok": False,
                    "error": "该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看",
                }, status=409)
            page.element_count = Element.objects.filter(page=page).count()
            page.save(update_fields=["element_count"])

        return JsonResponse({
            "ok": True,
            "updated": updated,
            "element": _element_payload(el),
        })
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "error": "保存元素失败，请稍后重试",
            "detail": str(e),
        }, status=500)


@csrf_exempt
def batch_add_elements(request, page_id):
    """POST /api/elements/pages/{page_id}/elements/batch — Batch save elements.

    Body: { elements: [{ alias, xpath, xpath_candidates, class_name, text_val,
            resource_id, bounds, clickable, content_desc }], strategy: "resource-id" }

    Each element already has its pre-selected XPath. Same per-element upsert logic.
    """
    try:
        page = Page.objects.get(id=page_id)
    except Page.DoesNotExist:
        return JsonResponse({"ok": False, "error": "页面不存在"}, status=400)
    if page.is_folder:
        return JsonResponse({"ok": False, "error": "目录节点不能添加元素"}, status=400)

    data = json.loads(request.body)
    items = data.get("elements", [])
    if not items:
        return JsonResponse({"ok": False, "error": "elements 不能为空"}, status=400)

    saved = 0
    updated = 0
    skipped = 0
    errors = []

    for item in items:
        alias = item.get("alias", "").strip()
        if not alias:
            skipped += 1
            continue

        xpath_candidates_data = item.get("xpath_candidates")
        if xpath_candidates_data:
            xpaths = json.dumps(xpath_candidates_data)
        else:
            xpath = item.get("xpath", "")
            if xpath:
                xpaths = json.dumps([{
                    "type": item.get("xpath_type", "manual"),
                    "xpath": xpath,
                    "count": item.get("xpath_count", 1),
                }])
            else:
                xpaths = "[]"

        fields = {
            "alias": alias,
            "class_name": item.get("class_name", ""),
            "text_val": item.get("text_val", ""),
            "content_desc": item.get("content_desc", ""),
            "resource_id": item.get("resource_id", ""),
            "bounds": item.get("bounds", ""),
            "xpath_candidates": xpaths,
            "clickable": bool(item.get("clickable", False)),
            "enabled": bool(item.get("enabled", True)),
            "notes": item.get("notes", ""),
        }

        try:
            existing = Element.objects.filter(
                page=page,
                resource_id=fields["resource_id"],
                bounds=fields["bounds"],
            ).first()
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                existing.save()
                updated += 1
            else:
                try:
                    Element.objects.create(page=page, **fields)
                    saved += 1
                except IntegrityError:
                    skipped += 1
                    continue
        except Exception as e:
            errors.append(f"{alias}: {e}")
            skipped += 1
            continue

    # Update page element count
    page.element_count = Element.objects.filter(page=page).count()
    page.save(update_fields=["element_count"])

    result = {"ok": True, "saved": saved, "updated": updated, "skipped": skipped}
    if errors:
        result["errors"] = errors[:5]
    return JsonResponse(result)


@csrf_exempt
def clear_pages(request):
    """POST /api/elements/pages/clear — Clear all pages/elements/flows."""
    Element.objects.all().delete()
    PageFlow.objects.all().delete()
    Page.objects.all().delete()
    return JsonResponse({"ok": True})


def page_elements(request, page_id):
    """GET /api/elements/pages/{page_id}/items — Page elements with filter."""
    filter_type = request.GET.get("filter", "all")
    qs = Element.objects.filter(page_id=page_id)
    if filter_type == "clickable":
        qs = qs.filter(clickable=True)
    elif filter_type == "text":
        qs = qs.exclude(text_val='')
    elif filter_type == "testpoint":
        qs = qs.filter(is_test_point=True)
    qs = qs.order_by('id')

    result = [{
        "id": e.id, "page_id": e.page_id, "class_name": e.class_name,
        "text_val": e.text_val, "content_desc": e.content_desc,
        "resource_id": e.resource_id, "bounds": e.bounds,
        "xpath_candidates": e.xpath_candidates, "clickable": e.clickable,
        "enabled": e.enabled, "alias": e.alias, "tags": e.tags,
        "is_test_point": e.is_test_point, "notes": e.notes,
        "created_at": str(e.created_at),
    } for e in qs]
    return JsonResponse({"ok": True, "elements": result})


@csrf_exempt
def update_element(request, el_id):
    """PUT /api/elements/items/{el_id} — Update element metadata."""
    data = json.loads(request.body)
    updates = {}
    for k in ["alias", "tags", "notes"]:
        if k in data:
            updates[k] = data[k]
    if "is_test_point" in data:
        updates["is_test_point"] = bool(data["is_test_point"])
    if updates:
        Element.objects.filter(id=el_id).update(**updates)
    return JsonResponse({"ok": True})


# ── Flow CRUD ──

@csrf_exempt
def flows_handler(request):
    """GET/POST /api/elements/flows."""
    if request.method == 'GET':
        flows = PageFlow.objects.select_related(
            'from_page', 'to_page', 'trigger_element'
        ).order_by('-created_at')
        result = [{
            "id": f.id, "from_page_id": f.from_page_id,
            "to_page_id": f.to_page_id,
            "trigger_element_id": f.trigger_element_id,
            "trigger_action": f.trigger_action,
            "created_at": str(f.created_at),
            "from_label": f.from_page.label if f.from_page_id else "",
            "to_label": f.to_page.label if f.to_page_id else "",
            "trigger_text": f.trigger_element.text_val if f.trigger_element_id else "",
            "trigger_rid": f.trigger_element.resource_id if f.trigger_element_id else "",
        } for f in flows]
        return JsonResponse({"ok": True, "flows": result})

    elif request.method == 'POST':
        data = json.loads(request.body)
        PageFlow.objects.create(
            from_page_id=data["from_page_id"],
            to_page_id=data["to_page_id"],
            trigger_element_id=data.get("trigger_element_id"),
            trigger_action=data.get("trigger_action", "click"),
        )
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def delete_flow(request, flow_id):
    """DELETE /api/elements/flows/{flow_id}."""
    PageFlow.objects.filter(id=flow_id).delete()
    return JsonResponse({"ok": True})
