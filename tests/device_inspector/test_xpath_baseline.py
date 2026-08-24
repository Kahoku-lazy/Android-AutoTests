"""Step 0 基线 — XPath 候选生成与层级裁剪现状行为锚定（L1a 算法下沉前置）。"""

import pytest

from apps.device_inspector.service import gen_xpath_candidates, trim_hierarchy

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _node(
    class_name="android.widget.Button",
    text="",
    content_desc="",
    resource_id="",
    index="",
    clickable=False,
    depth=0,
    bounds="[0,0][10,10]",
):
    return {
        "class_name": class_name,
        "text": text,
        "content_desc": content_desc,
        "resource_id": resource_id,
        "index": index,
        "clickable": clickable,
        "depth": depth,
        "bounds": bounds,
    }


class TestGenXpathCandidates:
    def test_all_locator_types_produced_and_sorted(self):
        cls = "android.widget.Button"
        rid = "com.app:id/btn"
        txt = "确定"
        desc = "确认按钮"
        el = _node(cls, txt, desc, rid, index="2")
        others = [
            _node(cls, txt, "", rid),  # 同类同 rid 同 text → count 权重
            _node(cls, txt, "", rid),
            _node("android.widget.TextView", "其他", "", "com.app:id/other"),
        ]
        all_els = [el, *others]

        locators = gen_xpath_candidates(el, all_els)

        types = [l["type"] for l in locators]
        # 现状行为：按 count 升序稳定排序（同 count 保持生成顺序）
        assert types == [
            "content-desc",
            "index",
            "resource-id",
            "text",
            "class",
            "combined",
            "resource-id (any)",
            "text (any)",
        ]
        # xpath 字符串口径
        by_type = {l["type"]: l for l in locators}
        assert by_type["resource-id"]["xpath"] == f"//{cls}[@resource-id='{rid}']"
        assert by_type["resource-id"]["count"] == 3
        assert by_type["text"]["count"] == 3
        assert by_type["class"]["xpath"] == f"//{cls}"
        assert by_type["class"]["count"] == 3  # 3 个 Button
        assert by_type["index"]["xpath"] == f"(//{cls})[3]"  # int(idx)+1
        assert by_type["combined"]["xpath"] == (f"//{cls}[@resource-id='{rid}' and @text='{txt}']")

    def test_minimal_element_only_class(self):
        el = _node("android.widget.TextView")
        all_els = [el]

        locators = gen_xpath_candidates(el, all_els)

        assert [l["type"] for l in locators] == ["class"]
        assert locators[0]["count"] == 1

    def test_non_numeric_index_skipped(self):
        el = _node("android.widget.TextView", text="x", index="abc")
        locators = gen_xpath_candidates(el, [el])
        assert all(l["type"] != "index" for l in locators)

    def test_count_uses_full_list_not_just_identity(self):
        el = _node("android.widget.Button", "a", "", "com.app:id/btn")
        many = [_node("android.widget.Button", f"t{i}", "", "com.app:id/btn") for i in range(5)]
        locators = gen_xpath_candidates(el, [el, *many])
        rid_any = next(l for l in locators if l["type"] == "resource-id (any)")
        # rid 出现在 6 个元素上（不限 class）
        assert rid_any["count"] == 6


class TestTrimHierarchy:
    def test_plain_layout_container_removed(self):
        nodes = [
            _node("android.widget.LinearLayout", depth=2),
            _node("android.widget.TextView", text="可见", depth=3),
        ]
        result = trim_hierarchy(nodes)
        assert [e["text"] for e in result] == ["可见"]

    def test_layout_with_identity_kept(self):
        nodes = [
            _node("android.widget.LinearLayout", text="有文本的容器", depth=2),
        ]
        result = trim_hierarchy(nodes)
        assert len(result) == 1
        assert result[0]["text"] == "有文本的容器"

    def test_bounds_dedup_keeps_most_specific(self):
        plain = _node("android.widget.TextView", "", "desc-only", "", depth=3, bounds="[0,0][5,5]")
        specific = _node(
            "android.widget.TextView",
            text="具体",
            content_desc="具体desc",
            resource_id="com.app:id/x",
            clickable=True,
            depth=7,
            bounds="[0,0][5,5]",
        )
        result = trim_hierarchy([plain, specific])
        assert len(result) == 1
        # 现状行为：同 bounds 保留特异性最高（clickable+text+desc+rid）
        assert result[0]["text"] == "具体"
