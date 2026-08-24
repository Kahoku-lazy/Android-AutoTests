"""UI 层级节点 — dump 输出与 XPath 算法的数据契约（D-2：Node 归属 models/）。

engines/ 将 u2 XML 解析为 Node 列表（构造职责在 engines 或 algorithms/hierarchy，
本模块只定义结构）；`xpaths` 由 algorithms/xpath 填充。
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
    xpaths: list[str] = field(default_factory=list)  # 由 algorithms/xpath 填充，解析不生成
