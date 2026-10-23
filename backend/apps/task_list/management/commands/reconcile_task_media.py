"""对账任务截图文件与 task_media 行：清理孤儿文件、报告缺失文件。"""

from django.core.management.base import BaseCommand

from backend.apps.task_list import media_storage
from backend.apps.task_list.models import TaskMedia


class Command(BaseCommand):
    help = "Reconcile DATA_DIR/task_media with task_media rows (orphan files / missing files)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only list what would be removed or reported.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        storage = media_storage.get_media_storage()
        rows = TaskMedia.objects.exclude(storage_key="")
        known: dict[int, set[str]] = {}
        missing = []
        for media in rows.iterator():
            known.setdefault(media.task_id, set()).add(media.storage_key)
            if not storage.exists(media.storage_key):
                missing.append((media.task_id, media.id, media.storage_key))

        orphans = []
        root = storage.root
        if root.is_dir():
            for directory in root.iterdir():
                if not directory.is_dir() or not directory.name.isdigit():
                    continue
                task_id = int(directory.name)
                for entry in directory.iterdir():
                    if not entry.is_file() or entry.name.endswith(".tmp"):
                        continue
                    key = f"{directory.name}/{entry.name}"
                    if key not in known.get(task_id, set()):
                        orphans.append((key, entry))

        removed = 0
        for _key, path in orphans:
            if not dry_run:
                path.unlink(missing_ok=True)
            removed += 1

        prefix = "Would remove" if dry_run else "Removed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {removed} orphan file(s); {len(missing)} row(s) missing their file."
            )
        )
        for task_id, media_id, key in missing[:50]:
            self.stderr.write(
                self.style.WARNING(f"missing: task={task_id} media={media_id} key={key}")
            )
