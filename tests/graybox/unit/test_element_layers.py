"""灰盒·单元测试 — 元素两级分层与主定位规则（element-layering）。

覆盖 openspec/changes/add-element-layering-core 的 spec 场景：一级分组按类名、
二级与七细类、主定位的唯一性与类型质量、位置型候选不得冒充唯一、坐标顺序与保留标记。
零 I/O、零 DB、不连设备。
"""

import pytest

from algorithms.element_layers import (
    KIND_HOTZONE,
    KIND_ICON_BARE,
    KIND_ICON_FONT,
    KIND_ICON_SEMANTIC,
    KIND_SHAPE,
    KIND_TEXT,
    KIND_TEXT_EMPTY,
    LEVEL2_ICON,
    LEVEL2_OTHER,
    LEVEL2_TEXT,
    ROLE_CONTENT,
    ROLE_LAYOUT,
    ROLE_OTHER,
    ROLE_SCROLL,
    build_layers,
    classify_node,
    pick_primary,
)


def make_node(class_name="android.widget.TextView", **overrides):
    """构造一个字段齐全的节点（形态与 algorithms/hierarchy.parse_hierarchy_xml 输出一致）。"""
    node = {
        "depth": 1,
        "class_name": class_name,
        "text": "",
        "content_desc": "",
        "resource_id": "",
        "package": "com.demo",
        "index": "0",
        "bounds": "[0,0][10,10]",
        "x": 0,
        "y": 0,
        "width": 10,
        "height": 10,
        "clickable": False,
        "enabled": True,
        "scrollable": False,
        "checkable": False,
        "checked": False,
        "focusable": False,
        "long_clickable": False,
    }
    node.update(overrides)
    return node


# ══════════════ 一级分组 ══════════════


@pytest.mark.unit
@pytest.mark.device_pool
def test_level1_groups_by_class_name_only():
    """一级分组只看类名：布局容器 / 滚动·集合容器 / 内容控件 / 其它。"""
    assert classify_node(make_node("android.widget.FrameLayout"))[0] == ROLE_LAYOUT
    assert classify_node(make_node("androidx.recyclerview.widget.RecyclerView"))[0] == ROLE_SCROLL
    assert classify_node(make_node("android.widget.TextView"))[0] == ROLE_CONTENT


@pytest.mark.unit
@pytest.mark.device_pool
def test_unknown_class_falls_into_other_without_guessing():
    """不在任何集合内的类名归「其它」，不猜测归入前三个分组。"""
    level1, level2, kind = classify_node(
        make_node("com.vendor.CustomWidget", text="x", clickable=True)
    )
    assert level1 == ROLE_OTHER
    assert level2 is None
    assert kind == "unclassified"


@pytest.mark.unit
@pytest.mark.device_pool
def test_level1_does_not_use_position_or_flags():
    """归组不受位置与交互标志影响：可点击的纯容器仍是布局容器。"""
    node = make_node("android.widget.FrameLayout", clickable=True, y=9999, text="点击我")
    assert classify_node(node)[0] == ROLE_LAYOUT


# ══════════════ 二级分组与七细类 ══════════════


@pytest.mark.unit
@pytest.mark.device_pool
def test_text_kinds():
    """文本非空 → text；空文本仍归文本组（占位件不冒充图标）。"""
    assert classify_node(make_node("android.widget.TextView", text="设备")) == (
        ROLE_CONTENT,
        LEVEL2_TEXT,
        KIND_TEXT,
    )
    assert classify_node(make_node("android.widget.TextView", text="  ")) == (
        ROLE_CONTENT,
        LEVEL2_TEXT,
        KIND_TEXT_EMPTY,
    )


@pytest.mark.unit
@pytest.mark.device_pool
def test_icon_font_goes_to_icon_group():
    """文本类控件的文本由私用区码点组成 → 图标（图标字体伪装）。"""
    node = make_node("android.widget.TextView", text="\ue600")
    assert classify_node(node) == (ROLE_CONTENT, LEVEL2_ICON, KIND_ICON_FONT)


