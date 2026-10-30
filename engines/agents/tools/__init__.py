"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/tools/__init__.py 🏁
模块功能：➡️ 工具包 —— `ToolSpec` → 框架工具 / `Toolkit` 的构造点 🏁
Python 调试：➡️ python -m engines.agents.tools 🏁
时间：➡️ 2026-10-22 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. （模块无公开类/函数，见源码）
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/engines/agents/test_ocr_tool.py: 引擎 OCR 工具：实现存在、只读、且不装配给任何角色
2. tests/engines/agents/test_tool_device.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_device.py -vv -s --tb=sh
3. tests/engines/agents/test_tool_device_e2e.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_device_e2e.py -vv -s --t
4. tests/engines/agents/test_tool_img_b64.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_img_b64.py -vv --tb=shor
5. tests/engines/agents/test_xpath_action_coords.py: xpath_action 只返回文本与中心坐标，不点击
🏁
"""

from .tool_wrapper import PlatformFunctionTool, build_toolkit

__all__ = ["PlatformFunctionTool", "build_toolkit"]
