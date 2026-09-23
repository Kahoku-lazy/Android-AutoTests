"""检查器「保存到元素定位」的保存契约 — 集成测试。

钉住四件事：勾选 = 坐标顺序序号（越界被拒）；只写入收敛后的六项 + 去重键；
缩略图在保存时从快照整屏截图按 bounds 裁剪；整屏截图不写入元素定位。
"""

import pytest

from django.test import override_settings
from PIL import Image

from apps.device_inspector.api import save_snapshot_to_elements
from apps.device_inspector.models import Snapshot
from apps.element_locator.models import Element, Page

pytestmark = [pytest.mark.integration, pytest.mark.device_inspector]

USER = "u1"
TS = "20260101_000000_000000"
SHOT = f"inspector/shots/capture_{TS}.png"
PAGE_LABEL = "保存契约页"


def _node(text: str, resource_id: str, y: int) -> dict:
    """全量节点索引条目：坐标顺序（y 升序）决定序号 1..N。"""
    return {
        "depth": 5,
        "class_name": "android.widget.TextView",
        "text": text,
        "content_desc": "",
        "resource_id": resource_id,
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


NODES = [
    _node("第一行", "com.demo:id/a", 0),
    _node("第二行", "com.demo:id/b", 20),
    _node("第三行", "com.demo:id/c", 40),
]


def _make_snapshot() -> Snapshot:
    return Snapshot.objects.create(
        serial="S1",
        method="dump",
        package="com.demo",
        activity=".Main",
        dump_json={},
        nodes_json=NODES,
        screenshot_path=SHOT,
        created_by=USER,
    )


def _write_shot(media_root):
    path = media_root / SHOT
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (60, 60), (255, 0, 0)).save(path)
    return path


@pytest.mark.django_db
def test_save_keeps_only_selected_seqs(tmp_path):
    """勾选 = 坐标顺序序号集合，只有被勾中的元素落库。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write_shot(tmp_path)
        snapshot = _make_snapshot()

        result = save_snapshot_to_elements(
            snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=[1, 3]
        )

        page = Page.objects.get(id=result["page_id"])
        assert sorted(Element.objects.filter(page=page).values_list("seq", flat=True)) == [1, 3]
        assert (result["saved"], result["updated"]) == (2, 0)


@pytest.mark.django_db
def test_save_rejects_out_of_range_seq(tmp_path):
    """序号越界（含非整数）→ ValueError，不落库。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write_shot(tmp_path)
        snapshot = _make_snapshot()

        with pytest.raises(ValueError):
            save_snapshot_to_elements(
                snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=[99]
            )
        with pytest.raises(ValueError):
            save_snapshot_to_elements(
                snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=["s1"]
            )

        assert not Page.objects.filter(label=PAGE_LABEL).exists()


@pytest.mark.django_db
def test_save_writes_only_converged_fields_and_no_screenshot(tmp_path):
    """元素只带六项 + 去重键；类名/坐标分量/层级/父内序号/候选列表不写；页面不落截图。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write_shot(tmp_path)
        snapshot = _make_snapshot()

        result = save_snapshot_to_elements(
            snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=[1]
        )

        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert element.seq == 1
        assert element.alias == "第一行"
        assert element.text_val == "第一行"
        assert element.primary_xpath
        assert element.primary_stable is True
        assert element.clickable is True
        assert (element.resource_id, element.bounds) == ("com.demo:id/a", "[0,0][10,10]")

        assert element.class_name == ""
        assert element.content_desc == ""
        assert (element.x, element.y, element.width, element.height) == (0, 0, 0, 0)
        assert element.depth == 0
        assert element.index == ""
        assert element.xpath_candidates == "[]"

        assert page.screenshot_path == ""
        assert not (tmp_path / f"locator/pages/{page.id}/screen.png").exists()


@pytest.mark.django_db
def test_save_crops_thumbnail_from_snapshot_screenshot(tmp_path):
    """缩略图按元素 bounds 从快照截图裁剪，并复制到元素定位自有目录。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write_shot(tmp_path)
        snapshot = _make_snapshot()

        result = save_snapshot_to_elements(
            snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=[1]
        )

        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert element.thumbnail_path.startswith(f"locator/pages/{page.id}/el_")
        with Image.open(tmp_path / element.thumbnail_path) as thumb:
            assert thumb.size == (10, 10)


@pytest.mark.django_db
def test_save_keeps_thumbnail_empty_when_screenshot_missing(tmp_path):
    """快照截图缺失：元素照常写入，缩略图留空，不使保存失败。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        snapshot = _make_snapshot()

        result = save_snapshot_to_elements(
            snapshot.id, user_id=USER, page_label=PAGE_LABEL, element_ids=[1]
        )

        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert element.thumbnail_path == ""
        assert result["saved"] == 1
