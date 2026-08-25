"""UI 层级结构分区 — L1a 纯函数（零 apps/django 依赖）。

只依据「位置 / class / package / 交互标志」识别结构事实，不依赖任何
App 特化的 resource-id 命名（保证跨 App/页面泛化）。

输入元素字段约定（与 `algorithms/hierarchy.py` 的 parse 输出一致）：
    class_name / resource_id / text / content_desc / package / index /
    bounds / x / y / width / height / depth /
    clickable / enabled / scrollable / checkable / checked / focusable / long_clickable
"""

# 系统层判定：package 含 systemui
_SYSTEM_PKG = "systemui"

# 分区角色
ROLE_STATUS_BAR = "status_bar"
ROLE_SYSTEM_NAV = "system_nav"
ROLE_HEADER = "header"
ROLE_TAB_BAR = "tab_bar"
ROLE_CONTENT = "content"
ROLE_BOTTOM_NAV = "bottom_nav"
ROLE_OTHER = "other"

# 角色 → 显示名
SECTION_NAMES = {
    ROLE_STATUS_BAR: "系统状态栏",
    ROLE_SYSTEM_NAV: "系统导航栏",
    ROLE_HEADER: "App头部",
    ROLE_TAB_BAR: "标签栏",
    ROLE_CONTENT: "内容区",
    ROLE_BOTTOM_NAV: "底部导航",
    ROLE_OTHER: "其他",
}

# 相对阈值（相对 screen_h 的比例，横屏/不同分辨率自适应）
_TOP_BAND = 0.06  # 状态栏带（systemui 顶部）
_HEADER_BAND = 0.12  # 头部/标签带（App 顶部）
_BOTTOM_BAND = 0.85  # 底部导航带（App 底部）
_SYSNAV_BAND = 0.92  # 系统导航带（systemui 底部）


def metrics(el: dict) -> list:
    """可点击/可滚动/可勾选 → 指标标签列表（都无则空列表）。"""
    tags = []
    if el.get("clickable"):
        tags.append("可点击")
    if el.get("scrollable"):
        tags.append("可滚动")
    if el.get("checkable"):
        tags.append("可勾选")
    return tags


def _is_system(el: dict) -> bool:
    return _SYSTEM_PKG in (el.get("package") or "").lower()


def _is_webview(el: dict) -> bool:
    return "webview" in (el.get("class_name") or "").lower()


def _guess_screen_h(elements: list) -> int:
    """screen_h 缺失时用元素最大底部坐标兜底。"""
    bottom = 0
    for el in elements:
        bottom = max(bottom, (el.get("y") or 0) + (el.get("height") or 0))
    return bottom


def detect_webview(elements: list) -> bool:
    """内容区是否含 WebView（原生层含 WebView 类节点）。

    WebView 类节点（class 含 `webview`）是网页容器的唯一明确信号；
    命中即视为网页承载页，供前端提示"切 Web context"。
    """
    return any(_is_webview(e) for e in elements if not _is_system(e))


def _classify_element(el: dict, screen_h: float) -> str:
    """单元素 → 分区角色（纯信号：package / class / y 坐标）。"""
    if _is_system(el):
        y = el.get("y") or 0
        if y < screen_h * _TOP_BAND:
            return ROLE_STATUS_BAR
        if y > screen_h * _SYSNAV_BAND:
            return ROLE_SYSTEM_NAV
        return ROLE_OTHER  # 中间的系统浮层（如 heads-up 通知）

    y = el.get("y") or 0
    cls = (el.get("class_name") or "").lower()

    if _is_webview(el):
        return ROLE_CONTENT

    if y > screen_h * _BOTTOM_BAND:
        return ROLE_BOTTOM_NAV

    if y < screen_h * _HEADER_BAND:
        # 顶部带内：横向滚动/顶部 RecyclerView → 标签栏，否则头部
        if "horizontalscrollview" in cls or "recyclerview" in cls:
            return ROLE_TAB_BAR
        return ROLE_HEADER

    return ROLE_CONTENT


def classify_structure(elements: list, screen_h: int = 0) -> dict:
    """平铺元素 → 分区结构（6 层分区 + 每元素 role/metrics）。

    Args:
        elements: 裁剪后的元素列表（`algorithms/xpath.trim_hierarchy` 输出）。
        screen_h: 屏幕高度（px）；<=0 时用元素最大底部坐标兜底。

    Returns:
        {
            "is_webview": bool,
            "sections": [{"name","role","bounds","element_count"}, ...],  # 自上而下排序
            "elements": [ {原始字段 + "role" + "metrics"}, ... ],
        }
    """
    if not elements:
        return {"is_webview": False, "sections": [], "elements": []}

    if screen_h <= 0:
        screen_h = _guess_screen_h(elements) or 1

    result_elements = []
    # role -> 聚合 bounds 与计数
    agg: dict[str, dict] = {}

    for el in elements:
        role = _classify_element(el, screen_h)
        out = dict(el)
        out["role"] = role
        out["metrics"] = metrics(el)
        result_elements.append(out)

        x, y = el.get("x") or 0, el.get("y") or 0
        w, h = el.get("width") or 0, el.get("height") or 0
        s = agg.setdefault(
            role,
            {"min_x": x, "min_y": y, "max_x": x + w, "max_y": y + h, "count": 0},
        )
        s["min_x"] = min(s["min_x"], x)
        s["min_y"] = min(s["min_y"], y)
        s["max_x"] = max(s["max_x"], x + w)
        s["max_y"] = max(s["max_y"], y + h)
        s["count"] += 1

    sections = []
    for role, s in agg.items():
        sections.append(
            {
                "name": SECTION_NAMES.get(role, role),
                "role": role,
                "bounds": f"[{s['min_x']},{s['min_y']}][{s['max_x']},{s['max_y']}]",
                "element_count": s["count"],
                "_min_y": s["min_y"],
            }
        )
    # 自上而下排序
    sections.sort(key=lambda s: s["_min_y"])
    for s in sections:
        s.pop("_min_y", None)

    return {
        "is_webview": detect_webview(elements),
        "sections": sections,
        "elements": result_elements,
    }
