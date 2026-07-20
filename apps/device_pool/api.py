"""device-pool public API.

共享给其他模块（element-locator, test-runner, report-generator）使用。
遵循防火墙 #2：跨 App 写操作必须走此 API。
"""

from datetime import datetime
from django.db import transaction
from .models import Device, DeviceLock, DeviceQueue
from .pool import DevicePool, device


# ── Query helpers ──


def get_online_devices():
    """Get all online devices (status=ONLINE)."""
    return list(Device.objects.filter(status="ONLINE"))


def get_busy_devices():
    """Get all busy devices (status=BUSY)."""
    return list(Device.objects.filter(status="BUSY"))


def get_device_by_serial(serial: str) -> dict | None:
    """Get full device info dict for a serial, or None."""
    try:
        dev = Device.objects.get(serial=serial)
        return {
            "id": dev.id,
            "serial": dev.serial,
            "name": dev.name,
            "model": dev.model,
            "brand": dev.brand,
            "screen_w": dev.screen_w,
            "screen_h": dev.screen_h,
            "android_version": dev.android_version,
            "connection_type": dev.connection_type,
            "status": dev.status,
            "locked_by": dev.locked_by,
            "locked_at": dev.locked_at,
            "last_seen": dev.last_seen,
        }
    except Device.DoesNotExist:
        return None


def get_current_device_info():
    """Get info dict for the current device (from DevicePool cache)."""
    return device.info()


def get_device_info(serial: str) -> dict:
    """Get device info from DB + u2, merging both sources."""
    info = {}
    try:
        dev = Device.objects.get(serial=serial)
        info = {
            "serial": dev.serial,
            "model": dev.model,
            "brand": dev.brand,
            "screen_w": dev.screen_w,
            "screen_h": dev.screen_h,
            "status": dev.status,
        }
    except Device.DoesNotExist:
        pass
    # Fallback to u2 if no DB record
    if not info.get("model"):
        try:
            import uiautomator2 as u2

            d = u2.connect(serial)
            u2_info = d.info
            info["model"] = u2_info.get("productName", "")
            info["screen_w"] = u2_info.get("displayWidth", 0)
            info["screen_h"] = u2_info.get("displayHeight", 0)
        except Exception:
            pass
    return info


# ── Write helpers ──


def ensure_device(serial, name=""):
    """Get or create a device record (backward-compatible)."""
    obj, _ = Device.objects.get_or_create(
        serial=serial,
        defaults={
            "name": name,
            "connection_type": "WIFI" if ":" in serial else "USB",
        },
    )
    return obj


@transaction.atomic
def acquire_device(serial, user_id, timeout=300):
    """Lock a device for a user (v2 — creates audit trail).

    Returns: dict with lock info, or raises ValueError on conflict.
    """
    device_obj = Device.objects.get(serial=serial)

    # Check existing process occupation
    if device_obj.status == "BUSY":
        active_lock = (
            DeviceLock.objects.filter(device=device_obj, lock_type="process", status="active")
            .order_by("-locked_at")
            .first()
        )
        if active_lock and not active_lock.is_expired:
            if device_obj.occupied_by != user_id:
                raise ValueError(
                    f"设备已被 {device_obj.occupied_by or 'unknown'} 占用，"
                    f"剩余 {active_lock.remaining_seconds} 秒"
                )

    now = datetime.now()
    device_obj.status = "BUSY"
    device_obj.occupied_by = user_id  # process occupation
    device_obj.occupied_at = now
    device_obj.save(update_fields=["status", "occupied_by", "occupied_at"])

    DeviceLock.objects.create(
        device=device_obj,
        user_id=user_id,
        lock_type="process",
        timeout_seconds=timeout,
        status="active",
    )

    return {
        "serial": serial,
        "user_id": user_id,
        "locked_at": now,
        "timeout": timeout,
    }


def release_device(serial, reason="manual"):
    """Release a locked device (v2 — preserves audit trail).

    Marks DeviceLock as released instead of deleting.
    """
    from .views import _release_internal

    try:
        dev = Device.objects.get(serial=serial)
        if dev.status == "BUSY":
            _release_internal(dev, reason=reason)
            return True
    except Device.DoesNotExist:
        pass
    return False


# ── Queue helpers (v2) ──


def join_device_queue(serial, user_id):
    """Add a user to the device wait queue.

    Returns: dict with position and waited_seconds.
    """
    dev = Device.objects.get(serial=serial)

    # Check for existing waiting entry
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
        return {"position": position, "waited_seconds": waited}

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
    return {"position": position, "waited_seconds": 0}


def leave_device_queue(serial, user_id=None):
    """Cancel queue entries for a device (optionally per user).

    Returns: number of entries cancelled.
    """
    dev = Device.objects.get(serial=serial)
    qs = DeviceQueue.objects.filter(device=dev, status="waiting")
    if user_id:
        qs = qs.filter(user_id=user_id)
    return qs.update(status="cancelled")


def get_queue_for_device(serial):
    """Get queue entries for a device."""
    return list(
        DeviceQueue.objects.filter(device__serial=serial, status="waiting").order_by("requested_at")
    )


__all__ = [
    "Device",
    "DeviceLock",
    "DeviceQueue",
    "DevicePool",
    "device",
    "get_online_devices",
    "get_busy_devices",
    "get_device_by_serial",
    "get_current_device_info",
    "get_device_info",
    "ensure_device",
    "acquire_device",
    "release_device",
    "join_device_queue",
    "leave_device_queue",
    "get_queue_for_device",
]
