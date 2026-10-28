"""Backfill BUG tickets from historical task errors.

Usage:
    python manage.py sync_bug_tickets
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
        tasks = Task.objects.filter(
            status__in=("failed", "interrupted", "completed")
        ).select_related("agent")
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
