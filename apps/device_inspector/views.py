"""device-inspector HTTP routes — live device interaction endpoints."""

import json
import logging

from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.device_pool.api import device
from apps.device_pool.models import Device

from .service import gen_xpath_candidates

logger = logging.getLogger(__name__)

# Process prefixes that indicate execution engine occupation
_EXECUTION_OCCUPY_PREFIXES = ("runner-", "ai_agent", "task-", "run-")


def _check_device_available(serial: str) -> tuple[bool, str, str]:
    """Check if a device is available for inspector operations.

    Returns (available, error_message, occupied_by).
    """
    if not serial:
        return False, "未选择设备，请先连接设备", ""
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return False, "设备未注册", ""
    if dev.status == "OFFLINE":
        return False, "设备已离线", ""
    if dev.status == "BUSY" and dev.occupied_by:
        for prefix in _EXECUTION_OCCUPY_PREFIXES:
            if dev.occupied_by.startswith(prefix):
                return (
                    False,
                    f"设备正被执行引擎占用（{dev.occupied_by}），请等待执行完毕",
                    dev.occupied_by,
                )
    return True, "", dev.occupied_by or ""


@csrf_exempt
def dump_page(request):
    """POST /api/inspector/dump — Dump current UI hierarchy (no persistence).

    Pages and elements are now managed manually via the element-manager.
    This endpoint only returns the live hierarchy for the locator UI.
    """
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"status": False, "message": err_msg}, status=409)

    nodes = device.dump_hierarchy()

    # Save screenshot for visual reference (keep last 3)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_dir = settings.SCREENSHOT_DIR
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_file = shot_dir / f"page_{ts}.png"
    device.screenshot_file(str(shot_file))
    pngs = sorted(shot_dir.glob("page_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in pngs[3:]:
        try:
            old.unlink()
        except Exception:
            logger.debug("Failed to delete old screenshot: %s", old)

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

    actionable = [
        e for e in nodes if e["clickable"] or e["text"] or e["resource_id"] or e["content_desc"]
    ]

    logger.info(
        "[dump] total=%d xpath=%d actionable=%d package=%s activity=%s",
        len(nodes),
        xpath_count,
        len(actionable),
        package,
        activity,
    )
    return JsonResponse(
        {
            "status": True,
            "serial": device.current_serial,
            "package": package,
            "activity": activity,
            "element_count": len(nodes),
            "actionable_count": len(actionable),
            "elements": nodes,
            "actionable": actionable,
        }
    )


@csrf_exempt
def do_action(request):
    """POST /api/inspector/action — Execute click or input on device."""
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"status": False, "message": err_msg}, status=409)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": False, "message": "invalid JSON"})

    action = data.get("action", "")
    try:
        if action == "click":
            device.action_click(int(data["x"]), int(data["y"]))
        elif action == "longclick":
            device.action_longclick(int(data["x"]), int(data["y"]))
        elif action == "swipe":
            device.action_swipe(data.get("direction", "up"), int(data.get("distance", 500)))
        elif action == "drag":
            device.action_drag(
                int(data["x"]),
                int(data["y"]),
                data.get("direction", "up"),
                int(data.get("distance", 300)),
            )
        elif action == "input":
            device.action_input(
                data.get("text", ""),
                data.get("x"),
                data.get("y"),
                clear_first=data.get("clear_first", True),
            )
        else:
            return JsonResponse({"status": False, "message": f"unknown action: {action}"})
        return JsonResponse({"status": True})
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)})


def device_info_view(request):
    """GET /api/inspector/device-info — Current device info with resolution.

    Combines DB cached fields with live u2 info for the active device.
    Includes occupation status for frontend awareness.
    """
    info = device.info()
    serial = device.current_serial

    try:
        dev = Device.objects.get(serial=serial)
        is_occupied = dev.status == "BUSY" and bool(dev.occupied_by)
        return JsonResponse(
            {
                "status": True,
                "serial": serial,
                "model": dev.model or info.get("productName", ""),
                "brand": dev.brand or "",
                "screen_w": dev.screen_w or info.get("displayWidth", 1440),
                "screen_h": dev.screen_h or info.get("displayHeight", 3040),
                "connection_type": device.get_connection_type(serial),
                "package": info.get("currentPackageName", ""),
                "occupied": is_occupied,
                "occupied_by": dev.occupied_by if is_occupied else "",
            }
        )
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "status": True,
                "serial": serial,
                "model": info.get("productName", ""),
                "brand": "",
                "screen_w": info.get("displayWidth", 1440),
                "screen_h": info.get("displayHeight", 3040),
                "connection_type": device.get_connection_type(serial),
                "package": info.get("currentPackageName", ""),
            }
        )


def screenshot_snapshot(request):
    """GET /api/inspector/screenshot — Single JPEG snapshot for fast first paint."""
    if not device.current_serial:
        return JsonResponse({"status": False, "message": "未选择设备"})
    available, err_msg, _ = _check_device_available(device.current_serial)
    if not available:
        return JsonResponse({"status": False, "message": err_msg}, status=409)
    try:
        b64 = device.screenshot_b64(quality=50, max_width=720)
        info = device.info()
        return JsonResponse(
            {
                "status": True,
                "image": b64,
                "format": "jpeg",
                "serial": device.current_serial,
                "screen_w": info.get("displayWidth", 0),
                "screen_h": info.get("displayHeight", 0),
            }
        )
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)})
