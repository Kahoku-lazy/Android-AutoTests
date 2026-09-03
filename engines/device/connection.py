"""设备连接工具 — u2 探活与信息采集（框架层，上层可 import）。

只依赖 uiautomator2，不依赖具体引擎实现；上层（device_pool）经本模块 import，
不触碰 engines.device.android.* 具体实现。
"""

from __future__ import annotations

import uiautomator2 as u2

from engines.device.base import EngineConnectError

__all__ = ["fetch_device_info", "probe_u2"]


def probe_u2(addr: str) -> None:
    """u2 连接 + info 验证（设备连接入口的轻量探活）。失败抛 EngineConnectError。"""
    try:
        d = u2.connect(addr)
        _ = d.info
    except Exception as e:
        raise EngineConnectError(str(e)) from e


def fetch_device_info(addr: str) -> dict:
    """经 u2 采集设备元信息（productName/displayWidth/displayHeight/sdkInt…）。"""
    d = u2.connect(addr)
    return dict(d.info)
