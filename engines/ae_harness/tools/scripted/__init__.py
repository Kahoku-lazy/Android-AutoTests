"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/tools/scripted/__init__.py 🏁
模块功能：➡️ 按名字与入参形状构造一个只回放文本的假工具 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.scripted 🏁
时间：➡️ 2026-11-19 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. scripted_tool: 调用时执行调用方给的函数，并把返回正文包成一个文本块。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 agentscope 的工具类型。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_scripted_tool.py: 工具名、入参形状与返回正文
🏁
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from agentscope.message import TextBlock
from agentscope.tool import FunctionTool, ToolChunk

__all__ = ["scripted_tool"]


def scripted_tool(
    name: str,
    input_schema: dict,
    respond: Callable[..., Awaitable[str]],
) -> FunctionTool:
    """
    构造一个按给定名字与入参形状回放文本的工具。

    Args:
        name: 工具名，调用方按这个名字挂载与识别。
        input_schema: 入参形状；空字典时不限制。
        respond: 收到入参后返回正文的异步函数。

    Returns:
        只回放一段文本的工具。
    """

    async def run(**kwargs: object) -> ToolChunk:
        text = await respond(**kwargs)
        return ToolChunk(content=[TextBlock(type="text", text=str(text))])

    return FunctionTool(
        run,
        name=name,
        description=f"评测假世界：{name}",
        input_schema=input_schema or None,
    )
