"""
模块功能：➡️ 只读文档工具门面：导出只读文档工具列表装配 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.document 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（只读工具权限由 tests/arch/unit 的契约守护覆盖）
🏁
"""

from .tools import bind_requirement_text, build_document_tools

__all__ = ["bind_requirement_text", "build_document_tools"]
