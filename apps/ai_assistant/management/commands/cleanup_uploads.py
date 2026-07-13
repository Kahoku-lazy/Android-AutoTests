from django.core.management.base import BaseCommand

from apps.ai_assistant.upload_cleanup import cleanup_upload_dir


class Command(BaseCommand):
    help = "Delete stale chat upload files from data/uploads/ (default: older than 7 days)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-age-days",
            type=int,
            default=None,
            help="Remove files older than N days (default: UPLOAD_CLEANUP_MAX_AGE_DAYS or 7).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be deleted without removing files.",
        )

    def handle(self, *args, **options):
        max_age_seconds = None
        if options["max_age_days"] is not None:
            max_age_seconds = max(0, options["max_age_days"]) * 24 * 3600

        result = cleanup_upload_dir(max_age_seconds, dry_run=options["dry_run"])
        mb = result["bytes_freed"] / (1024 * 1024)
        prefix = "Would delete" if result["dry_run"] else "Deleted"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {result['deleted']} file(s), ~{mb:.2f} MB freed "
                f"(max age {result['max_age_seconds'] // 86400} days)."
            )
        )
        for err in result["errors"]:
            self.stderr.write(self.style.WARNING(err))
