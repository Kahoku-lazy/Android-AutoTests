"""设备检查器快照媒体的生命周期 — 集成测试。

两组契约：
  A) 删除快照时的媒体保全（fix-dangling-snapshot-media）：被元素定位引用的媒体保留；
  B) 导入时只复制元素缩略图（rework-save-to-elements）：页面不落截图，


跨 App 只读 element_locator 的 Model（apps/AGENTS.md §1.1 允许读）。
"""

import pytest

from django.test import override_settings

from apps.device_inspector import api as inspector_api
from apps.device_inspector.models import Snapshot
from apps.element_locator.api import import_snapshot_page
from apps.element_locator.models import Element, Page

pytestmark = [pytest.mark.integration, pytest.mark.device_inspector]

TS = "20260101_000000_000000"
SHOT = f"inspector/shots/capture_{TS}.png"
THUMB = f"inspector/thumbs/{TS}/el_0.png"
USER = "u1"


def _make_snapshot() -> Snapshot:
    return Snapshot.objects.create(
        serial="S1",
        method="dump",
        dump_json={
            "actionable": [{"thumbnail_path": THUMB}],
            "elements": [{"thumbnail_path": THUMB}],
        },
        screenshot_path=SHOT,
        created_by=USER,
    )


def _write_file(media_root, rel: str, payload: bytes):
    path = media_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _write_media(media_root):
    return _write_file(media_root, SHOT, b"png"), _write_file(media_root, THUMB, b"png")


# ── A) 删除快照时的媒体保全 ──


@pytest.mark.django_db
def test_delete_snapshot_keeps_media_referenced_by_locator(tmp_path):
    """被已保存页面/元素引用的截图与缩略图必须保留（否则页面回看会 404）。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot, thumb = _write_media(tmp_path)
        snapshot = _make_snapshot()
        page = Page.objects.create(is_folder=False, label="被引用页面", screenshot_path=SHOT)
        Element.objects.create(
            page=page,
            resource_id="com.demo:id/x",
            bounds="[0,0][10,10]",
            thumbnail_path=THUMB,
        )

        assert inspector_api.delete_snapshot(snapshot.id, USER) is True

        assert not Snapshot.objects.filter(id=snapshot.id).exists()
        assert shot.is_file(), "被引用的截图不得被删除"
        assert thumb.is_file(), "被引用的缩略图不得被删除"


@pytest.mark.django_db
def test_delete_snapshot_removes_unreferenced_media(tmp_path):
    """没有任何引用的快照，媒体照旧清理。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot, thumb = _write_media(tmp_path)
        snapshot = _make_snapshot()

        assert inspector_api.delete_snapshot(snapshot.id, USER) is True

        assert not Snapshot.objects.filter(id=snapshot.id).exists()
        assert not shot.is_file(), "未被引用的截图应被清理"
        assert not thumb.exists(), "未被引用的缩略图目录应被清理"


@pytest.mark.django_db
def test_reference_check_failure_keeps_everything(tmp_path, monkeypatch):
    """判定失败时不得删除任何文件，也不得删除快照记录。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot, thumb = _write_media(tmp_path)
        snapshot = _make_snapshot()

        def _boom(*_args, **_kwargs):
            raise RuntimeError("引用判定失败")

        monkeypatch.setattr(inspector_api, "_media_referenced", _boom)

        with pytest.raises(RuntimeError):
            inspector_api.delete_snapshot(snapshot.id, USER)

        assert Snapshot.objects.filter(id=snapshot.id).exists(), "判定失败时快照记录必须保留"
        assert shot.is_file(), "判定失败时截图必须保留"
        assert thumb.is_file(), "判定失败时缩略图必须保留"


# ── B) 导入时只复制元素缩略图，不保存也不关联截图 ──


@pytest.mark.django_db
def test_import_copies_thumbnail_into_locator_dir(tmp_path):
    """导入后元素缩略图指向元素定位自有目录，副本存在、源文件不变，页面不落截图。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot, thumb = _write_media(tmp_path)
        result = import_snapshot_page(
            page_label="导入页",
            package="com.demo",
            snapshot_id=1,
            elements=[
                {"resource_id": "id/a", "bounds": "[0,0][1,1]", "thumbnail_path": THUMB},
            ],
        )
        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert page.screenshot_path == "", "导入不保存也不关联整屏截图"
        assert element.thumbnail_path.startswith(f"locator/pages/{page.id}/el_")
        assert (tmp_path / element.thumbnail_path).read_bytes() == b"png"
        assert not (tmp_path / f"locator/pages/{page.id}/screen.png").exists()
        assert thumb.read_bytes() == b"png", "源缩略图不得被改动"
        assert shot.read_bytes() == b"png", "源截图不得被改动"


