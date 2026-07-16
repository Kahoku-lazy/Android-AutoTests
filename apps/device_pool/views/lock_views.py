"""Device lock, release, heartbeat, and queue endpoints."""
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .helpers import (
    _update_device_status, _release_internal,
    _auto_assign_from_queue, _check_timeout_queue, _device_to_dict,
)
from ..models import Device, DeviceQueue

@csrf_exempt
def lock_device(request, serial):
    """POST /api/devices/{serial}/lock — 用户绑定或进程占用。

    type="user" (default): 用户绑定 — 设置 locked_by，不改 status
    type="occupy": 进程占用 — 设置 occupied_by，改 status=BUSY
    """
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})

    lock_type = data.get("type", "user")
    user_id = data.get("user_id", "").strip()
    if not user_id:
        return JsonResponse({"ok": False, "error": "user_id 不能为空"}, status=400)
    timeout = int(data.get("timeout", 300))

    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse({"ok": False, "error": f"设备 {serial} 未注册"}, status=404)

    if dev.status == "OFFLINE" or dev.status == "DISCONNECTED":
        return JsonResponse({"ok": False, "error": f"设备已{dev.status}，无法操作"}, status=400)

    now = datetime.now()

    # ── 进程占用 ──
    if lock_type == "occupy":
        if dev.occupied_by and dev.occupied_by != user_id:
            return JsonResponse(
                {"ok": False, "error": f"设备已被 {dev.occupied_by} 占用"}, status=409
            )
        dev.occupied_by = user_id
        dev.occupied_at = now
        dev.status = "BUSY"
        dev.save(update_fields=["occupied_by", "occupied_at", "status"])
        DeviceLock.objects.create(
            device=dev,
            user_id=user_id,
            lock_type="process",
            timeout_seconds=timeout,
            status="active",
        )
        return JsonResponse(
            {
                "ok": True,
                "serial": serial,
                "occupied_by": user_id,
                "occupied_at": now.isoformat(),
                "timeout": timeout,
            }
        )

    # ── 用户绑定 ──
    if dev.locked_by and dev.locked_by != user_id:
        return JsonResponse({"ok": False, "error": f"设备已被 {dev.locked_by} 绑定"}, status=409)
    dev.locked_by = user_id
    dev.locked_at = now
    dev.save(update_fields=["locked_by", "locked_at"])
    DeviceLock.objects.create(
        device=dev,
        user_id=user_id,
        lock_type="user",
        timeout_seconds=timeout,
        status="active",
    )
    return JsonResponse(
        {
            "ok": True,
            "serial": serial,
            "user_id": user_id,
            "locked_at": now.isoformat(),
            "timeout": timeout,
            "is_occupied": dev.is_occupied,
        }
    )


