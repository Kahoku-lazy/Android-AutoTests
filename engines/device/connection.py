from __future__ import annotations

import uiautomator2 as u2

from engines.device.action import EngineConnectError
from utils.adb import adb_binary

__all__ = ["fetch_device_info", "probe_u2"]


def probe_u2(addr: str) -> None:
    adb_binary()
    try:
        d = u2.connect(addr)
        _ = d.info
    except Exception as e:
        raise EngineConnectError(str(e)) from e


def fetch_device_info(addr: str) -> dict:
    adb_binary()
    d = u2.connect(addr)
    return dict(d.info)
