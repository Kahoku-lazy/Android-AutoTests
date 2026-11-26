from django.db import models


class AIModelConfig(models.Model):
    PROVIDER_CHOICES = [
        ("deepseek", "deepseek"),
        ("dashscope", "dashscope"),
        ("openai", "openai"),
    ]
    API_KEY_CHOICES = [
        ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
        ("DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
        ("OPENAI_API_KEY", "OPENAI_API_KEY"),
    ]

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
    api_key_env = models.CharField(max_length=64, choices=API_KEY_CHOICES)
    api_protocol = models.CharField(max_length=32, default="", blank=True)
    model_kind = models.CharField(max_length=32, default="chat", blank=True)
    voice = models.CharField(max_length=64, default="", blank=True)
    dimensions = models.PositiveIntegerField(null=True, blank=True)
    base_url = models.CharField(max_length=500, default="", blank=True)
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_model_configs"
        verbose_name = "模型配置"
        verbose_name_plural = "模型配置"
        constraints = [
            models.UniqueConstraint(
                fields=["api_key_env", "model_name"],
                name="uniq_ai_model_config_key_model",
            )
        ]

    def __str__(self):
        return f"{self.api_key_env} / {self.model_name}"


class AIRole(models.Model):
    role_id = models.CharField(max_length=11, unique=True)
    name = models.CharField(max_length=200, unique=True, db_collation="utf8mb4_bin")
    model_config = models.ForeignKey(
        AIModelConfig,
        on_delete=models.PROTECT,
        related_name="roles",
    )
    system_prompt = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_roles"
        verbose_name = "Agent配置"
        verbose_name_plural = "Agent配置"

    def __str__(self):
        return f"{self.role_id} {self.name}"


class AIRoleKind(models.Model):
    KIND_EXECUTOR = "executor"
    KIND_VERIFIER = "verifier"
    KIND_PLANNER = "planner"
    KIND_CHOICES = [
        (KIND_EXECUTOR, "执行者"),
        (KIND_VERIFIER, "验收者"),
        (KIND_PLANNER, "规划者"),
    ]

    role = models.ForeignKey(AIRole, on_delete=models.CASCADE, related_name="kinds")
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_role_kinds"
        verbose_name = "Agent配置类型"
        verbose_name_plural = "Agent配置类型"
        constraints = [
            models.UniqueConstraint(fields=["role"], name="uniq_ai_role_kind_role"),
            models.UniqueConstraint(fields=["role", "kind"], name="uniq_ai_role_kind_pair"),
        ]

    def __str__(self):
        return f"{self.role_id} {self.kind}"


class ModelUseGrant(models.Model):
    user_id = models.PositiveIntegerField()
    model_config = models.ForeignKey(
        AIModelConfig,
        on_delete=models.CASCADE,
        related_name="use_grants",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_model_use_grants"
        verbose_name = "模型使用名单"
        verbose_name_plural = "模型使用名单"
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "model_config"],
                name="uniq_ai_model_use_grant",
            )
        ]

    def __str__(self):
        return f"{self.user_id}:{self.model_config_id}"


class AssistantRelease(models.Model):
    KIND_ASSISTANT = "assistant"
    KIND_WORKFLOW = "workflow"

    target_kind = models.CharField(max_length=16)
    target_id = models.CharField(max_length=32)
    version = models.PositiveIntegerField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_releases"
        verbose_name = "助手发布版本"
        verbose_name_plural = "助手发布版本"
        constraints = [
            models.UniqueConstraint(
                fields=["target_kind", "target_id", "version"],
                name="uniq_ai_assistant_release",
            )
        ]

    def __str__(self):
        return f"{self.target_kind}:{self.target_id}@{self.version}"


class AssistantAuthorGrant(models.Model):
    user_id = models.PositiveIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_author_grants"
        verbose_name = "助手作者授权"
        verbose_name_plural = "助手作者授权"

    def __str__(self):
        return str(self.user_id)


class AIAssistant(models.Model):
    assistant_id = models.CharField(max_length=12, unique=True)
    display_name = models.CharField(max_length=200)
    avatar = models.TextField(default="", blank=True)
    marker = models.CharField(max_length=16)
    role_id = models.CharField(max_length=11)
    tools = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    release_state = models.CharField(max_length=16, default="draft")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "ai_assistants"
        verbose_name = "助手名片"
        verbose_name_plural = "助手名片"

    def __str__(self):
        return f"{self.assistant_id} {self.display_name}"