@pytest.mark.unit
@pytest.mark.device_pool
def test_icon_kinds_by_content_desc():
    """图形类按内容描述区分有语义 / 无语义。"""
    assert classify_node(make_node("android.widget.ImageView", content_desc="返回")) == (
        ROLE_CONTENT,
        LEVEL2_ICON,
        KIND_ICON_SEMANTIC,
    )
    assert classify_node(make_node("android.widget.ImageView")) == (
        ROLE_CONTENT,
        LEVEL2_ICON,
        KIND_ICON_BARE,
    )


@pytest.mark.unit
@pytest.mark.device_pool
def test_bare_view_kinds():
    """裸 View：可点击 → 热区；不可点击 → 形状。"""
    assert classify_node(make_node("android.view.View", clickable=True)) == (
        ROLE_CONTENT,
        LEVEL2_OTHER,
        KIND_HOTZONE,
    )
    assert classify_node(make_node("android.view.View")) == (ROLE_CONTENT, LEVEL2_OTHER, KIND_SHAPE)


# ══════════════ 主定位 ══════════════


@pytest.mark.unit
@pytest.mark.device_pool
def test_primary_picks_unique_resource_id():
    """存在唯一资源标识候选时选它并标记稳定。"""
    primary = pick_primary(
        [
            {"type": "resource-id", "xpath": "//A[@resource-id='x']", "count": 1},
            {"type": "class", "xpath": "//A", "count": 3},
        ]
    )
    assert primary["stable"] is True
    assert primary["type"] == "resource-id"
    assert primary["count"] == 1


@pytest.mark.unit
@pytest.mark.device_pool
def test_positional_candidate_never_becomes_primary():
    """位置型候选匹配数恒为 1，但 MUST NOT 被当作主定位（不得冒充唯一）。"""
    primary = pick_primary(
        [
            {"type": "resource-id", "xpath": "//A[@resource-id='x']", "count": 2},
            {"type": "index", "xpath": "(//A)[3]", "count": 1, "note": "fragile"},
        ]
    )
    assert primary["stable"] is False
    assert primary["type"] != "index"
    assert primary["type"] == "resource-id"


@pytest.mark.unit
@pytest.mark.device_pool
def test_positional_only_yields_no_primary():
    """只有位置型候选时不给出主定位，如实标记不稳定。"""
    primary = pick_primary([{"type": "index", "xpath": "(//A)[3]", "count": 1, "note": "fragile"}])
    assert primary == {"xpath": "", "type": "", "count": 0, "stable": False}


@pytest.mark.unit
@pytest.mark.device_pool
def test_unique_beats_type_quality():
    """唯一性优先于类型质量：匹配数为 1 的内容描述胜过匹配数为 3 的资源标识。"""
    primary = pick_primary(
        [
            {"type": "resource-id", "xpath": "//A[@resource-id='x']", "count": 3},
            {"type": "content-desc", "xpath": "//A[@content-desc='返回']", "count": 1},
        ]
    )
    assert primary["stable"] is True
    assert primary["type"] == "content-desc"


@pytest.mark.unit
@pytest.mark.device_pool
def test_no_candidate_yields_empty_primary():
    """无可定位身份时主定位为空且不稳定。"""
    assert pick_primary([]) == {"xpath": "", "type": "", "count": 0, "stable": False}


# ══════════════ 条目、排序与保留标记 ══════════════


@pytest.mark.unit
@pytest.mark.device_pool
def test_elements_are_ordered_by_coordinates():
    """元素按 (顶边 y, 左边 x, 层级深度) 升序。"""
    nodes = [
        make_node("android.widget.TextView", text="下", y=100, x=0, bounds="[0,100][10,110]"),
        make_node("android.widget.TextView", text="右上", y=10, x=50, bounds="[50,10][60,20]"),
        make_node("android.widget.TextView", text="左上", y=10, x=5, bounds="[5,10][15,20]"),
    ]
    layers = build_layers(nodes)
    assert [e["text"] for e in layers["elements"]] == ["左上", "右上", "下"]
    assert [e["seq"] for e in layers["elements"]] == [1, 2, 3]


