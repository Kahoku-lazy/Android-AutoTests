"""device-pool HTTP views — 12 endpoints under /api/devices/*.

v2 per PRD §6.2:
  v1 (5): list, scan, connect, disconnect, current, activate
  v2 (6): lock, release, queue, heartbeat, queue-join, queue-leave
"""

import json
import re
import subprocess
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import uiautomator2 as u2

from ..models import Device, DeviceLock, DeviceQueue
from ..pool import device as device_pool
from ..pool import DevicePool


# ═══════════════════════════════════════════════
# 核心 Helper 函数
# ═══════════════════════════════════════════════


def _adb_device_serials():
    """Return set of serials currently visible to adb."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        serials = set()
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                serials.add(parts[0])
        return serials
    except Exception:
        return set()


def _update_device_status():
    """Sync DB device status with actual ADB state.

    在 list_devices 和 heartbeat 端点中调用。

    Rules:
        - adb devices 列表中的 OFFLINE → ONLINE
        - DB 中 BUSY 但锁已超时 → 自动释放 (reason=timeout)
        - 不在 adb 列表中且非 BUSY → 标记 OFFLINE
    """
    _purge_disconnected_devices()
    now = datetime.now()
    adb_serials = _adb_device_serials()
    updated = 0
    offline = 0

    for dev in Device.objects.all():
        if dev.serial in adb_serials:
            # 设备在线
            if dev.status == "OFFLINE":
                dev.status = "ONLINE"
                dev.last_seen = now
                dev.save(update_fields=["status", "last_seen"])
                updated += 1

            # 检查 BUSY 设备的进程锁是否超时（仅 process 类型）
            if dev.status == "BUSY":
                active_lock = (
                    DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                    .order_by("-locked_at")
                    .first()
                )
                if active_lock and active_lock.is_expired:
                    _release_internal(dev, reason="timeout")
                    updated += 1
                elif active_lock:
                    # 更新 last_seen
                    dev.last_seen = now
                    dev.save(update_fields=["last_seen"])
                elif dev.locked_at:
                    # 没有 active 锁但有 locked_at（数据不一致），修复
                    elapsed = (now - dev.locked_at).total_seconds()
                    if elapsed > 300:
                        _release_internal(dev, reason="timeout")
                        updated += 1
        else:
            # 设备不在 adb 列表中
            if dev.status == "BUSY":
                # BUSY 设备可能暂时断 USB，检查进程锁超时
                active_lock = (
                    DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                    .order_by("-locked_at")
                    .first()
                )
                if active_lock and active_lock.is_expired:
                    _release_internal(dev, reason="timeout")
                    dev.status = "OFFLINE"
                    dev.save(update_fields=["status"])
                    updated += 1
                    offline += 1
                # 否则保持 BUSY（保护进行中的任务）
            else:
                dev.status = "OFFLINE"
                dev.save(update_fields=["status"])
                offline += 1

    return updated, offline


def _delete_device_record(dev, *, reason="disconnect"):
    """Remove a device row and its pool cache entry (no DISCONNECTED tombstone)."""
    serial = dev.serial
    if dev.status == "BUSY":
        _release_internal(dev, reason=reason)
    device_pool.remove_device(serial)
    dev.delete()


def _release_internal(dev, reason="manual", clear_lock=False):
    """内部释放占用：清空 occupied_by + 恢复 ONLINE。

    不删除锁记录（保留审计）。
    """
    now = datetime.now()

    # 标记活跃锁为 released（进程+用户均释放）
    DeviceLock.objects.filter(device=dev, status="active").update(
        status="released",
        released_at=now,
        release_reason=reason,
    )

    # 清空进程占用
    dev.occupied_by = ""
    dev.occupied_at = None
    update_fields = ["occupied_by", "occupied_at"]
    if dev.status == "BUSY":
        dev.status = "ONLINE"
        update_fields.append("status")
    if clear_lock:
        dev.locked_by = ""
        dev.locked_at = None
        update_fields.extend(["locked_by", "locked_at"])
    dev.save(update_fields=update_fields)

    print(f"[INFO] 设备 {dev.serial} 已释放占用 (reason={reason})")

    # 触发队列分配
    assigned = _auto_assign_from_queue(dev)
    if assigned:
        print(f"[INFO] 设备 {dev.serial} 已从队列分配给 {assigned}")


def _purge_disconnected_devices():
    """Delete legacy DISCONNECTED rows — not kept as history."""
    stale = list(Device.objects.filter(status="DISCONNECTED"))
    for dev in stale:
        _delete_device_record(dev, reason="purge")
    return len(stale)


def _collect_device_info(dev, serial):
    """通过 uiautomator2 采集设备信息并更新 Device 记录。

    采集: model, brand, screen_w, screen_h, android_version
    """
    try:
        d = u2.connect(serial)
        info = d.info
        dev.model = info.get("productName", "") or ""
        dev.brand = info.get("brand", "") or ""
        dev.screen_w = info.get("displayWidth", 0) or 0
        dev.screen_h = info.get("displayHeight", 0) or 0
        sdk = info.get("sdkInt", 0)
        dev.android_version = str(sdk) if sdk else ""
        dev.last_seen = datetime.now()
        dev.save(
            update_fields=[
                "model",
                "brand",
                "screen_w",
                "screen_h",
                "android_version",
                "last_seen",
            ]
        )
        print(
            f"[INFO] 设备信息已采集: {dev.serial} → {dev.brand} {dev.model} "
            f"{dev.screen_w}x{dev.screen_h} SDK={dev.android_version}"
        )
    except Exception as e:
        print(f"[WARN] 采集设备信息失败 {serial}: {e}")


def _auto_assign_from_queue(dev):
    """释放后从队列中分配第一个等待用户。

    Returns: 被分配的用户 ID，或 None（队列为空）。
    """
    entry = (
        DeviceQueue.objects.filter(device=dev, status="waiting").order_by("requested_at").first()
    )

    if not entry:
        return None

    entry.status = "assigned"
    entry.assigned_at = datetime.now()
    entry.save(update_fields=["status", "assigned_at"])

    # 自动绑定用户
    dev.locked_by = entry.user_id
    dev.locked_at = datetime.now()
    dev.save(update_fields=["locked_by", "locked_at"])

    DeviceLock.objects.create(
        device=dev,
        user_id=entry.user_id,
        lock_type="user",
        timeout_seconds=300,
        status="active",
    )

    return entry.user_id


def _check_timeout_queue():
    """清理超过 600 秒未响应的排队记录。"""
    cutoff = datetime.now() - timedelta(seconds=600)
    expired = DeviceQueue.objects.filter(status="waiting", requested_at__lt=cutoff).update(
        status="timeout"
    )
    if expired:
        print(f"[INFO] {expired} 条排队记录超时自动取消")


def _device_to_dict(dev, current_serial):
    """将 Device ORM 对象转为 PRD §6.2.1 响应格式。"""
    now = datetime.now()
    result = {
        "id": dev.id,
        "serial": dev.serial,
        "name": dev.name,
        "model": dev.model,
        "brand": dev.brand,
        "screen": f"{dev.screen_w}x{dev.screen_h}" if dev.screen_w else "",
        "status": dev.status,
        "connection_type": dev.connection_type or ("WIFI" if ":" in dev.serial else "USB"),
        "locked_by": dev.locked_by,
        "locked_at": dev.locked_at.isoformat() if dev.locked_at else None,
        "occupied_by": dev.occupied_by,
        "occupied_at": dev.occupied_at.isoformat() if dev.occupied_at else None,
        "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
        "is_current": dev.serial == current_serial,
    }

    # BUSY 设备：计算剩余时间（进程占用，非用户绑定）
    if dev.status == "BUSY" and (dev.occupied_by or dev.locked_by):
        active_lock = (
            DeviceLock.objects.filter(device=dev, status="active").order_by("-locked_at").first()
        )
        if active_lock:
            result["remaining"] = active_lock.remaining_seconds
            result["locked_by"] = dev.locked_by
        else:
            result["remaining"] = 0
    else:
        result["remaining"] = 0

    return result


# ═══════════════════════════════════════════════
# v1 endpoints (5)
# ═══════════════════════════════════════════════


