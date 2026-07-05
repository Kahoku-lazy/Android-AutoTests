"""test-runner ORM models — tr_ prefix tables."""
from django.db import models


class TestSOP(models.Model):
    """AI Test SOP context — tracks the 4-phase workflow across a conversation."""

    sop_id = models.CharField(max_length=50, unique=True)
    conv_id = models.IntegerField(default=0)
    phase = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='active')

    requirement = models.TextField(default='', blank=True)
    case_design = models.JSONField(default=list)
    element_mapping = models.JSONField(default=list)
    element_gaps = models.JSONField(default=list)
    debug_notes = models.JSONField(default=list)
    case_ids = models.JSONField(default=list)

    run_id = models.CharField(max_length=200, default='', blank=True)
    run_results = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tr_test_sop'

    def __str__(self):
        return f"SOP {self.sop_id} phase={self.phase}"


class TestRunRecord(models.Model):
    """Test execution run → tr_test_runs."""
    run_id = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=50, default='PENDING')
    device_serial = models.CharField(max_length=200, default='')
    selected_cases = models.JSONField(default=list)
    loop_count = models.IntegerField(default=1)
    summary = models.JSONField(default=dict)
    started_at = models.CharField(max_length=100, default='')
    finished_at = models.CharField(max_length=100, default='')
    csv_path = models.CharField(max_length=1000, default='', blank=True)
    log_path = models.CharField(max_length=1000, default='', blank=True)

    class Meta:
        db_table = 'tr_test_runs'

    def __str__(self):
        return f"Run {self.run_id}: {self.status}"


class TestResult(models.Model):
    """Single iteration result → tr_test_results."""
    run = models.ForeignKey(
        TestRunRecord, on_delete=models.CASCADE, related_name='results',
        null=True, blank=True,
    )
    case_id = models.CharField(max_length=200)
    iteration = models.IntegerField()
    result = models.CharField(max_length=50)
    duration_ms = models.FloatField(default=0.0)
    detail = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tr_test_results'
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['result']),
        ]

    def __str__(self):
        return f"{self.case_id}#{self.iteration}: {self.result}"
