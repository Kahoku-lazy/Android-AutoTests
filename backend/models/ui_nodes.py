"""UI 层级节点 — dump 输出的数据契约（D-2：Node 归属 models/）。

当前实现：引擎只产出层级原始 XML；平台的层级解析、XPath 生成与分层分组实现均已下线，
本模块的 Node 结构没有平台消费者，保留为数据契约；是否退役另行评估。
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
