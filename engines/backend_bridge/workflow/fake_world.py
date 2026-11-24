"""
文件名: ➡️ fake_world.py 🏁
路径: ➡️ engines/backend_bridge/workflow/fake_world.py 🏁
模块功能：➡️ 评测用的同名假工具 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.fake_world 🏁
时间：➡️ 2026-11-18 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. scripted_tools: 按勾选复制工具名与入参形状，调用只记账并返回剧本。
2. 不调用 adb、用例库或文档实现。
🏁
关联模块：➡️
1. engines.backend_bridge.agents.tool_selection: 导入 select_tools，取出真工具的名字与入参。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_fake_world.py: 同名、只记账、无真实副作用
🏁
"""

from __future__ import annotations

import json

from engines.ae_harness.tools.scripted import scripted_tool
from engines.backend_bridge.agents.tool_selection import select_tools

__all__ = ["scripted_tools"]


def scripted_tools(
    selections: list[dict] | None, script: dict, calls: list[dict], *, kind: str = "ui_automation"
) -> list:
    """
    按勾选复制出同名假工具。

    Args:
        selections: 名片上的工具勾选。
        script: 工具名到返回正文的映射；没有条目时返回一条固定观察。
        calls: 调用记录列表，函数会往里面追加。
        kind: 工作流种类，用来过滤工具域。

    Returns:
        与勾选同名的假工具列表。
    """
    fakes = []
    for real in select_tools(selections, kind=kind):
        fakes.append(_one(real.name, dict(real.input_schema or {}), script, calls))
    return fakes


def _one(name: str, schema: dict, script: dict, calls: list[dict]):
    """做一个只记账的假工具。名字写进默认参数，避免循环里串名。"""

    async def respond(_tool_name: str = name, **kwargs) -> str:
        calls.append({"tool": _tool_name, "input": kwargs})
        body = script.get(_tool_name) or "假世界：动作已记录，没有触达真实设备。"
        return json.dumps({"status": True, "text": body}, ensure_ascii=False)

    return scripted_tool(name, schema, respond)
