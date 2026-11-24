"""
模块功能：➡️ UI 层级节点 — dump 输出的数据契约（D-2：Node 归属 models/） 🏁
Python 调试：➡️ python -m backend.models.ui_nodes 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 models 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from dataclasses import dataclass, field


@dataclass
class Node:
    """标准 UI 节点（对应 u2 XML 一个 node 元素）。"""

    depth: int
    class_name: str
    text: str
    content_desc: str
    resource_id: str
    package: str
    index: str
    bounds: str  # "[l,t][r,b]"
    x: int
    y: int
    width: int
    height: int
    clickable: bool
    enabled: bool
    scrollable: bool
    checkable: bool
    checked: bool
    focusable: bool
    long_clickable: bool
    # 预留字段：候选 XPath 由外部填充，层级解析本身不生成
    xpaths: list[str] = field(default_factory=list)
