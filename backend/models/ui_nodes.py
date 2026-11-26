from dataclasses import dataclass, field


@dataclass
class Node:
    depth: int
    class_name: str
    text: str
    content_desc: str
    resource_id: str
    package: str
    index: str
    bounds: str
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
    xpaths: list[str] = field(default_factory=list)
