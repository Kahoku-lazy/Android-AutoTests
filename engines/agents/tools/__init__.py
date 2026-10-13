"""工具包 —— `ToolSpec` → 框架工具 / `Toolkit` 的构造点。

设备动作在 `tool_device`，设备日志在 `tool_serial`。
日志工具只在判断端口是否关闭监听时咨询平台开关，不在这里启动采集。
"""

from .tool_wrapper import PlatformFunctionTool, build_toolkit

__all__ = ["PlatformFunctionTool", "build_toolkit"]
