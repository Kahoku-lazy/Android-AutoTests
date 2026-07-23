"""
Atomic step types for data-driven test cases.
Migrated from sku_stress_test — core primitives for building executable test sequences.
"""
from enum import Enum
from dataclasses import dataclass, field


class StepResult(Enum):
    """Standardized step/case execution result — replaces magic strings across executors.

    Used by executor.py, api_executor.py, web_executor.py, adapter.py, runner.py
    and all code that checks or returns execution outcomes.
    """
    PASS = "pass"
    FAIL = "fail"
    STOPPED = "stopped"
    SKIP = "skip"
    ERROR = "error"


class CaseType(Enum):
    """Test case type — single source of truth for task type discrimination.

    Maps to DB case_type fields and frontend taskType values.
    Storage is data-only and has no execution path.
    """
    UI_AUTOMATION = "ui_automation"
    API_TESTING = "api_testing"
    WEB_AUTOMATION = "web_automation"
    STORAGE = "storage"  # data management only, not executable

    @property
    def is_virtual(self) -> bool:
        """True for task types that do NOT require a physical device."""
        return self in (CaseType.API_TESTING, CaseType.WEB_AUTOMATION)

    @property
    def is_device_based(self) -> bool:
        """True for task types that require a physical Android device."""
        return self is CaseType.UI_AUTOMATION


class StepType(Enum):
    """Atomic step types — single source of truth for all step definitions.

    This enum is the authoritative registry. Executor dispatch, frontend
    step-utils, adapter methods, and all documentation MUST reference these values.
    """
    # ── UI: 点击类 ──
    CLICK = "click"                       # 点击元素
    LONG_CLICK = "long_click"             # 长按元素
    # ── UI: 滑动类 ──
    SWIPE = "swipe"                       # 滑动屏幕（direction + distance）
    # ── UI: 等待类 ──
    WAIT = "wait"                         # 等待元素出现
    WAIT_DISAPPEAR = "wait_disappear"     # 等待元素出现后消失
    SLEEP = "sleep"                       # 固定等待（秒）
    # ── UI: 断言类 ──
    VERIFY_TEXT = "verify_text"           # 验证元素文本
    POLL_TEXT = "poll_text"               # 轮询等待文本变为期望值
    # ── UI: 应用控制类 ──
    START_APP = "start_app"               # 启动APP
    KILL_APP = "kill_app"                 # 杀掉APP
    # ── UI: 性能测试类 ──
    PERF_ELEMENT_TIME = "perf_element_time"  # APP性能: 等待元素出现耗时
    # ── UI: 弹窗检测类 ──
    WAIT_TOAST = "wait_toast"               # 等待Toast消息
    # ── UI: 流程控制 — 分支 ──
    IF_ELEMENT_APPEAR = "if_element_appear"     # 如果元素出现，执行子步骤
    IF_ELEMENT_DISAPPEAR = "if_element_disappear"  # 如果元素消失，执行子步骤
    # ── UI: 流程控制 — 循环 ──
    LOOP_N = "loop_n"                       # 重复执行子步骤N次
    LOOP_ELEMENTS = "loop_elements"         # 遍历元素列表依次执行
    # ── API: 请求与验证 ──
    API_REQUEST = "api_request"             # 发送HTTP请求
    API_ASSERT = "api_assert"               # 断言响应内容
    API_SLEEP = "api_sleep"                 # 暂停等待
    API_LOG = "api_log"                     # 输出日志
    # ── Web: 浏览器操作 ──
    WEB_NAVIGATE = "web_navigate"           # 页面跳转
    WEB_CLICK = "web_click"                 # 点击元素
    WEB_FILL = "web_fill"                   # 填充输入
    WEB_TYPE = "web_type"                   # 逐字输入
    WEB_WAIT = "web_wait"                   # 等待元素/时间
    WEB_ASSERT = "web_assert"               # 验证文本
    WEB_SCREENSHOT = "web_screenshot"       # 截图
    WEB_STEP = "web_step"                   # 通用 Web 步骤


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
    # API
    StepType.API_REQUEST: "API 请求",
    StepType.API_ASSERT: "断言验证",
    StepType.API_SLEEP: "暂停等待",
    StepType.API_LOG: "输出日志",
    # Web
    StepType.WEB_NAVIGATE: "页面跳转",
    StepType.WEB_CLICK: "点击元素",
    StepType.WEB_FILL: "填充输入",
    StepType.WEB_TYPE: "逐字输入",
    StepType.WEB_WAIT: "等待",
    StepType.WEB_ASSERT: "验证文本",
    StepType.WEB_SCREENSHOT: "截图",
    StepType.WEB_STEP: "Web 步骤",
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
    # -- Web / API --
    selector: str = ""           # Web: CSS Selector
    value: str = ""              # Web: input value / API: request body text
    url: str = ""                # Web/API: request URL
    method: str = "GET"          # API: HTTP method
    headers: dict = field(default_factory=dict)   # API: request headers
    body: dict = field(default_factory=dict)      # API: request body
    extract: dict = field(default_factory=dict)   # API: variable extraction rules
    assertions: list = field(default_factory=list) # API: assertion rules
    expected_status: int = 200      # API: expected HTTP status code

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
            "selector": self.selector,
            "value": self.value,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body": self.body,
            "extract": self.extract,
            "assertions": self.assertions,
            "expected_status": self.expected_status,
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
            selector=d.get("selector", ""),
            value=d.get("value", ""),
            url=d.get("url", ""),
            method=d.get("method", "GET"),
            headers=d.get("headers", {}),
            body=d.get("body", {}),
            extract=d.get("extract", {}),
            assertions=d.get("assertions", []),
            expected_status=d.get("expected_status", 200),
        )
