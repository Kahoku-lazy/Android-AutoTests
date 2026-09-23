"""元素两级分层与主定位规则 — L1a 算法层（纯函数，零 apps/django/engines 依赖）。

口径真相源：openspec/specs/element-layering（变更 add-element-layering-core）。

- L1 四类：布局容器 / 滚动·集合容器 / 内容控件 / 其它（不属于以上三类的）
- L2 三类（仅作用于内容控件）：文本 / 图标 / 其它
- 七个细类：text / text_empty / icon_font / icon_semantic / icon_bare / hotzone / shape
- 主定位：先筛「匹配数为 1 且非位置型」的候选，再按类型质量取首条；
  无唯一候选时如实标记 stable=False，MUST NOT 用位置型候选冒充唯一。

设计要点：
- 归组只看控件类名，不看位置/文本/交互标志；类名不在任何集合内即归「其它」，不猜测。
- 位置型候选（同类第 n 个）保留在候选列表里作为回退，但永不作为主定位，且始终标注脆弱。
- 元素条目按坐标顺序（顶边 y → 左边 x → 层级深度）排列；被展示裁剪丢弃的元素同样入组，
  只以保留标记区分。
"""

from algorithms.xpath import gen_xpath_candidates, trim_hierarchy

__all__ = [
    "ICON_CLASSES",
    "KIND_HOTZONE",
    "KIND_ICON_BARE",
    "KIND_ICON_FONT",
    "KIND_ICON_SEMANTIC",
    "KIND_SHAPE",
    "KIND_TEXT",
    "KIND_TEXT_EMPTY",
    "LAYOUT_CLASSES",
    "LEVEL2_ICON",
    "LEVEL2_OTHER",
    "LEVEL2_TEXT",
    "ROLE_CONTENT",
    "ROLE_LAYOUT",
    "ROLE_OTHER",
    "ROLE_SCROLL",
    "SCROLL_CLASSES",
    "TEXT_CLASSES",
    "build_layers",
    "classify_node",
    "is_private_use",
    "pick_primary",
]

# ═══════════════════════════════════════════════
# 类名集合（取类名末段，与 Android 类名同形）
# ═══════════════════════════════════════════════

LAYOUT_CLASSES = frozenset(
    {
        "ViewGroup",
        "FrameLayout",
        "LinearLayout",
        "RelativeLayout",
        "ConstraintLayout",
        "CoordinatorLayout",
        "GridLayout",
        "TableLayout",
        "TableRow",
        "RadioGroup",
        "CardView",
        "AppBarLayout",
        "NavigationView",
        "DrawerLayout",
        "SwipeRefreshLayout",
        "Toolbar",
        "MotionLayout",
        "TabLayout",
        "ViewAnimator",
        "ViewSwitcher",
    }
)

SCROLL_CLASSES = frozenset(
    {
        "RecyclerView",
        "ListView",
        "GridView",
        "ScrollView",
        "HorizontalScrollView",
        "NestedScrollView",
        "ViewPager",
        "ViewPager2",
        "ExpandableListView",
        "AdapterView",
        "AbsListView",
        "AbsSpinner",
        "Spinner",
    }
)

TEXT_CLASSES = frozenset(
    {
        "TextView",
        "Button",
        "EditText",
        "AutoCompleteTextView",
        "CheckBox",
        "RadioButton",
        "Switch",
        "ToggleButton",
        "CheckedTextView",
        "Chip",
        "SearchView",
    }
)

ICON_CLASSES = frozenset({"ImageView", "ImageButton"})

# ═══════════════════════════════════════════════
# 分组与细类标识
# ═══════════════════════════════════════════════

ROLE_LAYOUT = "layout_container"
ROLE_SCROLL = "scroll_collection"
ROLE_CONTENT = "content_widget"
ROLE_OTHER = "unclassified"

ROLE_NAMES = {
    ROLE_LAYOUT: "布局容器",
    ROLE_SCROLL: "滚动·集合容器",
    ROLE_CONTENT: "内容控件",
    ROLE_OTHER: "其它（不属于以上三类的）",
}
ROLE_ORDER = (ROLE_LAYOUT, ROLE_SCROLL, ROLE_CONTENT, ROLE_OTHER)

LEVEL2_TEXT = "text"
LEVEL2_ICON = "icon"
LEVEL2_OTHER = "other"

LEVEL2_NAMES = {LEVEL2_TEXT: "文本", LEVEL2_ICON: "图标", LEVEL2_OTHER: "其它"}
LEVEL2_ORDER = (LEVEL2_TEXT, LEVEL2_ICON, LEVEL2_OTHER)

