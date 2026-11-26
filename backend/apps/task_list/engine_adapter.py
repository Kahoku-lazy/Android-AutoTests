from __future__ import annotations

__all__ = ["resolve_device_serial"]


def resolve_device_serial(task_device_serial: str = "") -> str:
    serial = str(task_device_serial or "").strip()
    if serial:
        return serial

    from backend.apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        raise ValueError("无可用设备：任务未指定设备 serial，且当前没有在线设备")

    first_serial = str(getattr(devices[0], "serial", "") or "").strip()
    if not first_serial:
        raise ValueError("无可用设备：在线设备缺少 serial")
    return first_serial
