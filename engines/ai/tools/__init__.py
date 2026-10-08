"""工具包（叶子）—— `ToolSpec` → 框架工具 / `Toolkit` 的唯一构造点。

平台工具函数本体在后端（引擎 MUST NOT import `apps.*`），本包只做框架侧包装与装配：
工具与技能在此装载；MCP 客户端与工具组将来只在此接线（见变更设计 D6）。
"""

from .tool_wrapper import PlatformFunctionTool, build_toolkit

__all__ = ["PlatformFunctionTool", "build_toolkit"]
