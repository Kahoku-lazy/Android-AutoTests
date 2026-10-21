"""report-generator ORM models — rg_ prefix tables (v2+)."""

from django.db import models


class Report(models.Model):
    """Report record → rg_reports (v2)."""

    run_id = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=500, default="")
    file_type = models.CharField(max_length=20, default="csv")
    file_path = models.CharField(max_length=1000, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rg_reports"
        verbose_name = "报告"
        verbose_name_plural = "报告"

    def __str__(self):
        return f"Report {self.title} ({self.file_type})"


class ReportTemplate(models.Model):
    """Report template → rg_report_templates (v3)."""

    name = models.CharField(max_length=200)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rg_report_templates"
        verbose_name = "报告模板"
        verbose_name_plural = "报告模板"

    def __str__(self):
        return self.name
