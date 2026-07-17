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
    LONG_CLICK = "long_click"             # 长按元素（1秒）
    CLICK_INDEXED = "click_indexed"       # 点击第N个元素
    RETRY_CLICK = "retry_click"           # 点击+等待重试
    # 手势类
    SWIPE = "swipe"                       # 滑动屏幕（direction + distance）
    DRAG = "drag"                         # 拖动元素（start → end 坐标）
    # 等待类
    WAIT = "wait"                         # 等待元素出现
    WAIT_DISAPPEAR = "wait_disappear"     # 等待元素出现后消失
    WAIT_ANY = "wait_any"                 # 等待两个元素之一出现
    WAIT_TOAST = "wait_toast"             # 等待Toast消息
    # 验证类
    VERIFY_TEXT = "verify_text"           # 验证元素文本
    POLL_TEXT = "poll_text"               # 轮询等待文本变为期望值
    # 应用控制类
    START_APP = "start_app"               # 启动APP
    KILL_APP = "kill_app"                 # 杀掉APP
    RESTART_APP = "restart_app"           # 重启APP
    # 工具类
    SLEEP = "sleep"                       # 固定等待
    LOG = "log"                           # 打印日志


UI_LABELS = {
    StepType.CLICK: "点击元素",
    StepType.LONG_CLICK: "长按元素",
    StepType.CLICK_INDEXED: "点击第N个元素",
    StepType.RETRY_CLICK: "点击重试",
    StepType.SWIPE: "滑动屏幕",
    StepType.DRAG: "拖动元素",
    StepType.WAIT: "等待元素出现",
    StepType.WAIT_DISAPPEAR: "等待元素消失",
    StepType.WAIT_ANY: "等待任意一个出现",
    StepType.WAIT_TOAST: "等待Toast",
    StepType.VERIFY_TEXT: "验证文本",
    StepType.POLL_TEXT: "轮询文本",
    StepType.START_APP: "启动应用",
    StepType.KILL_APP: "关闭应用",
    StepType.RESTART_APP: "重启应用",
    StepType.SLEEP: "固定等待",
    StepType.LOG: "记录信息",
}

# Reverse mapping: step type value string → StepType enum
STEP_TYPE_MAP: dict[str, StepType] = {st.value: st for st in StepType}
# Backward compat — "wait_either" was renamed to "wait_any" in v2
STEP_TYPE_MAP["wait_either"] = StepType.WAIT_ANY


@dataclass
class TestStep:
    """A single atomic step in a test case.

    Fields:
        type:       StepType value string (e.g. "click", "wait", "verify_text")
        xpath:      Primary XPath locator
        xpath2:     Secondary XPath (for wait_any: second element)
        timeout:    Timeout in seconds
        expected_text: Expected text content (verify_text / poll_text / wait_toast)
        index:      Multi-purpose index —
                    - click_indexed: which element to click (0-based)
                    - retry_click: max retry attempts
                    - wait/poll_text: polling interval in seconds
                    - wait_any: 0=normal element, >0=indexed element
                    - restart_app: kill_wait seconds
        direction:  Swipe/drag direction (up/down/left/right)
        distance:   Swipe/drag distance in pixels
        description: Human-readable description for the step
    """
    type: str = "click"          # StepType value
    xpath: str = ""              # Primary XPath
    xpath2: str = ""             # Secondary XPath (wait_any)
    timeout: float = 10          # Timeout in seconds
    expected_text: str = ""      # Expected text (verify_text / poll_text)
    index: int = 0               # Multi-purpose index
    direction: str = ""          # Swipe/drag direction (up/down/left/right)
    distance: int = 500          # Swipe/drag distance in pixels
    description: str = ""        # Human-readable step description

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
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TestStep":
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
        )