@pytest.mark.unit
@pytest.mark.device_pool
def test_center_point_is_derived_from_bounds():
    """中心点由左上角与宽高派生（整数截断）。"""
    node = make_node("android.widget.TextView", text="x", x=58, y=59, width=98, height=158)
    entry = build_layers([node])["elements"][0]
    assert entry["coords"] == {
        "x": 58,
        "y": 59,
        "w": 98,
        "h": 158,
        "cx": 107,
        "cy": 138,
        "bounds": "[0,0][10,10]",
    }


@pytest.mark.unit
@pytest.mark.device_pool
def test_dropped_elements_stay_in_groups_with_flag():
    """被展示裁剪丢弃的元素仍入组，只是保留标记为假。"""
    container = make_node("android.widget.FrameLayout", bounds="[0,0][10,10]")
    text = make_node("android.widget.TextView", text="标题", bounds="[0,20][10,30]", y=20)
    layers = build_layers([container, text])
    by_class = {e["class_simple"]: e for e in layers["elements"]}
    assert by_class["FrameLayout"]["kept_in_snapshot"] is False  # 纯布局容器被裁
    assert by_class["TextView"]["kept_in_snapshot"] is True
    assert by_class["FrameLayout"]["level1"] == ROLE_LAYOUT


@pytest.mark.unit
@pytest.mark.device_pool
def test_summary_has_four_level1_and_three_level2_groups_even_when_empty():
    """摘要含一级四组与内容控件下的二级三组；「其它」计数为 0 也如实出现。"""
    layers = build_layers([make_node("android.widget.TextView", text="设备")])
    summary = layers["summary"]
    assert [g["key"] for g in summary["groups"]] == [
        ROLE_LAYOUT,
        ROLE_SCROLL,
        ROLE_CONTENT,
        ROLE_OTHER,
    ]
    assert summary["groups"][3]["count"] == 0
    content = summary["groups"][2]
    assert [c["key"] for c in content["children"]] == [LEVEL2_TEXT, LEVEL2_ICON, LEVEL2_OTHER]
    assert content["children"][0]["count"] == 1


@pytest.mark.unit
@pytest.mark.device_pool
def test_synthetic_root_is_not_an_element():
    """合成根节点（class 为空）不计入任何分组。"""
    root = make_node("", bounds="[0,0][0,0]", x=0, y=0, width=0, height=0)
    layers = build_layers([root, make_node("android.widget.TextView", text="设备")])
    assert layers["summary"]["total"] == 1


@pytest.mark.unit
@pytest.mark.device_pool
def test_candidates_are_generated_on_demand_but_not_part_of_the_entry():
    """候选按需生成（节点缺 xpaths 时即时算），但不作为条目字段返回。"""
    node = make_node("android.widget.TextView", text="设备", resource_id="com.demo:id/tv")
    entry = build_layers([node])["elements"][0]
    assert "xpath_candidates" not in entry
    assert entry["primary"]["type"] == "resource-id"


@pytest.mark.unit
@pytest.mark.device_pool
def test_stored_keep_flag_wins_over_recomputed_trim():
    """节点自带 kept_in_snapshot 时以它为准（索引落库记录的是采集时的真实结果）。"""
    kept = make_node("android.widget.TextView", text="已保留", kept_in_snapshot=True)
    dropped = make_node(
        "android.widget.TextView", text="被裁", y=50, bounds="[0,50][10,60]", kept_in_snapshot=False
    )
    layers = build_layers([kept, dropped])
    flags = {e["text"]: e["kept_in_snapshot"] for e in layers["elements"]}
    assert flags == {"已保留": True, "被裁": False}


@pytest.mark.unit
@pytest.mark.device_pool
def test_keep_flag_recomputed_when_absent():
    """没有 kept_in_snapshot 字段时按展示裁剪规则现算（纯布局容器被裁）。"""
    layers = build_layers([make_node("android.widget.FrameLayout", bounds="[0,0][10,10]")])
    assert layers["elements"][0]["kept_in_snapshot"] is False
