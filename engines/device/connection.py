"""
文件名: ➡ connection.py 🏁
路径: ➡ engines/device/connection.py 🏁
模块功能：➡ u2 探活与设备信息采集（框架层） 🏁
Python 调试：➡ python -m engines.device.connection 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. probe_u2: uiautomator2 探活
2. fetch_device_info: 采集设备信息
3. 只依赖 u2，不依赖具体引擎实现；上层（device_pool）经本模块 import
🏁
关联模块：➡
1. engines.device.action: 连接相关类型/错误
🏁
测试：➡
1. tests/device_pool/test_connectable_serials.py: 可连接序列号
2. tests/graybox/unit/test_device_contracts.py: 设备契约
🏁
"""

from __future__ import annotations

import uiautomator2 as u2

from engines.device.action import EngineConnectError

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
