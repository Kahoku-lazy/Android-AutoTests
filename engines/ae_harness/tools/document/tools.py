"""
文件名: ➡️ tools.py 🏁
路径: ➡️ engines/ae_harness/tools/document/tools.py 🏁
模块功能: ➡️ 只读文档工具：读取本次运行绑定的需求正文 🏁
Python 调试: ➡️ python -m engines.ae_harness.tools.document.tools 🏁
时间: ➡️ 2026-11-18 🏁
作者: ➡️ kahoku 🏁
版本: ➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ 工具模块 🏁
简介说明: ➡️
1. bind_requirement_text: 注入本次需求正文。
2. build_document_tools: 产出只读文档工具。
🏁
关联模块: ➡️
1. agentscope.tool: 导入 FunctionTool。
🏁
测试: ➡️
1. tests/engines/backend_bridge/unit/test_tool_selection.py: 需求拆解不挂设备工具
🏁
"""

from __future__ import annotations

import json

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

__all__ = ["bind_requirement_text", "build_document_tools"]

_text = ""
_ALLOW = lambda _request: PermissionDecision(behavior=PermissionBehavior.ALLOW)


def bind_requirement_text(text: str) -> None:
    """绑定本次运行要读取的需求正文。"""
    global _text
    _text = text or ""


def read_requirement() -> str:
    """读取本次绑定的需求正文。没有正文时返回失败。"""
    if not _text.strip():
        return json.dumps({"status": False, "error": "没有需求正文"}, ensure_ascii=False)
    return json.dumps({"status": True, "text": _text}, ensure_ascii=False)


def build_document_tools() -> list[FunctionTool]:
    """文档工具。只有读取需求，没有写操作。"""
    return [FunctionTool(read_requirement, is_read_only=True, permission=_ALLOW)]


def build_document_readonly_tools() -> list[FunctionTool]:
    """文档域全部只读，只读预设与全部预设相同。"""
    return build_document_tools()