@pytest.mark.django_db
def test_delete_snapshot_after_import_keeps_locator_thumbnail_copy(tmp_path):
    """解耦证明：导入后再删源快照，检查器媒体被清理，而元素定位缩略图副本与记录仍在。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot, thumb = _write_media(tmp_path)
        snapshot = _make_snapshot()
        result = import_snapshot_page(
            page_label="解耦页",
            package="com.demo",
            snapshot_id=snapshot.id,
            elements=[
                {"resource_id": "id/a", "bounds": "[0,0][1,1]", "thumbnail_path": THUMB},
            ],
        )
        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert inspector_api.delete_snapshot(snapshot.id, USER) is True

        assert not thumb.exists(), "导入后记录不再引用源缩略图，删快照应照旧清理"
        assert not shot.exists(), "页面不引用截图，删快照应照旧清理"
        assert (tmp_path / element.thumbnail_path).is_file(), "元素定位缩略图副本必须保留"


@pytest.mark.django_db
def test_import_leaves_thumbnail_empty_when_source_missing(tmp_path):
    """源缩略图缺失时元素缩略图留空（不指向检查器媒体），导入仍然成功。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        result = import_snapshot_page(
            page_label="缺源页",
            elements=[
                {
                    "resource_id": "id/b",
                    "bounds": "[0,0][1,1]",
                    "thumbnail_path": "inspector/thumbs/gone/el_0.png",
                },
            ],
        )
        page = Page.objects.get(id=result["page_id"])
        element = Element.objects.get(page=page)

        assert element.thumbnail_path == ""
        assert result["saved"] == 1


@pytest.mark.django_db
def test_repeated_import_does_not_cross_link_thumbnails(tmp_path):
    """重复导入且元素集合变化时，老元素仍指向自己那份副本（不串图）。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        thumb_a = _write_file(tmp_path, f"inspector/thumbs/{TS}/el_a.png", b"AAA")
        thumb_b = _write_file(tmp_path, f"inspector/thumbs/{TS}/el_b.png", b"BBB")
        thumb_c = _write_file(tmp_path, f"inspector/thumbs/{TS}/el_c.png", b"CCC")

        first = import_snapshot_page(
            page_label="重复页",
            elements=[
                {
                    "resource_id": "id/a",
                    "bounds": "[0,0][1,1]",
                    "thumbnail_path": str(thumb_a.relative_to(tmp_path)).replace("\\", "/"),
                },
                {
                    "resource_id": "id/b",
                    "bounds": "[0,0][2,2]",
                    "thumbnail_path": str(thumb_b.relative_to(tmp_path)).replace("\\", "/"),
                },
            ],
        )
        page = Page.objects.get(id=first["page_id"])
        path_a = Element.objects.get(page=page, resource_id="id/a").thumbnail_path
        assert (tmp_path / path_a).read_bytes() == b"AAA"

        import_snapshot_page(
            page_id=page.id,
            elements=[
                {
                    "resource_id": "id/c",
                    "bounds": "[0,0][3,3]",
                    "thumbnail_path": str(thumb_c.relative_to(tmp_path)).replace("\\", "/"),
                },
            ],
        )

        assert Element.objects.get(page=page, resource_id="id/a").thumbnail_path == path_a
        assert (tmp_path / path_a).read_bytes() == b"AAA", "首轮元素的副本不得被第二轮覆盖"
