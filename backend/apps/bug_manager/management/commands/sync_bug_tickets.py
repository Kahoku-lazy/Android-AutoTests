"""
模块功能：➡️ Backfill BUG tickets from historical task errors. 🏁
Python 调试：➡️ python -m backend.apps.bug_manager.management.commands.sync_bug_tickets 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（管理命令，无自动化用例）
🏁
"""

from django.core.management.base import BaseCommand

from backend.apps.bug_manager.api import record_task_bugs
from backend.apps.task_list.models import Task


class Command(BaseCommand):
    """Scan failed/interrupted tasks and completed case tasks with import failures."""

    help = "Backfill BUG tickets from historical task errors (idempotent)."

    def handle(self, *args, **options):
        """Run the backfill and print counters."""
        result = {"scanned": 0, "created": 0, "updated": 0, "skipped": 0}
        tasks = Task.objects.filter(status__in=("failed", "interrupted", "completed"))
        for task in tasks:
            result["scanned"] += 1
            try:
                counts = record_task_bugs(task)
            except Exception as exc:  # noqa: BLE001 - keep the batch running
                result["skipped"] += 1
                self.stderr.write(f"task {task.id} skipped: {exc}")
                continue
            if counts["created"] == 0 and counts["updated"] == 0:
                result["skipped"] += 1
            result["created"] += counts["created"]
            result["updated"] += counts["updated"]
        self.stdout.write(
            "scanned={scanned} created={created} updated={updated} skipped={skipped}".format(
                **result
            )
        )
