"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/tools/adb/__init__.py 🏁
模块功能：➡️ adb 工具包门面：只导出工具列表装配与工具函数表 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.adb 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_adb_tools: 产出全部 16 个工具，供创建后逐个挂载。
2. build_adb_readonly_tools: 只读子集（5 个），供验收角色使用。
3. 各工具函数也可单独导入使用。
🏁
关联模块：➡️
1. engines.ae_harness.tools.adb.tools: 工具实现。
2. engines.ae_harness.tools.adb.core: adb 执行与设备选择。
🏁
测试：➡️
1. python -m engines.ae_harness.tools.adb.tools
🏁
"""

from __future__ import annotations

from .core import AdbError, DeviceInfo, adb_binary, list_devices, resolve_serial
from .tools import (
    adb_app_start,
    adb_app_state,
    adb_app_stop,
    adb_devices,
    adb_dump_ui,
    adb_input_text,
    adb_install,
    adb_long_press,
    adb_press_key,
    adb_screen_off,
    adb_screenshot,
    adb_screenshot_grid,
    adb_swipe,
    adb_tap,
    adb_uninstall,
    adb_unlock,
    build_adb_readonly_tools,
    build_adb_tools,
)

__all__ = [
    "AdbError",
    "DeviceInfo",
    "adb_app_start",
    "adb_app_state",
    "adb_app_stop",
    "adb_binary",
    "adb_devices",
    "adb_dump_ui",
    "adb_input_text",
    "adb_install",
    "adb_long_press",
    "adb_press_key",
    "adb_screen_off",
    "adb_screenshot",
    "adb_screenshot_grid",
    "adb_swipe",
    "adb_tap",
    "adb_unlock",
    "adb_uninstall",
    "build_adb_readonly_tools",
    "build_adb_tools",
    "list_devices",
    "resolve_serial",
]
