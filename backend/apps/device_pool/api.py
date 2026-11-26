__all__ = [
    "activate_device",
    "connect_device",
    "disconnect_device",
    "get_online_devices",
    "heartbeat_sync",
    "list_connectable_serials",
    "list_devices",
    "register_connected_device",
    "release_observe",
    "release_occupy",
    "scan_all_devices",
    "scan_and_register",
    "set_device_lock",
    "sync_device_status",
]

from django.conf import settings

from .contracts import ConnectionType, DeviceError, DeviceStatus, LockReleaseReason
from .manager import detector, registry, serializer, state_machine
from .models import Device
from .pool import device


def get_online_devices():
    return list(Device.objects.filter(status=DeviceStatus.ONLINE))


def sync_device_status() -> tuple[int, int]:
    return state_machine.update_device_status()


def list_connectable_serials() -> set[str]:
    return detector.connectable_serials()


def _get_device(serial: str) -> Device:
    if not serial:
        raise DeviceError("未选择设备，请先连接设备", status_code=400)
    try:
        return Device.objects.get(serial=serial)
    except Device.DoesNotExist as exc:
        raise DeviceError(f"设备 {serial} 未注册", status_code=404) from exc


def list_devices(user_id: str = "") -> dict:
    sync_device_status()

    admin_ids = serializer.resolve_admin_ids(settings.ADMIN_USERS)
    devices = [
        d for d in Device.objects.all() if serializer.is_device_visible(d, user_id, admin_ids)
    ]
    status_order = {DeviceStatus.ONLINE: 0, DeviceStatus.BUSY: 1}
    devices.sort(key=lambda d: status_order.get(d.status, 99))

    current_serial = device.current_serial
    if not current_serial:
        online = [d for d in devices if d.status in (DeviceStatus.ONLINE, DeviceStatus.BUSY)]
        if online:
            first = online[0]
            device.switch_to(first.serial)
            current_serial = first.serial

    visible_serials = {d.serial for d in devices}
    if current_serial not in visible_serials:
        current_serial = None

    owner_ids = (
        {d.locked_by for d in devices if d.locked_by}
        | {d.added_by for d in devices if d.added_by}
        | {d.occupied_by for d in devices if d.occupied_by}
    )
    id_to_name = serializer.usernames_by_ids(owner_ids)
    return {
        "devices": [serializer.device_to_dict(d, current_serial, id_to_name) for d in devices],
        "current": current_serial,
    }


def activate_device(serial: str, user_id: str = "") -> str:
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        dev, _created = registry.register_device(serial, user_id)

    if dev.status == DeviceStatus.BUSY:
        raise DeviceError("设备正在使用中，无法激活", status_code=400)

    device.switch_to(serial)
    registry.touch_last_seen(dev)
    return serial


def scan_and_register(
    addr: str, user_id: str = "", *, pair_port: str = "", pair_code: str = ""
) -> dict:
    ip = addr.partition(":")[0]
    if pair_port or pair_code:
        detector.pair(ip, pair_port, pair_code)
    detector.connect(addr)
    dev, created = registry.register_device(addr, user_id)
    state_machine.claim_wireless_device(dev, user_id)
    return {
        "newly_added": 1 if created else 0,
        "devices": [serializer.device_to_dict(dev, device.current_serial)],
    }


def register_connected_device(serial: str, user_id: str = "") -> dict:
    dev, created = registry.register_device(serial, user_id)
    return {
        "newly_added": 1 if created else 0,
        "devices": [serializer.device_to_dict(dev, device.current_serial)],
    }


def scan_all_devices(user_id: str = "") -> dict:
    adb_serials = detector.connectable_serials()
    newly_added = 0
    devices_out = []
    for addr in adb_serials:
        try:
            dev, created = registry.register_device(addr, user_id)
        except DeviceError:
            continue
        if created:
            newly_added += 1
        devices_out.append(serializer.device_to_dict(dev, device.current_serial))

    if devices_out and device.current_serial not in adb_serials:
        device.switch_to(devices_out[0]["serial"])

    return {"count": len(devices_out), "newly_added": newly_added, "devices": devices_out}


def connect_device(
    serial: str, user_id: str = "", *, activate: bool = True, mode: str = ""
) -> dict:
    dev = _get_device(serial)
    if dev.status == DeviceStatus.BUSY:
        raise DeviceError("设备正在使用中，无法连接", status_code=409)

    addr = dev.connection_addr or serial
    connection_type = ConnectionType.WIFI if detector.is_wireless(addr) else ConnectionType.USB

    detector.connect(addr)
    registry.set_connection_state(dev, connection_type)
    registry.collect_device_info(dev, addr)

    if activate:
        device.switch_to(serial)

    if mode == "observe":
        state_machine.occupy_observe(dev, user_id)

    dev.refresh_from_db()
    return {
        "serial": dev.serial,
        "model": dev.model,
        "screen_w": dev.screen_w,
        "screen_h": dev.screen_h,
        "android_version": dev.android_version,
    }


def disconnect_device(serial: str) -> None:
    dev = _get_device(serial)
    if dev.connection_type != ConnectionType.WIFI:
        raise DeviceError("USB 设备无删除键", status_code=400)
    if dev.status == DeviceStatus.BUSY:
        raise DeviceError("设备使用中，无法删除", status_code=409)
    registry.delete_device_record(dev, reason=LockReleaseReason.DISCONNECT)


def release_observe(serial: str) -> None:
    device.remove_device(serial)
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return
    state_machine.release_observe(dev)


def set_device_lock(serial: str, locked: bool, user_id: str) -> dict:
    return state_machine.set_device_lock(_get_device(serial), bool(locked), user_id)


def release_occupy(serial: str) -> dict:
    return state_machine.release_occupy(_get_device(serial))


def heartbeat_sync() -> dict:
    return state_machine.heartbeat_sync()
