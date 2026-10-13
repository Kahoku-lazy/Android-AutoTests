"""工具包 —— `ToolSpec` → 框架工具 / `Toolkit` 的构造点。

工具与技能在此装载；平台工具函数本体不在引擎侧（引擎不 import `apps.*`）。
"""

from .tool_wrapper import PlatformFunctionTool, build_toolkit

__all__ = ["PlatformFunctionTool", "build_toolkit"]