KIND_TEXT = "text"
KIND_TEXT_EMPTY = "text_empty"
KIND_ICON_FONT = "icon_font"
KIND_ICON_SEMANTIC = "icon_semantic"
KIND_ICON_BARE = "icon_bare"
KIND_HOTZONE = "hotzone"
KIND_SHAPE = "shape"

# 主定位候选的质量顺序：唯一性优先于类型质量（见 pick_primary）
PRIMARY_QUALITY = (
    "resource-id",
    "content-desc",
    "combined",
    "resource-id (any)",
    "text",
    "text (any)",
    "class",
    "index",
)
# 位置型候选：匹配数恒为 1，但页面多一个同类控件就会指错，故永不作为主定位
POSITIONAL_TYPES = frozenset({"index"})

# 私用区码点：图标字体把图标画在文本里（U+E000–F8FF / U+F0000–FFFFD）
_PUA_RANGES = ((0xE000, 0xF8FF), (0xF0000, 0xFFFFD))


def simple_class(class_name: str) -> str:
    """android.widget.TextView → TextView。"""
    return class_name.rsplit(".", 1)[-1] if class_name else ""


def is_private_use(text: str) -> bool:
    """文本是否含私用区码点（图标字体伪装成文本的判据）。"""
    return any(any(lo <= ord(ch) <= hi for lo, hi in _PUA_RANGES) for ch in text)


def classify_node(node: dict) -> tuple:
    """节点 → (一级分组, 二级分组或 None, 细类)。

    一级只看类名；二级与细类只看内容控件承载什么，不看位置。
    """
    cls = simple_class(node.get("class_name", ""))
    text = (node.get("text") or "").strip()
    desc = (node.get("content_desc") or "").strip()

    if cls in LAYOUT_CLASSES:
        return ROLE_LAYOUT, None, "layout"
    if cls in SCROLL_CLASSES:
        return ROLE_SCROLL, None, "scroll"
    if cls in TEXT_CLASSES:
        if not text:
            return ROLE_CONTENT, LEVEL2_TEXT, KIND_TEXT_EMPTY
        if is_private_use(text):
            return ROLE_CONTENT, LEVEL2_ICON, KIND_ICON_FONT
        return ROLE_CONTENT, LEVEL2_TEXT, KIND_TEXT
    if cls in ICON_CLASSES:
        return ROLE_CONTENT, LEVEL2_ICON, KIND_ICON_SEMANTIC if desc else KIND_ICON_BARE
    if cls == "View":
        return ROLE_CONTENT, LEVEL2_OTHER, KIND_HOTZONE if node.get("clickable") else KIND_SHAPE
    return ROLE_OTHER, None, "unclassified"


def pick_primary(candidates) -> dict:
    """候选列表 → 主定位。

    先筛「匹配数为 1 且非位置型」，再按 PRIMARY_QUALITY 取首条；没有这样的候选时
    标记 stable=False，并给出匹配数最小的一条作为最接近的定位（不冒充唯一）。
    """
    cands = [c for c in (candidates or []) if c.get("xpath")]
    # 位置型候选全程排除：它匹配数恒为 1，一旦参与排序就会把「同类第 n 个」当成唯一
    usable = [c for c in cands if c.get("type") not in POSITIONAL_TYPES]
    unique = [c for c in usable if int(c.get("count") or 0) == 1]
    if unique:
        best = min(
            unique,
            key=lambda c: (
                PRIMARY_QUALITY.index(c["type"]) if c["type"] in PRIMARY_QUALITY else 999,
                len(c["xpath"]),
            ),
        )
        return {"xpath": best["xpath"], "type": best["type"], "count": 1, "stable": True}
    if not usable:
        # 只有位置型候选（或无候选）：不给主定位，如实标记不稳定
        return {"xpath": "", "type": "", "count": 0, "stable": False}
    fallback = min(
        usable,
        key=lambda c: (
            int(c.get("count") or 0),
            PRIMARY_QUALITY.index(c["type"]) if c["type"] in PRIMARY_QUALITY else 999,
        ),
    )
    return {
        "xpath": fallback["xpath"],
        "type": fallback["type"],
        "count": int(fallback.get("count") or 0),
        "stable": False,
    }


def order_key(node: dict) -> tuple:
    """坐标顺序：顶边 y → 左边 x → 层级深度。"""
    return (node.get("y", 0), node.get("x", 0), node.get("depth", 0))


