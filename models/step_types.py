"""
Atomic step types for data-driven test cases.
Migrated from sku_stress_test — core primitives for building executable test sequences.
"""

from dataclasses import dataclass, field
from enum import Enum


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
    CLICK = "click"  # 点击元素
    LONG_CLICK = "long_click"  # 长按元素
    # ── UI: 滑动类 ──
    SWIPE = "swipe"  # 滑动屏幕（direction + distance）
    # ── UI: 等待类 ──
    WAIT = "wait"  # 等待元素出现
    WAIT_DISAPPEAR = "wait_disappear"  # 等待元素出现后消失
    SLEEP = "sleep"  # 固定等待（秒）
    # ── UI: 断言类 ──
    VERIFY_TEXT = "verify_text"  # 验证元素文本
    POLL_TEXT = "poll_text"  # 轮询等待文本变为期望值
    # ── UI: 应用控制类 ──
    START_APP = "start_app"  # [deprecated] 启动APP — use ADB_START_APP
    KILL_APP = "kill_app"  # [deprecated] 杀掉APP — use ADB_KILL_APP
    # ── UI: 性能测试类 ──
    PERF_ELEMENT_TIME = "perf_element_time"  # [deprecated] APP性能 — use ADB_PERF_ELEMENT_TIME
    # ── UI: 弹窗检测类 ──
    WAIT_TOAST = "wait_toast"  # [deprecated] 等待Toast — use ADB_WAIT_TOAST
    # ── UI: 流程控制 — 分支 ──
    IF_ELEMENT_APPEAR = "if_element_appear"  # [deprecated] 如果元素出现 — use ADB_IF_APPEAR
    IF_ELEMENT_DISAPPEAR = (
        "if_element_disappear"  # [deprecated] 如果元素消失 — use ADB_IF_DISAPPEAR
    )
    # ── UI: 流程控制 — 循环 ──
    LOOP_N = "loop_n"  # [deprecated] 重复执行 — use ADB_LOOP_N
    LOOP_ELEMENTS = "loop_elements"  # [deprecated] 遍历元素 — use ADB_LOOP_ELEMENTS
    # ── UI: Android 专属（adb_ 前缀 — 统一命名，与 STEP_TYPE_META 一致）──
    ADB_START_APP = "adb_start_app"  # 启动APP
    ADB_KILL_APP = "adb_kill_app"  # 杀掉APP
    ADB_WAIT_TOAST = "adb_wait_toast"  # 等待Toast消息
    ADB_PERF_ELEMENT_TIME = "adb_perf_element_time"  # 元素出现耗时
    ADB_IF_APPEAR = "adb_if_appear"  # 如果元素出现
    ADB_IF_DISAPPEAR = "adb_if_disappear"  # 如果元素消失
    ADB_LOOP_N = "adb_loop_n"  # 重复执行子步骤N次
    ADB_LOOP_ELEMENTS = "adb_loop_elements"  # 遍历元素列表
    ADB_POLL_TEXT = "adb_poll_text"  # 轮询等待文本变为期望值
    # ── API: 请求与验证 ──
    API_REQUEST = "api_request"  # 发送HTTP请求
    API_ASSERT = "api_assert"  # 断言响应内容
    API_SLEEP = "api_sleep"  # 暂停等待
    API_LOG = "api_log"  # 输出日志
    # ── Web: 浏览器操作 ──
    WEB_NAVIGATE = "web_navigate"  # 页面跳转
    WEB_CLICK = "web_click"  # 点击元素
    WEB_FILL = "web_fill"  # 填充输入
    WEB_TYPE = "web_type"  # 逐字输入
    WEB_WAIT = "web_wait"  # 等待元素/时间
    WEB_ASSERT = "web_assert"  # 验证文本
    WEB_SCREENSHOT = "web_screenshot"  # 截图
    WEB_STEP = "web_step"  # 通用 Web 步骤


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