class AISopWorkflow(models.Model):
    name = models.CharField(max_length=200)
    orchestration = models.CharField(max_length=16, default="sop")
    kind = models.CharField(max_length=32, default="ui_automation")
    executor_assistant_id = models.CharField(max_length=12, default="", blank=True)
    verifier_assistant_id = models.CharField(max_length=12, default="", blank=True)
    leader_assistant_id = models.CharField(max_length=12, default="", blank=True)
    members = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    release_state = models.CharField(max_length=16, default="draft")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "ai_sop_workflows"
        verbose_name = "SOP 工作流"
        verbose_name_plural = "SOP 工作流"

    def __str__(self):
        return self.name


class AIAssistantThread(models.Model):
    STATUS_IDLE = "idle"
    STATUS_RUNNING = "running"
    STATUS_CANCELLED = "cancelled"
    STATUS_INTERRUPTED = "interrupted"
    STATUS_DONE = "done"

    thread_id = models.CharField(max_length=32, unique=True)
    assistant_id = models.CharField(max_length=12)
    title = models.CharField(max_length=80, default="", blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, default=STATUS_IDLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_assistant_threads"
        verbose_name = "助手对话栏"
        verbose_name_plural = "助手对话栏"

    def __str__(self):
        return self.thread_id


class AIAssistantMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    thread = models.ForeignKey(
        AIAssistantThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16)
    content = models.TextField()
    report_id = models.CharField(max_length=32, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_messages"
        ordering = ["id"]
        verbose_name = "助手对话消息"
        verbose_name_plural = "助手对话消息"

    def __str__(self):
        return f"{self.role}:{self.id}"


class AssistantEvalCase(models.Model):
    title = models.CharField(max_length=200)
    note = models.TextField(default="", blank=True)
    enabled = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=64, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_eval_cases"
        ordering = ["sort_order", "id"]
        verbose_name = "UI 执行评测题"
        verbose_name_plural = "UI 执行评测题"

    def __str__(self):
        return self.title


class AssistantEvalCaseStep(models.Model):
    case = models.ForeignKey(AssistantEvalCase, on_delete=models.CASCADE, related_name="steps")
    sort_order = models.PositiveIntegerField(default=1)
    action = models.TextField(default="", blank=True)
    assertion = models.TextField(default="", blank=True)
    anchor = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_eval_case_steps"
        ordering = ["sort_order", "id"]
        verbose_name = "评测题步骤"
        verbose_name_plural = "评测题步骤"

    def __str__(self):
        return f"{self.case_id}#{self.sort_order}"


class AssistantEvalScore(models.Model):
    target_kind = models.CharField(max_length=16)
    target_id = models.CharField(max_length=32)
    prompt_fingerprint = models.CharField(max_length=64, default="", blank=True)
    source_ref = models.CharField(max_length=200, default="", blank=True)
    judge_model = models.CharField(max_length=64, default="", blank=True)
    method_key = models.CharField(max_length=32, default="", blank=True)
    report_html = models.CharField(max_length=300, default="", blank=True)
    test_run_json = models.CharField(max_length=300, default="", blank=True)
    created_by = models.CharField(max_length=64, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_eval_scores"
        ordering = ["-id"]
        verbose_name = "助手评测评分"
        verbose_name_plural = "助手评测评分"

    def __str__(self):
        return f"{self.target_kind}:{self.target_id}@{self.id}"


class AssistantEvalScoreItem(models.Model):
    run = models.ForeignKey(AssistantEvalScore, on_delete=models.CASCADE, related_name="items")
    metric_key = models.CharField(max_length=32)
    score = models.DecimalField(max_digits=4, decimal_places=3)
    reason = models.TextField(default="", blank=True)
    threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_eval_score_items"
        ordering = ["id"]
        verbose_name = "助手评测评分项"
        verbose_name_plural = "助手评测评分项"

    def __str__(self):
        return f"{self.metric_key}={self.score}"


class AssistantEvalCaseResult(models.Model):
    run = models.ForeignKey(AssistantEvalScore, on_delete=models.CASCADE, related_name="cases")
    case_id = models.CharField(max_length=64)
    case_title = models.CharField(max_length=200, default="", blank=True)
    steps_total = models.PositiveIntegerField(default=0)
    steps_passed = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    cost_s = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    reason = models.TextField(default="", blank=True)
    failed_steps = models.JSONField(default=list)
    source_ref = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_eval_case_results"
        ordering = ["id"]
        verbose_name = "助手评测真题结果"
        verbose_name_plural = "助手评测真题结果"

    def __str__(self):
        return f"{self.case_id}:{self.steps_passed}/{self.steps_total}"
