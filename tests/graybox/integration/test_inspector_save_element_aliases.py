"""设备检查器「保存到元素定位」的逐元素名称回填 — 集成测试。

同名 resource_id 的多个元素必须各自保留自己的名称；只勾选子集时名称要按**坐标顺序序号**
（与元素表「序号」列同源）落地 —— 序号取自快照全量节点索引，不再用展示保留集的下标。

（dump_json 刻意留空：保存链路只认 nodes_json，旧下标口径不应再被使用。）
"""

import pytest

from apps.device_inspector.api import save_snapshot_to_elements
from apps.device_inspector.models import Snapshot
from apps.element_locator.models import Element, Page

pytestmark = [pytest.mark.integration, pytest.mark.device_inspector]

USER = "u1"
RID = "com.demo:id/row_title"


def _node(text: str, y: int) -> dict:
    """全量节点索引条目：坐标顺序（y 升序）决定序号 1..N。"""
    return {
        "depth": 5,
        "class_name": "android.widget.TextView",
        "text": text,
        "content_desc": "",
        "resource_id": RID,
        "index": "0",
        "bounds": f"[0,{y}][10,{y + 10}]",
        "x": 0,
        "y": y,
        "width": 10,
        "height": 10,
        "clickable": True,
        "enabled": True,
        "scrollable": False,
        "checkable": False,
        "checked": False,
        "focusable": True,
        "long_clickable": False,
        "kept_in_snapshot": True,
    }


# 两个元素共享同一 resource_id（列表项场景），y 不同 → 序号 1 / 2
NODES = [_node("A", 0), _node("B", 20)]


def _make_snapshot() -> Snapshot:
    return Snapshot.objects.create(
        serial="S1",
        method="dump",
        dump_json={},
        nodes_json=NODES,
        created_by=USER,
    )


@pytest.mark.django_db
def test_element_aliases_fill_per_seq_without_overwriting():
    """同名 rid 的两个元素分别命名，保存后各保留自己那一份。"""
    snapshot = _make_snapshot()

    result = save_snapshot_to_elements(
        snapshot.id,
        user_id=USER,
        page_label="同名页面",
        element_aliases=[
            {"index": 1, "name": "第一行"},
            {"index": 2, "name": "第二行"},
        ],
    )

    page = Page.objects.get(id=result["page_id"])
    aliases = {e.bounds: e.alias for e in Element.objects.filter(page=page)}
    assert aliases == {"[0,0][10,10]": "第一行", "[0,20][10,30]": "第二行"}


@pytest.mark.django_db
def test_element_aliases_follow_seq_when_subset_selected():
    """只勾选第二个元素时，名称必须按序号落到它身上（而不是筛减后的第 1 位）。"""
    snapshot = _make_snapshot()

    result = save_snapshot_to_elements(
        snapshot.id,
        user_id=USER,
        page_label="子集页面",
        element_ids=[2],
        element_aliases=[{"index": 2, "name": "只改第二行"}],
    )

    page = Page.objects.get(id=result["page_id"])
    elements = list(Element.objects.filter(page=page))
    assert len(elements) == 1
    assert elements[0].bounds == "[0,20][10,30]"
    assert elements[0].seq == 2
    assert elements[0].alias == "只改第二行"


@pytest.mark.django_db
def test_rid_aliases_still_work_for_ai_tool_path():
    """rid 口径的 aliases 通道保持可用（AI 工具调用方）。"""
    snapshot = _make_snapshot()

    result = save_snapshot_to_elements(
        snapshot.id,
        user_id=USER,
        page_label="rid口径页面",
        aliases={RID: "按rid命名"},
    )

    page = Page.objects.get(id=result["page_id"])
    assert {e.alias for e in Element.objects.filter(page=page)} == {"按rid命名"}


@pytest.mark.django_db
def test_out_of_range_seq_is_rejected():
    """序号越界（含非整数）→ ValueError，不静默丢弃后照常保存。"""
    snapshot = _make_snapshot()

    with pytest.raises(ValueError):
        save_snapshot_to_elements(snapshot.id, user_id=USER, page_label="越界页", element_ids=[99])
    with pytest.raises(ValueError):
        save_snapshot_to_elements(
            snapshot.id, user_id=USER, page_label="越界页", element_ids=["s1"]
        )
    assert not Page.objects.filter(label="越界页").exists()