# ═══════════════════════════════════════════════════════
# 操作类型注册表 — 全平台唯一权威数据
# 前端通过 GET /api/cases/step-types?target=xxx 拉取
# common = 所有平台通用, android = Android 专属, web = Web 专属
# ═══════════════════════════════════════════════════════
STEP_TYPE_META = {
    # ── 通用操作（模拟人的操作，所有平台共用）──
    "click": {
        "target": "common",
        "label": "点击元素",
        "icon": "👆",
        "desc": "点击匹配的单个 UI 元素",
        "group": "通用",
    },
    "long_click": {
        "target": "common",
        "label": "长按",
        "icon": "👇",
        "desc": "长按指定元素",
        "group": "通用",
    },
    "swipe": {
        "target": "common",
        "label": "滑动",
        "icon": "👈",
        "desc": "按方向滑动指定距离",
        "group": "通用",
    },
    "wait": {
        "target": "common",
        "label": "等待元素出现",
        "icon": "⏳",
        "desc": "等待指定元素出现在屏幕上",
        "group": "通用",
    },
    "sleep": {
        "target": "common",
        "label": "暂停",
        "icon": "💤",
        "desc": "固定时长暂停（秒）",
        "group": "通用",
    },
    "screenshot": {
        "target": "common",
        "label": "截图",
        "icon": "📸",
        "desc": "截取当前画面用于报告",
        "group": "通用",
    },
    # ── Android 独有操作 ──
    "verify_text": {
        "target": "android",
        "label": "验证文本",
        "icon": "✅",
        "desc": "校验元素文本是否匹配期望值",
        "group": "断言",
    },
    "adb_start_app": {
        "target": "android",
        "label": "启动 App",
        "icon": "🚀",
        "desc": "启动目标 App（package name）",
        "group": "应用",
    },
    "adb_kill_app": {
        "target": "android",
        "label": "停止 App",
        "icon": "💀",
        "desc": "强制停止目标 App",
        "group": "应用",
    },
    "adb_wait_toast": {
        "target": "android",
        "label": "等待 Toast",
        "icon": "💬",
        "desc": "等待指定文本的 Toast 消息出现",
        "group": "弹窗",
    },
    "adb_perf_element_time": {
        "target": "android",
        "label": "元素出现耗时",
        "icon": "⏱️",
        "desc": "等待元素出现并计时，超时则失败",
        "group": "性能",
    },
    "adb_if_appear": {
        "target": "android",
        "label": "如果元素出现",
        "icon": "🔀",
        "desc": "如果目标元素出现则执行子步骤，否则跳过",
        "group": "流程控制",
    },
    "adb_if_disappear": {
        "target": "android",
        "label": "如果元素消失",
        "icon": "🔀",
        "desc": "如果目标元素消失则执行子步骤，否则跳过",
        "group": "流程控制",
    },
    "adb_loop_n": {
        "target": "android",
        "label": "循环 N 次",
        "icon": "🔁",
        "desc": "重复执行子步骤 N 次",
        "group": "流程控制",
    },
    "adb_loop_elements": {
        "target": "android",
        "label": "遍历元素列表",
        "icon": "📋",
        "desc": "依次点击 XPath 列表中的每个元素",
        "group": "流程控制",
    },
    "adb_poll_text": {
        "target": "android",
        "label": "轮询文本",
        "icon": "🔄",
        "desc": "轮询等待元素文本变为期望值",
        "group": "断言",
    },
    "wait_disappear": {
        "target": "android",
        "label": "等待元素消失",
        "icon": "⌛",
        "desc": "等待元素从屏幕消失",
        "group": "等待",
    },
    # ── Web 独有操作 ──
    "web_navigate": {
        "target": "web",
        "label": "页面跳转",
        "icon": "🔗",
        "desc": "浏览器导航到指定 URL",
        "group": "导航",
    },
    "web_fill": {
        "target": "web",
        "label": "填充输入",
        "icon": "⌨️",
        "desc": "向输入框填充文本内容",
        "group": "交互",
    },
    "web_type": {
        "target": "web",
        "label": "逐字输入",
        "icon": "⌨️",
        "desc": "逐字符输入文本（模拟真实打字）",
        "group": "交互",
    },
    "web_assert": {
        "target": "web",
        "label": "验证文本",
        "icon": "✅",
        "desc": "验证页面上存在指定文本",
        "group": "断言",
    },
    "web_wait": {
        "target": "web",
        "label": "等待元素或时间",
        "icon": "⏳",
        "desc": "等待元素出现或固定时间",
        "group": "通用",
    },
    # Legacy web types (compatibility with existing DB data)
    "web_click": {
        "target": "web",
        "label": "点击元素",
        "icon": "👆",
        "desc": "点击 CSS 选择器匹配的页面元素",
        "group": "通用",
    },
    "web_screenshot": {
        "target": "web",
        "label": "截图",
        "icon": "📸",
        "desc": "截取当前页面截图",
        "group": "通用",
    },
    "web_step": {
        "target": "web",
        "label": "Web 步骤",
        "icon": "⚙️",
        "desc": "通用 Web 操作步骤",
        "group": "通用",
    },
    # ── API 独有操作 ──
    "api_request": {
        "target": "api",
        "label": "API 请求",
        "icon": "🌐",
        "desc": "发送 HTTP 请求并记录响应",
        "group": "请求",
    },
    "api_assert": {
        "target": "api",
        "label": "断言验证",
        "icon": "✅",
        "desc": "验证 API 响应内容是否符合预期",
        "group": "断言",
    },
    "api_sleep": {
        "target": "api",
        "label": "暂停等待",
        "icon": "😴",
        "desc": "暂停等待一段时间",
        "group": "通用",
    },
    "api_log": {
        "target": "api",
        "label": "输出日志",
        "icon": "📝",
        "desc": "输出自定义日志信息",
        "group": "通用",
    },
}


