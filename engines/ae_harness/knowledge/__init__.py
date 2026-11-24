"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/knowledge/__init__.py 🏁
模块功能：➡️ 独立知识库模块的包入口：只导出检索工具装配 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_knowledge_tools: 产出只读检索工具，由调用方挂到 Agent。
2. 本模块不 import Harness 其它子包：整目录删除不影响 adb 工具、角色、事件与 SOP。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.tool: 工具实现。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from .tool import build_knowledge_tools

__all__ = ["build_knowledge_tools"]
