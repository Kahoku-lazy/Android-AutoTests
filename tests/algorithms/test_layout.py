"""algorithms/layout — 结构分区纯函数单测。"""

import pytest

from algorithms.layout import (
    ROLE_BOTTOM_NAV,
    ROLE_CONTENT,
    ROLE_HEADER,
    ROLE_STATUS_BAR,
    ROLE_SYSTEM_NAV,
    ROLE_TAB_BAR,
    classify_structure,
    detect_webview,
    metrics,
)

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]

SCREEN_H = 3040


def el(**kw):
    """构造一个最小元素（字段与 parse_hierarchy_xml 输出对齐）。"""
    base = {
        "depth": 0,
        "class_name": "android.view.ViewGroup",
        "text": "",
        "content_desc": "",
        "resource_id": "",
        "package": "com.govee.home",
        "index": "0",
        "bounds": "[0,0][0,0]",
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
        "clickable": False,
        "enabled": True,
        "scrollable": False,
        "checkable": False,
        "checked": False,
        "focusable": False,
        "long_clickable": False,
    }
    base.update(kw)
    return base


# ── 指标聚合 ──


class TestMetrics:
    def test_empty(self):
        assert metrics(el()) == []

    def test_clickable(self):
        assert metrics(el(clickable=True)) == ["可点击"]

    def test_all_three(self):
        assert metrics(el(clickable=True, scrollable=True, checkable=True)) == [
            "可点击",
            "可滚动",
            "可勾选",
        ]


# ── WebView 识别 ──


class TestDetectWebview:
    def test_empty(self):
        assert detect_webview([]) is False

    def test_pure_webview(self):
        els = [
            el(class_name="android.webkit.WebView", y=1, height=2500),
            el(class_name="android.widget.FrameLayout", y=1, height=2500),
        ]
        assert detect_webview(els) is True

    def test_native_page(self):
        els = [
            el(class_name="android.widget.TextView", text="设备", y=110),
            el(
                class_name="android.widget.ImageView",
                resource_id="com.govee.home:id/ivSwitch",
                y=900,
            ),
        ]
        assert detect_webview(els) is False

    def test_systemui_not_counted(self):
        # 只有 systemui 元素时，不判为 WebView
        els = [el(package="com.android.systemui", class_name="android.widget.TextView", y=33)]
        assert detect_webview(els) is False


# ── 分区分类 ──


class TestClassifyStructure:
    def test_empty(self):
        assert classify_structure([]) == {"is_webview": False, "sections": [], "elements": []}

    def test_six_layers(self):
        els = [
            # 系统状态栏
            el(
                package="com.android.systemui",
                class_name="android.widget.TextView",
                text="15:30",
                y=33,
                height=117,
            ),
            # 系统导航键
            el(
                package="com.android.systemui",
                class_name="android.widget.ImageView",
                content_desc="主屏幕",
                y=2872,
                height=168,
            ),
            # App 头部标题
            el(class_name="android.widget.TextView", text="设备", y=110, height=211),
            # 顶部标签（横向 RecyclerView）
            el(
                class_name="androidx.recyclerview.widget.RecyclerView",
                resource_id="com.govee.home:id/rvRoom",
                y=352,
                height=157,
                scrollable=True,
            ),
            # 内容区元素
            el(class_name="android.widget.TextView", text="H705F", y=587, height=79),
            el(
                class_name="android.widget.ImageView",
                resource_id="com.govee.home:id/ivSwitch",
                y=901,
                height=150,
                clickable=True,
            ),
            # 底部导航
            el(
                class_name="android.widget.ImageView",
                resource_id="com.govee.home:id/ivTabDevice",
                y=2657,
                height=154,
                clickable=True,
            ),
        ]
        result = classify_structure(els, SCREEN_H)

        roles = {s["role"] for s in result["sections"]}
        assert roles == {
            ROLE_STATUS_BAR,
            ROLE_SYSTEM_NAV,
            ROLE_HEADER,
            ROLE_TAB_BAR,
            ROLE_CONTENT,
            ROLE_BOTTOM_NAV,
        }
        assert result["is_webview"] is False

        by_rid = {e["resource_id"]: e for e in result["elements"]}
        assert by_rid["com.govee.home:id/ivTabDevice"]["role"] == ROLE_BOTTOM_NAV
        assert by_rid["com.govee.home:id/ivSwitch"]["role"] == ROLE_CONTENT
        assert by_rid["com.govee.home:id/ivSwitch"]["metrics"] == ["可点击"]
        assert by_rid["com.govee.home:id/rvRoom"]["role"] == ROLE_TAB_BAR
        assert by_rid["com.govee.home:id/rvRoom"]["metrics"] == ["可滚动"]

    def _min_y(self, bounds):
        # "[min_x,min_y][max_x,max_y]" → min_y
        return int(bounds.split("][")[0].lstrip("[").split(",")[1])

    def test_sections_sorted_top_down(self):
        els = [
            el(package="com.android.systemui", class_name="android.widget.TextView", y=33),
            el(class_name="android.widget.TextView", text="设备", y=110),
            el(
                class_name="android.widget.ImageView",
                resource_id="x:id/switch",
                y=900,
                clickable=True,
            ),
            el(package="com.android.systemui", class_name="android.widget.ImageView", y=2872),
        ]
        result = classify_structure(els, SCREEN_H)
        ys = [self._min_y(s["bounds"]) for s in result["sections"]]
        assert ys == sorted(ys)

    def test_screen_h_fallback(self):
        # 不传 screen_h：用元素最大底部坐标兜底（需覆盖整屏的 fixture 才有意义）
        els = [
            el(
                package="com.android.systemui",
                class_name="android.widget.TextView",
                y=33,
                height=117,
            ),
            el(class_name="android.widget.TextView", text="设备", y=110, height=211),
            el(
                class_name="android.widget.ImageView",
                resource_id="x:id/tab",
                y=2657,
                height=154,
                clickable=True,
            ),
        ]
        result = classify_structure(els)
        assert result["sections"]  # 有分区产出即兜底可用
        by_text = {e["text"]: e for e in result["elements"]}
        by_rid = {e["resource_id"]: e for e in result["elements"]}
        assert by_text["设备"]["role"] == ROLE_HEADER
        assert by_rid["x:id/tab"]["role"] == ROLE_BOTTOM_NAV

    def test_original_fields_preserved(self):
        e = el(class_name="android.widget.TextView", text="设备", y=110, height=211)
        result = classify_structure([e], SCREEN_H)
        out = result["elements"][0]
        assert out["text"] == "设备"
        assert out["class_name"] == "android.widget.TextView"
        assert out["role"] == ROLE_HEADER
