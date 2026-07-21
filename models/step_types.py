"""
Atomic step types for data-driven test cases.
Migrated from sku_stress_test — core primitives for building executable test sequences.
"""
from enum import Enum
from dataclasses import dataclass, field


class StepType(Enum):
    """Atomic step types — single source of truth for all step definitions.

    This enum is the authoritative registry. Executor dispatch, frontend
    step-utils, adapter methods, and all documentation MUST reference these values.
    """
    # 点击类
    CLICK = "click"                       # 点击元素
    LONG_CLICK = "long_click"             # 长按元素
    # 滑动类
    SWIPE = "swipe"                       # 滑动屏幕（direction + distance）
    # 等待类
    WAIT = "wait"                         # 等待元素出现
    WAIT_DISAPPEAR = "wait_disappear"     # 等待元素出现后消失
    SLEEP = "sleep"                       # 固定等待（秒）
    # 断言类
    VERIFY_TEXT = "verify_text"           # 验证元素文本
    POLL_TEXT = "poll_text"               # 轮询等待文本变为期望值
    # 应用控制类
    START_APP = "start_app"               # 启动APP
    KILL_APP = "kill_app"                 # 杀掉APP
    # 性能测试类
    PERF_ELEMENT_TIME = "perf_element_time"  # APP性能: 等待元素出现耗时
    # 弹窗检测类
    WAIT_TOAST = "wait_toast"               # 等待Toast消息
    # 流程控制类 — 判断分支
    IF_ELEMENT_APPEAR = "if_element_appear"     # 如果元素出现，执行子步骤
    IF_ELEMENT_DISAPPEAR = "if_element_disappear"  # 如果元素消失，执行子步骤
    # 流程控制类 — 循环
    LOOP_N = "loop_n"                       # 重复执行子步骤N次
    LOOP_ELEMENTS = "loop_elements"         # 遍历元素列表依次执行


UI_LABELS = {
    StepType.CLICK: "点击元素",
    StepType.LONG_CLICK: "长按元素",
    StepType.SWIPE: "滑动屏幕",
    StepType.WAIT: "等待元素出现",
    StepType.WAIT_DISAPPEAR: "等待元素消失",
    StepType.SLEEP: "固定等待",
    StepType.VERIFY_TEXT: "验证文本",
    StepType.POLL_TEXT: "轮询文本",
    StepType.START_APP: "启动应用",
    StepType.KILL_APP: "关闭应用",
    StepType.PERF_ELEMENT_TIME: "等待元素出现耗时",
    StepType.WAIT_TOAST: "等待Toast消息",
    StepType.IF_ELEMENT_APPEAR: "如果元素出现",
    StepType.IF_ELEMENT_DISAPPEAR: "如果元素消失",
    StepType.LOOP_N: "循环N次",
    StepType.LOOP_ELEMENTS: "遍历元素列表",
}

# Reverse mapping: step type value string → StepType enum
STEP_TYPE_MAP: dict[str, StepType] = {st.value: st for st in StepType}


@dataclass
class TestStep:
    """A single atomic step in a test case.

    Fields:
        type:       StepType value string (e.g. "click", "wait", "verify_text")
        xpath:      Primary XPath locator; also used as package name for start_app/kill_app
        xpath2:     Secondary XPath (reserved for future use)
        timeout:    Timeout in seconds
        expected_text: Expected text content (verify_text / poll_text)
        index:      Multi-purpose index —
                    - wait / poll_text: polling interval in seconds
        direction:  Swipe direction (up/down/left/right)
        distance:   Swipe distance in pixels
        description: Human-readable description for the step
    """
    type: str = "click"          # StepType value
    xpath: str = ""              # Primary XPath
    xpath2: str = ""             # Secondary XPath (reserved)
    timeout: float = 10          # Timeout in seconds
    expected_text: str = ""      # Expected text (verify_text / poll_text)
    index: int = 0               # Multi-purpose index
    direction: str = ""          # Swipe direction (up/down/left/right)
    distance: int = 500          # Swipe distance in pixels
    description: str = ""        # Human-readable step description
    children: list = field(default_factory=list)  # Nested sub-steps (for if/loop containers)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "xpath": self.xpath,
            "xpath2": self.xpath2,
            "timeout": self.timeout,
            "expected_text": self.expected_text,
            "index": self.index,
            "direction": self.direction,
            "distance": self.distance,
            "description": self.description,
            "children": [c.to_dict() for c in self.children] if self.children else [],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TestStep":
        children_raw = d.get("children", [])
        children = [cls.from_dict(c) for c in children_raw] if children_raw else []
        return cls(
            type=d.get("type", "click"),
            xpath=d.get("xpath", ""),
            xpath2=d.get("xpath2", ""),
            timeout=d.get("timeout", 10),
            expected_text=d.get("expected_text", ""),
            index=d.get("index", 0),
            direction=d.get("direction", ""),
            distance=d.get("distance", 500),
            description=d.get("description", ""),
            children=children,
        )
