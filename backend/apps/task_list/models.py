from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=500)
    task_kind = models.CharField(max_length=32, default="device_control")
    workflow_id = models.PositiveIntegerField(null=True, blank=True)
    release_version = models.PositiveIntegerField(null=True, blank=True)
    orchestration = models.CharField(max_length=16, default="", blank=True)
    kind = models.CharField(max_length=32, default="", blank=True)
    created_by = models.CharField(max_length=64, default="", blank=True)
    goal = models.TextField(default="", blank=True)
    attachment = models.TextField(default="", blank=True)
    attachment_filename = models.CharField(max_length=255, default="", blank=True)
    device_serial = models.CharField(max_length=100, default="", blank=True)
    device_label = models.CharField(max_length=200, default="", blank=True)
    case_title = models.CharField(max_length=255, default="", blank=True)
    case_identity = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default="pending")
    result = models.TextField(default="", blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_input_tokens = models.IntegerField(default=0)
    model_usage = models.JSONField(default=dict, blank=True)
    by_role = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cost_input = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_cache = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_output = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_total = models.DecimalField(max_digits=14, decimal_places=8, default=0)

    class Meta:
        db_table = "task_tasks"
        verbose_name = "任务"
        verbose_name_plural = "任务"

    def __str__(self):
        return f"{self.title} [{self.status}]"


class TaskAttachment(models.Model):
    KIND_CONFIG = "config"
    KIND_DOCUMENT = "document"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="file_attachments")
    kind = models.CharField(max_length=16)
    filename = models.CharField(max_length=255, default="", blank=True)
    body = models.TextField(default="", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    stored_path = models.CharField(max_length=500, default="", blank=True)
    load_message = models.CharField(max_length=32, default="", blank=True)

    class Meta:
        db_table = "task_attachments"
        ordering = ["sort_order", "id"]
        verbose_name = "任务附件"
        verbose_name_plural = "任务附件"

    def __str__(self):
        return f"{self.kind}:{self.filename}"


class TaskEvent(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="events")
    case_title = models.CharField(max_length=255, default="", blank=True)
    step_seq = models.IntegerField(null=True, blank=True)
    attempt = models.IntegerField(null=True, blank=True)
    seq = models.IntegerField()
    event_type = models.CharField(max_length=48)
    phase = models.CharField(max_length=8)
    block_type = models.CharField(max_length=16)
    is_delta = models.BooleanField(default=False)
    delta_count = models.PositiveIntegerField(default=1)
    role_name = models.CharField(max_length=64, default="", blank=True)
    role_kind = models.CharField(max_length=16, default="", blank=True)
    model = models.CharField(max_length=64, default="", blank=True)
    status = models.CharField(max_length=16, default="", blank=True)
    payload = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(default=0)
    called_at = models.DateTimeField(null=True, blank=True)
    called_date = models.DateField(null=True, blank=True)
    called_hour = models.PositiveSmallIntegerField(null=True, blank=True)
    is_peak = models.BooleanField(null=True, blank=True)
    input_tokens = models.IntegerField(default=0)
    cache_input_tokens = models.IntegerField(default=0)
    cache_miss_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_creation_tokens = models.IntegerField(default=0)
    cost_input = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_cache = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_output = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_total = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    pricing_snapshot = models.JSONField(null=True, blank=True)
    media = models.ForeignKey(
        "TaskMedia",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_events"
        indexes = [
            models.Index(fields=["task", "seq"], name="idx_evt_task_seq"),
            models.Index(fields=["task", "event_type"], name="idx_evt_task_type"),
            models.Index(fields=["called_date", "called_hour"], name="idx_evt_usage"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["task", "seq"], name="uk_evt_task_seq"),
        ]

    def __str__(self):
        return f"{self.task_id}#{self.seq} {self.event_type}"


class TaskMedia(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="media")
    event_seq = models.IntegerField(null=True, blank=True)
    role_name = models.CharField(max_length=64, default="", blank=True)
    step_seq = models.IntegerField(null=True, blank=True)
    attempt = models.IntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64)
    media_type = models.CharField(max_length=32)
    byte_size = models.IntegerField(default=0)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    storage_key = models.CharField(max_length=300, default="", blank=True)
    thumb_b64 = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_media"
        constraints = [
            models.UniqueConstraint(fields=["task", "sha256"], name="uk_media_task_sha"),
        ]
        indexes = [
            models.Index(fields=["task", "step_seq"], name="idx_media_task_step"),
        ]

    def __str__(self):
        return f"{self.task_id}:{self.sha256[:8]}"


class TaskUsageHourly(models.Model):
    stat_date = models.DateField()
    stat_hour = models.PositiveSmallIntegerField()
    is_peak = models.BooleanField(default=False)
    agent_id = models.BigIntegerField(default=0)
    model = models.CharField(max_length=64)
    role_name = models.CharField(max_length=64)
    role_kind = models.CharField(max_length=16, default="", blank=True)
    calls = models.IntegerField(default=0)
    input_tokens = models.BigIntegerField(default=0)
    cache_input_tokens = models.BigIntegerField(default=0)
    cache_miss_tokens = models.BigIntegerField(default=0)
    output_tokens = models.BigIntegerField(default=0)
    cost_input = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_cache = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_output = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_total = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task_usage_hourly"
        constraints = [
            models.UniqueConstraint(
                fields=["stat_date", "stat_hour", "model", "role_name", "agent_id"],
                name="uk_usage_slot",
            ),
        ]
        indexes = [
            models.Index(fields=["agent_id", "stat_date"], name="idx_usage_agent"),
        ]

    def __str__(self):
        return f"{self.stat_date} {self.stat_hour} {self.model}"