def get_step_types_by_target(target: str) -> list[dict]:
    """返回指定平台可用的所有操作类型。结果在模块加载时预计算，O(1) 查询。"""
    return _STEP_TYPE_CACHE.get(target, [])


# 模块加载时预计算
_STEP_TYPE_CACHE: dict[str, list[dict]] = {}
for _target in ("android", "web", "api"):
    _result = []
    for _type_val, _meta in STEP_TYPE_META.items():
        if _meta["target"] in (_target, "common"):
            _result.append(
                {
                    "value": _type_val,
                    "label": _meta["label"],
                    "icon": _meta.get("icon", ""),
                    "target": _meta["target"],
                    "desc": _meta.get("desc", ""),
                    "group": _meta.get("group", ""),
                }
            )
    _STEP_TYPE_CACHE[_target] = _result


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

    type: str = "click"  # StepType value
    xpath: str = ""  # Primary XPath
    xpath2: str = ""  # Secondary XPath (reserved)
    timeout: float = 10  # Timeout in seconds
    expected_text: str = ""  # Expected text (verify_text / poll_text)
    index: int = 0  # Multi-purpose index
    direction: str = ""  # Swipe direction (up/down/left/right)
    distance: int = 500  # Swipe distance in pixels
    description: str = ""  # Human-readable step description
    children: list = field(default_factory=list)  # Nested sub-steps (for if/loop containers)
    # -- Web / API --
    selector: str = ""  # Web: CSS Selector
    value: str = ""  # Web: input value / API: request body text
    url: str = ""  # Web/API: request URL
    method: str = "GET"  # API: HTTP method
    headers: dict = field(default_factory=dict)  # API: request headers
    body: dict = field(default_factory=dict)  # API: request body
    extract: dict = field(default_factory=dict)  # API: variable extraction rules
    assertions: list = field(default_factory=list)  # API: assertion rules
    expected_status: int = 200  # API: expected HTTP status code
    request_schema: dict = field(default_factory=dict)  # API: request body JSON Schema
    response_schema: dict = field(default_factory=dict)  # API: response body JSON Schema

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
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
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
            request_schema=d.get("request_schema", {}),
            response_schema=d.get("response_schema", {}),
        )
