"""Execution pre-flight device check — 经 U2Engine 建立 uiautomator2 连接。

L1c 收敛（consolidate-airtest-u2-engine）：连接细节（adb connect / Airtest / u2 /
超时调优 / display 验证）已迁入 engines/android/airtest_u2.py，本模块保留执行编排
（池查询、45s 总超时、日志回调、DeviceConnection 兼容壳）。
"""

from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from typing import Callable, Optional

from engines.device.base import EngineConnectError
from engines.device.registry import get_device_engine

logger = logging.getLogger(__name__)

# adb connect(10s) + Android init(5s) + u2.connect(15s) + display_info + margin
DEVICE_CHECK_TIMEOUT = 45


@dataclass
class DeviceConnection:
    """Holds the UiEngine reference for a single serial."""

    serial: str
    engine: object


class DeviceCheckError(Exception):
    """Device check failed."""


def _query_pool_device(serial: str):
    """Query device pool for serial. Raises DeviceCheckError if not found.

    L1b 收敛：设备状态仅 ONLINE/BUSY 两态（离线即删除记录），
    原 OFFLINE/DISCONNECTED 幽灵状态检查为死分支，已删除。
    """
    from apps.device_pool.models import Device as PoolDevice

    try:
        dev = PoolDevice.objects.get(serial=serial)
    except PoolDevice.DoesNotExist:
        raise DeviceCheckError(
            f"Device {serial} not registered in pool. Add it in Device Management first."
        ) from None

    return dev


def check_and_connect(
    serial: str,
    on_log: Optional[Callable[[str], None]] = None,
) -> DeviceConnection:
    """Synchronous device connection (u2).

    Runs in thread pool. on_log must not block the event loop (string collection only).

    Returns:
        DeviceConnection with a u2 reference

    Raises:
        DeviceCheckError: Any step fails
    """

    def log(msg: str):
        if on_log:
            on_log(msg)

    log(f"🔍 Pre-flight device check: {serial}")

    # ① Query device pool status
    log("  ① Query device pool status…")
    dev = _query_pool_device(serial)
    conn = dev.connection_type or ("WIFI" if ":" in serial else "USB")
    name = dev.name or dev.model or serial
    log(f"  ✓ Pool: {dev.status} · {conn} · {name}")

    # ②~⑤ 连接细节由引擎完成（进度日志经 on_log 回传）
    engine = get_device_engine()
    try:
        engine.connect(serial, dev.connection_addr or serial, on_log=log)
    except EngineConnectError as e:
        raise DeviceCheckError(str(e)) from e

    log("✅ Pre-flight check passed, starting test execution")
    return DeviceConnection(serial=serial, engine=engine)


async def _flush_check_logs(run_id: str, callbacks, messages: list[str]):
    """Batch-push collected check logs to WebSocket after thread-pool work completes."""
    for msg in messages:
        await callbacks.on_log(run_id, msg)


async def check_and_connect_async(
    serial: str,
    run_id: str,
    callbacks,
    executor,
    timeout: float = DEVICE_CHECK_TIMEOUT,
) -> DeviceConnection:
    """Async wrapper: run dual-connection check in thread pool, push logs via WebSocket."""
    loop = asyncio.get_event_loop()
    collected: list[str] = []

    def do_check():
        return check_and_connect(serial, on_log=collected.append)

    err: Optional[BaseException] = None
    device_conn = None
    try:
        device_conn = await asyncio.wait_for(
            loop.run_in_executor(executor, do_check),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        err = DeviceCheckError(f"Device check timed out ({int(timeout)}s). Verify ADB/Airtest/u2.")
    except DeviceCheckError as e:
        err = e
    except Exception as e:
        err = DeviceCheckError(str(e))

    await _flush_check_logs(run_id, callbacks, collected)

    if err is not None:
        raise err
    assert device_conn is not None  # err is None only when device_conn was successfully assigned
    return device_conn
