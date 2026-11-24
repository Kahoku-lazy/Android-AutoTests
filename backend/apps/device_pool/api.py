__all__ = [
    "acquire_device",
    "device",
    "ensure_device",
    "get_online_devices",
    "list_devices",
    "release_device",
    "release_device_locks_for_device",
    "use_device",
]

from datetime import datetime

from django.conf import settings
from django.db import transaction

from .contracts import (
    RUNNER_OCCUPIED_PREFIXES,
    ConnectionType,
    DeviceStatus,
    LockReleaseReason,
    LockStatus,
)
from .manager import serializer, state_machine
from .models import Device, DeviceLock
from .pool import device


def get_online_devices():
    return list(Device.objects.filter(status=DeviceStatus.ONLINE))


def list_devices(user_id: str = "") -> list[dict]:
    admin_ids = serializer.resolve_admin_ids(settings.ADMIN_USERS)
    devices = [
        d for d in Device.objects.all() if serializer.is_device_visible(d, user_id, admin_ids)
    ]
    status_order = {DeviceStatus.ONLINE: 0, DeviceStatus.BUSY: 1}
    devices.sort(key=lambda d: status_order.get(d.status, 99))

    owner_ids = (
        {d.locked_by for d in devices if d.locked_by}
        | {d.added_by for d in devices if d.added_by}
        | {d.occupied_by for d in devices if d.occupied_by}
    )
    id_to_name = serializer.usernames_by_ids(owner_ids)
    return [serializer.device_to_dict(d, device.current_serial, id_to_name) for d in devices]


def ensure_device(serial, name=""):
    obj, _ = Device.objects.get_or_create(
        serial=serial,
        defaults={
            "name": name,
            "connection_type": ConnectionType.WIFI if ":" in serial else ConnectionType.USB,
        },
    )
    return obj


@transaction.atomic
def acquire_device(serial, user_id, timeout=300):
    device_obj = Device.objects.select_for_update().get(serial=serial)

    if device_obj.status == DeviceStatus.BUSY:
        active_lock = (
            DeviceLock.objects.filter(
                device=device_obj, lock_type="process", status=LockStatus.ACTIVE
            )
            .order_by("-locked_at")
            .first()
        )
        if active_lock and not active_lock.is_expired:
            if str(device_obj.occupied_by) != str(user_id):
                raise ValueError(
                    f"设备已被 {device_obj.occupied_by or 'unknown'} 占用，"
                    f"剩余 {active_lock.remaining_seconds} 秒"
                )

    now = datetime.now()
    device_obj.status = DeviceStatus.BUSY
    device_obj.occupied_by = user_id
    device_obj.occupied_at = now
    device_obj.save(update_fields=["status", "occupied_by", "occupied_at"])

    DeviceLock.objects.create(
        device=device_obj,
        user_id=user_id,
        lock_type="process",
        timeout_seconds=timeout,
        status=LockStatus.ACTIVE,
    )

    return {
        "serial": serial,
        "user_id": user_id,
        "locked_at": now,
        "timeout": timeout,
    }


def release_device(serial, reason=LockReleaseReason.MANUAL):
    try:
        dev = Device.objects.get(serial=serial)
        if dev.status == DeviceStatus.BUSY:
            state_machine.release_internal(dev, reason=reason)
            return True
    except Device.DoesNotExist:
        pass
    return False


def release_device_locks_for_device(device_obj, reason=LockReleaseReason.DISCONNECT):
    return DeviceLock.objects.filter(
        device=device_obj, lock_type="process", status=LockStatus.ACTIVE
    ).update(
        status=LockStatus.RELEASED,
        released_at=datetime.now(),
        release_reason=reason,
    )


def _resolve_device(serial: str) -> Device:
    if not serial:
        raise ValueError("未选择设备，请先连接设备")
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist as exc:
        raise ValueError("设备未注册") from exc

    if dev.status == DeviceStatus.BUSY and dev.occupied_by:
        for prefix in RUNNER_OCCUPIED_PREFIXES:
            if str(dev.occupied_by).startswith(prefix):
                raise ValueError(f"设备正被执行引擎占用（{dev.occupied_by}），请等待执行完毕")
    return dev


def use_device(serial: str) -> None:
    _resolve_device(serial)
    if device.current_serial != serial:
        device.switch_to(serial)
