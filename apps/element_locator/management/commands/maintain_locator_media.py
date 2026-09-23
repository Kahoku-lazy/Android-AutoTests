"""元素定位媒体维护命令 — 存量回填 + 孤儿副本回收。

默认只报告（dry-run），不写文件、不改 DB；落盘必须显式 --apply。

    python manage.py maintain_locator_media                    # 只报告
    python manage.py maintain_locator_media --apply            # 回填 + 回收
    python manage.py maintain_locator_media --apply --only backfill
    python manage.py maintain_locator_media --apply --only prune

背景：导入快照时会把检查器媒体复制到 `locator/pages/<page_id>/`（见 api_snapshot）。
本命令把该口径补到存量数据上，并回收不再被任何页面/元素引用的副本。
`inspector/**` 永不触碰——那是检查器快照的资产。
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.element_locator.api_snapshot import (
    _LOCATOR_MEDIA_DIR,
    _copy_into_locator,
    _media_filename,
)
from apps.element_locator.models import Element, Page


def _short(path: str, limit: int = 60) -> str:
    return path if len(path) <= limit else "…" + path[-limit:]


class Command(BaseCommand):
    help = "元素定位媒体维护：存量回填（复制到 locator/pages）+ 孤儿副本回收（默认 dry-run）"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="真正写盘（默认只报告）")
        parser.add_argument(
            "--only",
            choices=["backfill", "prune"],
            default=None,
            help="只跑其中一半（默认两件都跑）",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        only = options["only"]
        root = Path(settings.MEDIA_ROOT)
        self.stdout.write(f"MEDIA_ROOT={root} apply={apply} only={only or 'all'}")
        stats = {"scanned": 0, "copied": 0, "skipped_missing": 0, "orphans": 0, "bytes_freed": 0}

        if only in (None, "backfill"):
            self._backfill(root, apply, stats)
        if only in (None, "prune"):
            self._prune(root, apply, stats)

        self.stdout.write(
            self.style.SUCCESS(
                "扫描 {scanned} · 回填 {copied} · 源缺失跳过 {skipped_missing} · "
                "孤儿 {orphans}（{bytes_freed} 字节）{suffix}".format(
                    suffix="" if apply else "（dry-run，未写盘）", **stats
                )
            )
        )

    def _backfill(self, root: Path, apply: bool, stats: dict) -> None:
        """把仍指向检查器路径且源文件存在的记录改指元素定位自有副本（复制，不移动源）。"""
        prefix = _LOCATOR_MEDIA_DIR + "/"

        for page in Page.objects.exclude(screenshot_path="").iterator():
            if page.screenshot_path.startswith(prefix):
                continue
            stats["scanned"] += 1
            if not (root / page.screenshot_path).is_file():
                stats["skipped_missing"] += 1
                self.stdout.write(f"  跳过（源缺失）Page#{page.id} {_short(page.screenshot_path)}")
                continue
            dest = f"{_LOCATOR_MEDIA_DIR}/{page.id}/screen.png"
            if not apply:
                # dry-run 不落盘：只报告将要写入的路径
                stats["copied"] += 1
                self.stdout.write(f"  Page#{page.id} → {dest}")
                continue
            copied = _copy_into_locator(page.screenshot_path, dest)
            if copied == page.screenshot_path:
                continue  # 复制失败（IO）：保留原路径，不计入已回填
            stats["copied"] += 1
            page.screenshot_path = copied
            page.save(update_fields=["screenshot_path"])
            self.stdout.write(f"  Page#{page.id} → {copied}")

        for element in Element.objects.exclude(thumbnail_path="").select_related("page").iterator():
            if element.thumbnail_path.startswith(prefix):
                continue
            stats["scanned"] += 1
            if not (root / element.thumbnail_path).is_file():
                stats["skipped_missing"] += 1
                self.stdout.write(
                    f"  跳过（源缺失）Element#{element.id} {_short(element.thumbnail_path)}"
                )
                continue
            dest = (
                f"{_LOCATOR_MEDIA_DIR}/{element.page_id}/"
                f"{_media_filename(element.resource_id, element.bounds)}"
            )
            if not apply:
                stats["copied"] += 1
                continue
            copied = _copy_into_locator(element.thumbnail_path, dest)
            if copied == element.thumbnail_path:
                continue  # 复制失败（IO）：保留原路径，不计入已回填
            stats["copied"] += 1
            element.thumbnail_path = copied
            element.save(update_fields=["thumbnail_path"])

    def _prune(self, root: Path, apply: bool, stats: dict) -> None:
        """删除 locator/pages/** 下不再被任何页面/元素引用的文件（并清理空目录）。"""
        base = root / _LOCATOR_MEDIA_DIR
        if not base.is_dir():
            return

        referenced = set(
            Page.objects.exclude(screenshot_path="").values_list("screenshot_path", flat=True)
        )
        referenced.update(
            Element.objects.exclude(thumbnail_path="").values_list("thumbnail_path", flat=True)
        )

        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel in referenced:
                continue
            stats["orphans"] += 1
            stats["bytes_freed"] += path.stat().st_size
            self.stdout.write(f"  孤儿文件 {rel}")
            if apply:
                path.unlink()

        if not apply:
            return
        for path in sorted(base.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
