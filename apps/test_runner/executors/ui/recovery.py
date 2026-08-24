"""uiautomator2 + Airtest crash detection, health check, and reconnection.

L1c 收敛（consolidate-airtest-u2-engine）：重连实现迁入 engines/android/airtest_u2.py
（AirtestU2Engine.reconnect），本模块保留纯检测函数与常量，并保留
reconnect_* 兼容入口（签名不变，内部经引擎）。
"""

import logging
import time

from engines.android.airtest_u2 import AirtestU2Engine

logger = logging.getLogger(__name__)

# Max retries per test case on device crash
U2_CASE_RETRY_MAX = 3
# Reconnect interval (seconds)
U2_RECONNECT_INTERVAL = 2


# ── Crash Detection ──


def is_u2_crash(exc: BaseException) -> bool:
    """Detect if exception was caused by u2/ADB connection crash or timeout."""
    if isinstance(exc, ConnectionError):
        return True
    # u2 3.x error type names (detect by name to avoid import coupling)
    if type(exc).__name__ in (
        "HTTPTimeoutError",
        "HTTPError",
        "ConnectError",
        "DeviceError",
        "SessionBrokenError",
    ):
        return True
    msg = str(exc).lower()
    keywords = (
        "quit",
        "broken",
        "disconnect",
        "connection",
        "uiautomator",
        "adb",
        "socket",
        "remote end closed",
        "device offline",
        "cannot connect",
        "timeout",
        "timed out",
        "http request",
    )
    return any(k in msg for k in keywords)


def is_device_crash(exc: BaseException) -> bool:
    """Detect u2 OR Airtest crash/timeout.

    Extends is_u2_crash with Airtest-specific error patterns.
    """
    if is_u2_crash(exc):
        return True
    # Airtest error type names
    if type(exc).__name__ in (
        "AdbError",
        "AdbShellError",
        "AdbTimeoutError",
        "MinicapError",
        "MinitouchError",
        "ScreenRecorderError",
        "RotationWatcherError",
    ):
        return True
    msg = str(exc).lower()
    airtest_keywords = (
        "airtest",
        "minicap",
        "minitouch",
        "yosemite",
        "adb connection",
        "device not found",
        "screen record",
    )
    return any(k in msg for k in airtest_keywords)


# ── Health Check ──


def check_u2_alive(device) -> bool:
    """Quick probe: u2 service is responsive."""
    if device is None:
        return False
    try:
        device.info
        return True
    except Exception:
        return False


def check_device_alive(device_conn) -> bool:
    """Quick probe: Airtest device is responsive."""
    if device_conn is None:
        return False
    try:
        device_conn.airtest.display_info
        return True
    except Exception:
        return False


# ── Reconnection（兼容入口，内部经引擎）──


def reconnect_u2(serial: str):
    """Re-establish u2 connection. Raises on failure."""
    engine = AirtestU2Engine()
    engine.connect(serial)
    return engine.u2


def reconnect_device(serial: str):
    """Re-establish both Airtest and u2 connections.

    Returns a DeviceConnection-compatible object.
    """
    # Lazy import to avoid circular dependency
    from .connect import DeviceConnection

    engine = AirtestU2Engine()
    engine.connect(serial)
    return DeviceConnection(
        serial=serial, airtest=engine.airtest, u2=engine.u2, info=engine.device_info
    )


def wait_and_reconnect(serial: str, wait_seconds: float = U2_RECONNECT_INTERVAL):
    """Wait then reconnect u2, giving ATX agent recovery time."""
    time.sleep(wait_seconds)
    return reconnect_u2(serial)


def wait_and_reconnect_device(serial: str, wait_seconds: float = U2_RECONNECT_INTERVAL):
    """Wait then reconnect both Airtest + u2."""
    time.sleep(wait_seconds)
    return reconnect_device(serial)
