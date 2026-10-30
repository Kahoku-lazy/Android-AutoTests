"""
文件名: ➡️ tool_base.py 🏁
路径: ➡️ engines/agents/tools/tool_base.py 🏁
模块功能：➡️ 工具规格：名字、处理函数、是否只读、是否自动放行 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_base 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. ToolSpec: 平台工具（框架无关：纯函数 + 元数据）
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolSpec:
    """平台工具（框架无关：纯函数 + 元数据）。"""

    name: str
    handler: Callable[..., str]
    read_only: bool = True
    auto_allow: bool = False
