"""ai-assistant ORM models — ai_ prefix tables. AgentScope-powered agent management."""

from django.conf import settings
from django.db import models


class AIAgent(models.Model):
    """Agent configuration → ai_agents."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_agents",
    )
    name = models.CharField(max_length=200)
    avatar = models.TextField(default="", blank=True)
    tags = models.CharField(max_length=500, default="", blank=True)
    description = models.TextField(default="", blank=True)
    model_provider = models.CharField(max_length=50, default="dashscope")
    model_name = models.CharField(max_length=100, default="qwen-max")
    # 视觉模型名：意图路由为 phone_control/workflow 时使用；空则回退 model_name（纯文本）
    vision_model_name = models.CharField(max_length=100, default="", blank=True)
    # 强模型名：强模型开关开启时使用；空则回退 vision_model_name（多模态强模型）
    strong_model_name = models.CharField(max_length=100, default="", blank=True)
    # 强模型短路开关：开启时跳过意图 1/2 选择，直接下发强模型 Harness
    strong_enabled = models.BooleanField(default=False)
    # 设备控制线路模型配置：{"device_control": {"planner": {...}, "executor": {...}, "verifier": {...}}}
    # 每条线路的 api_key 经 Fernet 加密；读取时脱敏。
    route_configs = models.JSONField(default=dict, blank=True)
    # 工作流循环次数：executor ↔ verifier 内层循环的最大重试次数
    max_loops = models.IntegerField(default=3)
    api_key = models.CharField(max_length=500, default="", blank=True)
    base_url = models.CharField(max_length=500, default="", blank=True)
    status = models.CharField(max_length=20, default="active")
    # AgentScope agent_id returned by POST /agent/ — needed to reference in chat/session calls
    agent_scope_id = models.CharField(max_length=100, default="", blank=True)
    # Security: one-time API key reveal — set False on key change, True after first reveal
    key_revealed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_agents"
        verbose_name = "智能体"
        verbose_name_plural = "智能体"

    def __str__(self):
        return self.name


class AITask(models.Model):
    """Agent task → ai_tasks."""

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=500)
    # 任务发布字段
    goal = models.TextField(default="", blank=True)  # 任务目标（必填）
    attachment = models.TextField(default="", blank=True)  # 附件解析后的 Markdown（无附件为空）
    attachment_filename = models.CharField(
        max_length=255, default="", blank=True
    )  # 原始附件文件名（可选）
    device_serial = models.CharField(
        max_length=100, default="", blank=True
    )  # 指定设备 serial（提交时已固化）
    device_label = models.CharField(
        max_length=200, default="", blank=True
    )  # 卡片展示用设备名（型号优先，否则空）
    case_title = models.CharField(
        max_length=255, default="", blank=True
    )  # 指定用例标题；空串=执行 YAML 中的全部用例
    status = models.CharField(max_length=20, default="pending")
    result = models.TextField(default="", blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    # ── token 用量（任务完成时由工作流采集落库）──
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_input_tokens = models.IntegerField(default=0)
    # 按模型拆分：{model_name: {"input_tokens", "output_tokens", "cache_input_tokens"}}
    # DeepSeek 费用按模型单价计价，故需保留分模型用量。
    model_usage = models.JSONField(default=dict, blank=True)
    # 按角色拆分：{"planner"/"executor"/"verifier": {"input_tokens", "output_tokens", "cache_input_tokens"}}
    by_role = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cost_input = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_cache = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_output = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    cost_total = models.DecimalField(max_digits=14, decimal_places=8, default=0)

    class Meta:
        db_table = "ai_tasks"
        verbose_name = "任务"
        verbose_name_plural = "任务"

    def __str__(self):
        return f"{self.title} [{self.status}]"


class AITaskAttachment(models.Model):
    """任务附件正文与原件路径 → ai_task_attachments。"""

    KIND_CONFIG = "config"
    KIND_DOCUMENT = "document"

    task = models.ForeignKey(AITask, on_delete=models.CASCADE, related_name="file_attachments")
    kind = models.CharField(max_length=16)
    filename = models.CharField(max_length=255, default="", blank=True)
    body = models.TextField(default="", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    stored_path = models.CharField(max_length=500, default="", blank=True)
    load_message = models.CharField(max_length=32, default="", blank=True)

    class Meta:
        db_table = "ai_task_attachments"
        ordering = ["sort_order", "id"]
        verbose_name = "任务附件"
        verbose_name_plural = "任务附件"

    def __str__(self):
        return f"{self.kind}:{self.filename}"


class AITaskEvent(models.Model):
    """一条智能体运行事件 → ai_task_events。"""

    task = models.ForeignKey(AITask, on_delete=models.CASCADE, related_name="events")
    case_title = models.CharField(max_length=255, default="", blank=True)
    step_seq = models.IntegerField(null=True, blank=True)
    attempt = models.IntegerField(null=True, blank=True)
    seq = models.IntegerField()
    event_type = models.CharField(max_length=48)
    phase = models.CharField(max_length=8)
    block_type = models.CharField(max_length=16)
    is_delta = models.BooleanField(default=False)
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
        "AITaskMedia",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_task_events"
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


class AITaskMedia(models.Model):
    """任务图片缩略图 → ai_task_media。不存原图。"""

    task = models.ForeignKey(AITask, on_delete=models.CASCADE, related_name="media")
    event_seq = models.IntegerField(null=True, blank=True)
    role_name = models.CharField(max_length=64, default="", blank=True)
    step_seq = models.IntegerField(null=True, blank=True)
    attempt = models.IntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64)
    media_type = models.CharField(max_length=32)
    byte_size = models.IntegerField(default=0)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    thumb_b64 = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_task_media"
        constraints = [
            models.UniqueConstraint(fields=["task", "sha256"], name="uk_media_task_sha"),
        ]
        indexes = [
            models.Index(fields=["task", "step_seq"], name="idx_media_task_step"),
        ]

    def __str__(self):
        return f"{self.task_id}:{self.sha256[:8]}"


class AIUsageHourly(models.Model):
    """按小时累计的模型费用。agent_id 是裸数字，不设外键。"""

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
        db_table = "ai_usage_hourly"
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
