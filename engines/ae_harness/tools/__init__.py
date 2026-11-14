"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/tools/__init__.py 🏁
模块功能：➡️ 工具包门面：当前只提供 adb 一组 🏁
Python 调试：➡️ python -m engines.ae_harness.tools 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_adb_tools: 全部 adb 工具，供创建后逐个挂载。
2. build_adb_readonly_tools: 只读子集，供验收角色使用。
🏁
关联模块：➡️
1. engines.ae_harness.tools.adb: adb 工具实现。
🏁
测试：➡️
1. python -m engines.ae_harness.tools.adb.tools
🏁
"""

from __future__ import annotations

from .adb import build_adb_readonly_tools, build_adb_tools

__all__ = ["build_adb_readonly_tools", "build_adb_tools"]
