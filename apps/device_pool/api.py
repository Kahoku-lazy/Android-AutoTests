"""device-pool public API.

共享给其他模块（element-locator, test-runner, report-generator）使用。
遵循防火墙 #2：跨 App 写操作必须走此 API。
"""

__all__ = [
    "acquire_device",
    "device",
    "ensure_device",
    "get_online_devices",
    "release_device",
    "release_device_locks_for_device",
]

import logging

from datetime import datetime

from django.db import transaction

logger = logging.getLogger(__name__)

from .models import Device, DeviceLock
from .pool import device

# ── Query helpers ──


def get_online_devices():
    """Get all online devices (status=ONLINE)."""
    return list(Device.objects.filter(status="ONLINE"))


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
    # select_for_update() prevents concurrent processes from both passing
    # the BUSY check before either saves (row-level lock on MySQL/PostgreSQL).
    device_obj = Device.objects.select_for_update().get(serial=serial)

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


def release_device_locks_for_device(device_obj, reason="disconnect"):
    """Release all active process locks for a device (bulk — used by state recovery).

    This is the API-level entry point for releasing locks during crash recovery /
    orphan cleanup. Avoids cross-module ORM writes from test_runner or other apps.
    """
    return DeviceLock.objects.filter(
        device=device_obj, lock_type="process", status="active"
    ).update(
        status="released",
        released_at=datetime.now(),
        release_reason=reason,
    )
