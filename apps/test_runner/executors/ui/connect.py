"""Execution pre-flight device check — dual Airtest + uiautomator2 connection.

Creates independent connections (not via DevicePool singleton) for test execution
isolation. Airtest for device operations, u2 kept for XPath element location.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess

from dataclasses import dataclass, field
from typing import Callable, Optional

import uiautomator2 as u2

from airtest.core.android.android import Android

logger = logging.getLogger(__name__)

# adb connect(10s) + Android init(5s) + u2.connect(15s) + display_info + margin
DEVICE_CHECK_TIMEOUT = 45

# Single u2 HTTP operation timeout ceiling (seconds). u2 default HTTP_TIMEOUT=300,
# device freeze causes permanent blocking. Lowered to 20s for quick failure.
U2_OP_TIMEOUT = 20


@dataclass
class DeviceConnection:
    """Holds both Airtest and uiautomator2 device references for a single serial."""

    serial: str
    airtest: Android
    u2: u2.Device
    info: dict = field(default_factory=dict)


class DeviceCheckError(Exception):
    """Device check failed."""


def _query_pool_device(serial: str):
    """Query device pool for serial. Raises DeviceCheckError if not found or offline."""
    from apps.device_pool.models import Device as PoolDevice

    try:
        dev = PoolDevice.objects.get(serial=serial)
    except PoolDevice.DoesNotExist:
        raise DeviceCheckError(
            f"Device {serial} not registered in pool. Add it in Device Management first."
        ) from None

    if dev.status in ("OFFLINE", "DISCONNECTED"):
        raise DeviceCheckError(f"Device status is {dev.status}. Connect and confirm online first.")

    return dev


def _adb_connect(serial: str, pool_device, log: Callable[[str], None]) -> Android:
    """ADB connect for WiFi devices + Airtest init. Raises DeviceCheckError on failure."""
    if ":" in serial:
        log(f"  ② Wireless ADB: adb connect {serial}")
        try:
            result = subprocess.run(
                ["adb", "connect", serial],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                log(f"  → {output}")
            output_lower = output.lower()
            connected_keywords = ("connected", "already", "已连接", "已经连接", "成功")
            if not any(kw in output_lower for kw in connected_keywords):
                raise DeviceCheckError("ADB connect failed. Check WiFi network and device port.")
        except subprocess.TimeoutExpired:
            raise DeviceCheckError("ADB connect timed out (10s). Check network.") from None
        log("  ✓ ADB ready")
    else:
        log("  ② USB device, skip adb connect")

    log("  ③ Establish Airtest connection…")
    try:
        air_dev = Android(serialno=serial)
    except Exception as e:
        raise DeviceCheckError(f"Airtest connection failed: {e}") from e
    log("  ✓ Airtest session established")

    return air_dev


def _connect_u2(serial: str) -> u2.Device:
    """Connect uiautomator2. Raises DeviceCheckError on failure."""
    try:
        return u2.connect(serial)
    except Exception as e:
        raise DeviceCheckError(f"u2.connect failed: {e}") from e


def _tune_u2_http_timeout(u2_dev: u2.Device) -> None:
    """Lower u2 HTTP timeout to prevent permanent blocking on device freeze."""
    try:
        import uiautomator2.base as _u2base

        _u2base.HTTP_TIMEOUT = U2_OP_TIMEOUT
    except Exception:
        logger.debug("u2 HTTP timeout tuning failed, continuing")
    try:
        u2_dev.settings["wait_timeout"] = U2_OP_TIMEOUT
    except Exception:
        logger.debug("u2 HTTP timeout tuning failed, continuing")


def _verify_display(air_dev: Android, u2_dev: u2.Device, log: Callable[[str], None]) -> dict:
    """Verify Airtest connection via display_info. Raises DeviceCheckError on failure."""
    try:
        info = dict(air_dev.display_info)
        w = info.get("displayWidth", "?")
        h = info.get("displayHeight", "?")
        # display_info may not have productName/brand — enrich from u2 if needed
        try:
            u2_info = u2_dev.info
            for k in ("productName", "brand", "sdkInt"):
                if k not in info and k in u2_info:
                    info[k] = u2_info[k]
        except Exception:
            logger.debug("Failed to read extra device info via u2")
        extra = f" · {info.get('productName', '')}" if info.get("productName") else ""
        log(f"  ✓ Connection verified · {w}x{h}{extra}")
        return info
    except Exception as e:
        msg = str(e)
        if "atx-agent" in msg.lower() or "offline" in msg.lower():
            raise DeviceCheckError(
                "ATX Agent not running. Start uiautomator2 service on device."
            ) from e
        raise DeviceCheckError(f"Device verification failed: {e}") from e


def check_and_connect(
    serial: str, on_log: Optional[Callable[[str], None]] = None
) -> DeviceConnection:
    """Synchronous dual-connection: Airtest (device ops) + u2 (XPath only).

    Runs in thread pool. on_log must not block the event loop (string collection only).

    Args:
        serial: Device serial (USB or host:port for WiFi)
        on_log: Optional log callback for progress messages

    Returns:
        DeviceConnection with both airtest and u2 references

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

    # ② ADB + ③ Airtest
    air_dev = _adb_connect(serial, dev, log)

    # ④ Connect u2 (XPath only)
    log("  ④ Establish uiautomator2 connection (XPath)…")
    u2_dev = _connect_u2(serial)
    log("  ✓ u2 session established")

    # Tune u2 HTTP timeout to prevent permanent blocking on device freeze
    _tune_u2_http_timeout(u2_dev)

    # ⑤ Verify via Airtest display_info
    log("  ⑤ Verify Airtest connection (display_info)…")
    info = _verify_display(air_dev, u2_dev, log)

    log("✅ Pre-flight check passed, starting test execution")
    return DeviceConnection(serial=serial, airtest=air_dev, u2=u2_dev, info=info)


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
