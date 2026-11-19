"""
文件名: ➡️ tools.py 🏁
路径: ➡️ engines/ae_harness/tools/case_library/tools.py 🏁
模块功能: ➡️ 用例库工具目录：保存一条用例，写入动作由调用方注入 🏁
Python 调试: ➡️ python -m engines.ae_harness.tools.case_library.tools 🏁
时间: ➡️ 2026-11-18 🏁
作者: ➡️ kahoku 🏁
版本: ➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ 工具模块 🏁
简介说明: ➡️
1. bind_case_writer: 注入实际写入用例库的函数。
2. build_case_library_tools: 产出用例库工具列表。
🏁
关联模块: ➡️
1. agentscope.tool: 导入 FunctionTool。
🏁
测试: ➡️
1. tests/engines/backend_bridge/unit/test_tool_selection.py: 用例编写过滤掉设备工具
🏁
"""

from __future__ import annotations

import json

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

__all__ = ["bind_case_writer", "build_case_library_tools"]

_writer = None
_ALLOW = lambda _request: PermissionDecision(behavior=PermissionBehavior.ALLOW)


def bind_case_writer(writer) -> None:
    """注入写入函数。引擎不认识用例库，调用方负责传入。"""
    global _writer
    _writer = writer


def save_authored_case(title: str, module: str, priority: str, steps: str) -> str:
    """保存一条编写完成的用例。未注入写入函数时返回失败。"""
    if _writer is None:
        return json.dumps({"status": False, "error": "用例库未接入"}, ensure_ascii=False)
    return json.dumps(
        _writer(title=title, module=module, priority=priority, steps=steps),
        ensure_ascii=False,
    )


def build_case_library_tools() -> list[FunctionTool]:
    """用例库工具。当前只有保存一条用例。"""
    return [FunctionTool(save_authored_case, is_concurrency_safe=False, permission=_ALLOW)]


def build_case_library_readonly_tools() -> list[FunctionTool]:
    """用例库没有只读工具。验收侧不直接改库。"""
    return []
