from __future__ import annotations

import contextlib

from collections.abc import Iterator

from engines.ae_harness.tools.adb.core import AdbError, list_devices, lock_serial, unlock_serial

__all__ = ["require_online", "serial_lock"]


def require_online(serial: str) -> str:
    clean = str(serial or "").strip()
    if not clean:
        raise ValueError("设备序列号必须由平台传入，禁止自动探测")
    try:
        devices = list_devices()
    except AdbError as exc:
        raise ValueError(f"adb 不可用：{exc}") from exc
    states = {device.serial: device.state for device in devices}
    state = states.get(clean)
    if state is None:
        names = ", ".join(states) or "无"
        raise ValueError(f"平台指定的设备 {clean} 未连接；当前连接：{names}")
    if state != "device":
        raise ValueError(f"平台指定的设备 {clean} 状态为 {state}，不可执行（需要 device）")
    return clean


@contextlib.contextmanager
def serial_lock(serial: str) -> Iterator[str]:
    token = lock_serial(serial)
    try:
        yield serial
    finally:
        unlock_serial(token)
