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
        verbose_name = '测试SOP上下文'
        verbose_name_plural = '测试SOP上下文'

    def __str__(self):
        return f"SOP {self.sop_id} phase={self.phase}"


class TestRunRecord(models.Model):
    """Test execution run → tr_test_runs.

    selected_cases stores case snapshots at execution time:
        [{"case_id": "TC-...", "title": "...", "steps_data": [...]}, ...]
    This ensures historical runs are auditable even if cases are later modified.
    """
    run_id = models.CharField(max_length=200, unique=True)
    client_task_id = models.CharField(max_length=50, default='', blank=True)
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
        verbose_name = '测试运行记录'
        verbose_name_plural = '测试运行记录'

    def __str__(self):
        return f"Run {self.run_id}: {self.status}"


class TestResult(models.Model):
    """Single iteration result → tr_test_results."""
    run = models.ForeignKey(
        TestRunRecord, on_delete=models.CASCADE, related_name='results',
        null=True, blank=True,
    )
    case = models.ForeignKey(
        'case_manager.TestDefinition',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='test_results',
        db_column='case_id',
        to_field='id',
    )
    iteration = models.IntegerField()
    result = models.CharField(max_length=50)
    duration_ms = models.FloatField(default=0.0)
    detail = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tr_test_results'
        verbose_name = '测试结果'
        verbose_name_plural = '测试结果'
        indexes = [
            models.Index(fields=['result']),
        ]

    def __str__(self):
        case_id = self.case_id  # FK stores raw id in case_id column
        return f"{case_id}#{self.iteration}: {self.result}"


class TaskCard(models.Model):
    """User-created test execution task card → tr_task_cards.

    Replaces frontend localStorage for cross-device task sync.
    """
    task_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=200, default='')
    creator = models.CharField(max_length=200, default='')
    mode = models.CharField(max_length=20, default='immediate')  # immediate | scheduled
    device_serial = models.CharField(max_length=200, default='')
    case_ids = models.JSONField(default=list)
    loop_count = models.IntegerField(default=1)
    interval_seconds = models.IntegerField(default=5)
    status = models.CharField(
        max_length=20,
        choices=[("idle", "未执行"), ("queued", "排队中"), ("running", "执行中"), ("done", "已完成")],
        default="idle",
    )
    running = models.BooleanField(default=False)
    run = models.ForeignKey(
        TestRunRecord, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='task_cards',
    )
    case_items = models.JSONField(default=list)
    step_states = models.JSONField(default=list)
    overall_pass = models.IntegerField(default=0)
    overall_fail = models.IntegerField(default=0)
    logs = models.JSONField(default=list)
    outcome = models.CharField(
        max_length=20, default='', blank=True,
        choices=[('completed', '已完成'), ('stopped', '已停止'),
                 ('interrupted', '运行中断'), ('error', '异常终止')],
    )
    round = models.IntegerField(default=0)
    conclusion = models.TextField(default='', blank=True)
    bug_ticket = models.TextField(default='', blank=True)
    failed_steps = models.JSONField(default=list)
    current_case_title = models.CharField(max_length=500, default='', blank=True)
    current_iteration = models.IntegerField(default=0)
    start_at = models.CharField(max_length=100, default='', blank=True)
    end_at = models.CharField(max_length=100, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tr_task_cards'
        verbose_name = '任务卡片'
        verbose_name_plural = '任务卡片'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['device_serial']),
            models.Index(fields=['status', 'device_serial']),
        ]

    def __str__(self):
        return f"{self.task_id}: {self.name}"
