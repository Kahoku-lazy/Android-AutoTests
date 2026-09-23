"""元素定位媒体维护命令 — 集成测试。

覆盖：存量回填（复制 + 改指 + 源保留）、源缺失跳过、孤儿回收只删未引用、dry-run 零副作用。
"""

from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command
from django.test import override_settings

from apps.element_locator.models import Element, Page

pytestmark = [pytest.mark.integration, pytest.mark.element_locator]

LEGACY_SHOT = "inspector/shots/legacy.png"
LEGACY_THUMB = "inspector/thumbs/legacy/el_0.png"


def _write(media_root: Path, rel: str, payload: bytes) -> Path:
    path = media_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _make_legacy_records() -> tuple[Page, Element]:
    page = Page.objects.create(is_folder=False, label="存量页", screenshot_path=LEGACY_SHOT)
    element = Element.objects.create(
        page=page,
        resource_id="com.demo:id/x",
        bounds="[0,0][10,10]",
        thumbnail_path=LEGACY_THUMB,
    )
    return page, element


def _run(*args: str) -> str:
    buf = StringIO()
    call_command("maintain_locator_media", *args, stdout=buf)
    return buf.getvalue()


@pytest.mark.django_db
def test_backfill_copies_and_repoints_but_keeps_source(tmp_path):
    """回填把记录改指 locator 副本，源文件保留（快照可能还在引用它）。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        legacy_shot = _write(tmp_path, LEGACY_SHOT, b"shot")
        legacy_thumb = _write(tmp_path, LEGACY_THUMB, b"thumb")
        page, element = _make_legacy_records()

        _run("--apply", "--only", "backfill")

        page.refresh_from_db()
        element.refresh_from_db()
        assert page.screenshot_path == f"locator/pages/{page.id}/screen.png"
        assert element.thumbnail_path.startswith(f"locator/pages/{page.id}/el_")
        assert (tmp_path / page.screenshot_path).read_bytes() == b"shot"
        assert (tmp_path / element.thumbnail_path).read_bytes() == b"thumb"
        assert legacy_shot.is_file(), "源截图必须保留"
        assert legacy_thumb.is_file(), "源缩略图必须保留"


@pytest.mark.django_db
def test_backfill_skips_missing_source(tmp_path):
    """源文件缺失时跳过并计数，不伪造路径。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        page, element = _make_legacy_records()  # 不落盘任何源文件

        output = _run("--apply", "--only", "backfill")

        page.refresh_from_db()
        element.refresh_from_db()
        assert page.screenshot_path == LEGACY_SHOT
        assert element.thumbnail_path == LEGACY_THUMB
        assert "源缺失跳过 2" in output


@pytest.mark.django_db
def test_prune_deletes_only_orphans(tmp_path):
    """只删 locator/pages/** 下未被引用的文件；被引用的与被复制出来的 inspector 资产都保留。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write(tmp_path, LEGACY_SHOT, b"shot")
        page, _element = _make_legacy_records()
        kept = _write(tmp_path, f"locator/pages/{page.id}/keep.png", b"kept")
        page.screenshot_path = f"locator/pages/{page.id}/keep.png"
        page.save(update_fields=["screenshot_path"])
        orphan = _write(tmp_path, "locator/pages/999/orphan.png", b"orphan")
        inspector_asset = _write(tmp_path, "inspector/shots/other.png", b"other")

        output = _run("--apply", "--only", "prune")

        assert kept.is_file(), "被引用的副本必须保留"
        assert not orphan.exists(), "孤儿副本应被删除"
        assert not (tmp_path / "locator/pages/999").exists(), "空目录应被清理"
        assert inspector_asset.is_file(), "inspector/** 永不触碰"
        assert "孤儿 1" in output


@pytest.mark.django_db
def test_dry_run_changes_nothing(tmp_path):
    """默认 dry-run：不复制、不改指、不删文件。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _write(tmp_path, LEGACY_SHOT, b"shot")
        page, element = _make_legacy_records()
        orphan = _write(tmp_path, "locator/pages/999/orphan.png", b"orphan")

        output = _run()

        page.refresh_from_db()
        element.refresh_from_db()
        assert page.screenshot_path == LEGACY_SHOT
        assert element.thumbnail_path == LEGACY_THUMB
        assert orphan.is_file(), "dry-run 不得删文件"
        assert not (tmp_path / f"locator/pages/{page.id}/screen.png").exists(), "dry-run 不得复制"
        assert "dry-run" in output
