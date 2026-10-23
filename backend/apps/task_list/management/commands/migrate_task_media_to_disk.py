"""把 task_media.thumb_b64 存量迁到本地 WebP 文件。可重复执行。"""

import base64

from django.core.management.base import BaseCommand

from backend.apps.task_list import media_storage
from backend.apps.task_list.models import TaskMedia


class Command(BaseCommand):
    help = "Migrate task_media.thumb_b64 into DATA_DIR/task_media/<task_id>/<sha256>.webp."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only count rows that would be migrated.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        storage = media_storage.get_media_storage()
        rows = TaskMedia.objects.exclude(thumb_b64__isnull=True).exclude(thumb_b64="")
        migrated = 0
        failed = 0
        freed = 0
        for media in rows.iterator():
            try:
                raw = base64.b64decode(media.thumb_b64)
            except Exception:
                failed += 1
                continue
            packed = media_storage.reencode(raw)
            if packed is None:
                failed += 1
                continue
            data, width, height = packed
            freed += len(media.thumb_b64)
            if not dry_run:
                key = storage.save(media.task_id, media.sha256, data)
                media.storage_key = key
                media.media_type = media_storage.MEDIA_TYPE
                media.byte_size = len(data)
                media.width = width
                media.height = height
                media.thumb_b64 = ""
                media.save(
                    update_fields=[
                        "storage_key",
                        "media_type",
                        "byte_size",
                        "width",
                        "height",
                        "thumb_b64",
                    ]
                )
            migrated += 1

        prefix = "Would migrate" if dry_run else "Migrated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {migrated} image(s), freed ~{freed / (1024 * 1024):.2f} MB of DB text, "
                f"{failed} unreadable."
            )
        )
        if failed:
            self.stderr.write(
                self.style.WARNING(f"{failed} row(s) kept unchanged (bad base64/image).")
            )