def _extra(node: dict) -> dict:
    """元素条目里与分组无关的附加字段：七项交互标志。"""
    return {
        "flags": {
            "clickable": bool(node.get("clickable")),
            "long_clickable": bool(node.get("long_clickable")),
            "scrollable": bool(node.get("scrollable")),
            "checkable": bool(node.get("checkable")),
            "checked": bool(node.get("checked")),
            "enabled": bool(node.get("enabled")),
            "focusable": bool(node.get("focusable")),
        }
    }


def element_entry(node: dict, seq: int, keep: bool) -> dict:
    """节点 → 对外元素条目（字段口径见 specs/element-layering）。"""
    x, y = node.get("x", 0), node.get("y", 0)
    w, h = node.get("width", 0), node.get("height", 0)
    level1, level2, kind = classify_node(node)
    entry = {
        "seq": seq,
        "level1": level1,
        "level2": level2,
        "content_kind": kind,
        "coords": {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "cx": x + w // 2,
            "cy": y + h // 2,
            "bounds": node.get("bounds", ""),
        },
        "class_name": node.get("class_name", ""),
        "class_simple": simple_class(node.get("class_name", "")),
        "resource_id": node.get("resource_id", ""),
        "text": node.get("text", ""),
        "content_desc": node.get("content_desc", ""),
        "index_attr": node.get("index", ""),
        "depth": node.get("depth", 0),
        "kept_in_snapshot": keep,
        "primary": pick_primary(node.get("xpaths")),
    }
    entry.update(_extra(node))
    return entry


def _bucket_stats(rows) -> dict:
    return {
        "count": len(rows),
        "kept": sum(1 for e in rows if e["kept_in_snapshot"]),
        "stable_primary": sum(1 for e in rows if e["primary"]["stable"]),
        "clickable": sum(1 for e in rows if e["flags"]["clickable"]),
        "scrollable": sum(1 for e in rows if e["flags"]["scrollable"]),
    }


def build_layers(nodes) -> dict:
    """节点集合 → 两级分组（摘要 + 坐标顺序的全量元素条目）。

    Args:
        nodes: 节点 dict 列表（algorithms.hierarchy.parse_hierarchy_xml 的输出形态）；
            缺 xpaths 时按需即时生成（候选是派生数据，不要求调用方预置）。

    Returns:
        {"summary": {"total", "groups": [...]}, "elements": [...]}
        groups 里「内容控件」带 children（文本/图标/其它），其余分组 children 为空数组。
    """
    # 合成根节点 hierarchy（class 为空）不是 UI 元素，不计入分组
    items = [n for n in nodes if n.get("class_name")]

    for node in items:
        if node.get("xpaths") is None:
            has_identity = bool(
                node.get("resource_id")
                or node.get("text")
                or node.get("content_desc")
                or node.get("clickable")
            )
            node["xpaths"] = gen_xpath_candidates(node, items) if has_identity else []

    # 保留标记优先取节点自带的记录（全量索引落库时已写入采集时的真实结果）；
    # 没有该字段的输入（例如内存里现算的节点）按展示裁剪规则现算。
    if items and all("kept_in_snapshot" in n for n in items):
        kept_ids = {id(n) for n in items if n["kept_in_snapshot"]}
    else:
        kept_ids = {id(n) for n in trim_hierarchy(items)}
    ordered = sorted(items, key=order_key)

    elements = []
    buckets = {key: [] for key in ROLE_ORDER}
    sub_buckets = {key: [] for key in LEVEL2_ORDER}
    for seq, node in enumerate(ordered, start=1):
        level1, level2, _kind = classify_node(node)
        entry = element_entry(node, seq, id(node) in kept_ids)
        elements.append(entry)
        buckets[level1].append(entry)
        if level1 == ROLE_CONTENT:
            sub_buckets[level2].append(entry)

    groups = []
    for key in ROLE_ORDER:
        group = {
            "key": key,
            "name": ROLE_NAMES[key],
            "level": 1,
            **_bucket_stats(buckets[key]),
            "children": [],
        }
        if key == ROLE_CONTENT:
            group["children"] = [
                {
                    "key": sub,
                    "name": LEVEL2_NAMES[sub],
                    "level": 2,
                    **_bucket_stats(sub_buckets[sub]),
                }
                for sub in LEVEL2_ORDER
            ]
        groups.append(group)

    return {"summary": {"total": len(elements), "groups": groups}, "elements": elements}
