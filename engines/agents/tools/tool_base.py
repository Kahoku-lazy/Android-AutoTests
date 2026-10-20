"""工具规格：名字、处理函数、是否只读、是否自动放行。"""

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
