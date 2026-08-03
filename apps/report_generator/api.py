"""report-generator public API."""

from .models import Report, ReportTemplate
from .service import ReportGenerator

# ── Write helpers ──


def save_report(run_id, title, file_type, file_path):
    """Save a report record."""
    return Report.objects.create(
        run_id=run_id,
        title=title,
        file_type=file_type,
        file_path=file_path,
    )


__all__ = ["Report", "ReportTemplate", "ReportGenerator", "save_report"]