def release_device(request, serial):
    """POST /api/devices/{serial}/release — 释放设备锁。

    PRD §6.2.5: 手动/超时/断开/强制释放，保留锁审计。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    reason = data.get("reason", "manual")
    user_id = data.get("user_id", "").strip()

    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 未注册",
            },
            status=404,
        )

    # 解除进程占用 + 可选解除用户绑定
    # (不再检查 status==BUSY，因为 lock 不再改 status)
    force_release = data.get("force", False)
    unlock_too = data.get("unlock", False)  # 同时解除用户绑定
    occupied_by = dev.occupied_by or ""

    # 执行引擎占用 → 禁止解除（除非强制）
    is_runner_occupied = (
        occupied_by.startswith("ai_agent")
        or occupied_by.startswith("runner-")
        or occupied_by.startswith("task-")
        or occupied_by.startswith("run-")
    )

    if is_runner_occupied and not force_release:
        return JsonResponse(
            {
                "ok": False,
                "error": "设备正在执行用例，无法解除占用。请等待用例执行完毕或先停止执行任务。",
                "occupied_by": occupied_by,
                "is_runner": True,
            },
            status=409,
        )

    # 仅解除用户绑定（不清 occupied_by）
    if unlock_too and not dev.occupied_by:
        if not dev.locked_by:
            return JsonResponse({"ok": False, "error": "设备未被绑定，无需操作"}, status=400)
        dev.locked_by = ""
        dev.locked_at = None
        dev.save(update_fields=["locked_by", "locked_at"])
        DeviceLock.objects.filter(device=dev, lock_type="user", status="active").update(
            status="released", released_at=datetime.now(), release_reason="manual"
        )
        return JsonResponse({"ok": True, "serial": serial, "unlocked": True})

    # 解除占用（委托给共享 helper，保证 DeviceLock 审计 + 队列自动分配）
    if not dev.occupied_by:
        return JsonResponse({"ok": False, "error": "设备未被占用，无需操作"}, status=400)
    _release_internal(dev, reason="force" if force_release else "manual", clear_lock=unlock_too)

    return JsonResponse(
        {
            "ok": True,
            "serial": serial,
            "released": True,
            "force_released": force_release,
            "unlocked": unlock_too,
        }
    )


def device_queue(request):
    """GET /api/devices/queue — 排队状态。

    PRD §6.2.7: 返回当前所有等待中的排队记录（FIFO）。
    """
    entries = (
        DeviceQueue.objects.filter(status="waiting")
        .select_related("device")
        .order_by("requested_at")
    )

    now = datetime.now()
    result = []
    for i, entry in enumerate(entries):
        waited = int((now - entry.requested_at).total_seconds())
        result.append(
            {
                "position": i + 1,
                "serial": entry.device.serial,
                "user_id": entry.user_id,
                "requested_at": entry.requested_at.isoformat(),
                "waited_seconds": waited,
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "queue": result,
            "count": len(result),
        }
    )


def heartbeat(request):
    """GET /api/devices/heartbeat — 手动触发心跳检测。

    PRD §6.2.7: 同步设备状态，清理过期锁和排队。
    """
    updated, offline = _update_device_status()
    _check_timeout_queue()

    online = Device.objects.filter(status="ONLINE").count()
    busy = Device.objects.filter(status="BUSY").count()
    offline_count = Device.objects.filter(status="OFFLINE").count()
    disconnected = Device.objects.filter(status="DISCONNECTED").count()

    return JsonResponse(
        {
            "ok": True,
            "updated": updated,
            "offline": offline,
            "online": online,
            "busy": busy,
            "offline_count": offline_count,
            "disconnected": disconnected,
            "total": online + busy + offline_count + disconnected,
        }
    )


# ═══════════════════════════════════════════════
# v2 排队管理端点 (新增 2 个)
# ═══════════════════════════════════════════════


@csrf_exempt
def join_device_queue(request, serial):
    """POST /api/devices/{serial}/queue — 加入排队。

    防重复：同一用户对同一设备只能排队一次。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})

    user_id = data.get("user_id", "").strip()
    if not user_id:
        return JsonResponse(
            {
                "ok": False,
                "error": "user_id 不能为空",
            },
            status=400,
        )

    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 未注册",
            },
            status=404,
        )

    # 防重复
    existing = DeviceQueue.objects.filter(device=dev, user_id=user_id, status="waiting").first()
    if existing:
        waited = int((datetime.now() - existing.requested_at).total_seconds())
        position = (
            DeviceQueue.objects.filter(
                device=dev,
                status="waiting",
                requested_at__lt=existing.requested_at,
            ).count()
            + 1
        )
        return JsonResponse(
            {
                "ok": True,
                "message": "已在排队中",
                "position": position,
                "waited_seconds": waited,
            }
        )

    # 创建排队
    entry = DeviceQueue.objects.create(
        device=dev,
        user_id=user_id,
        status="waiting",
    )

    position = (
        DeviceQueue.objects.filter(
            device=dev,
            status="waiting",
            requested_at__lt=entry.requested_at,
        ).count()
        + 1
    )

    return JsonResponse(
        {
            "ok": True,
            "message": f"已加入 {serial} 的排队队列",
            "position": position,
            "waited_seconds": 0,
        }
    )


@csrf_exempt
def leave_device_queue(request, serial):
    """DELETE /api/devices/{serial}/queue — 取消排队。"""
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    user_id = data.get("user_id", "").strip()

    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 未注册",
            },
            status=404,
        )

    # 取消排队
    qs = DeviceQueue.objects.filter(device=dev, status="waiting")
    if user_id:
        qs = qs.filter(user_id=user_id)

    updated = qs.update(status="cancelled")

    return JsonResponse(
        {
            "ok": True,
            "cancelled": updated,
        }
    )
