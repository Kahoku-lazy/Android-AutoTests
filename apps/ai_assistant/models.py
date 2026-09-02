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
    # 多线路模型配置：{"device_control": {"planner": {...}, "executor": {...}, "verifier": {...}}, "platform_task": {...}}
    # 每条线路的 api_key 经 Fernet 加密；读取时脱敏。
    route_configs = models.JSONField(default=dict, blank=True)
    # 工作流循环次数：executor ↔ verifier 内层循环的最大重试次数
    max_loops = models.IntegerField(default=3)
    api_key = models.CharField(max_length=500, default="", blank=True)
    base_url = models.CharField(max_length=500, default="", blank=True)
    enable_knowledge_base = models.BooleanField(default=False)
    # Per-agent workspace skill toggles.
    # JSON object: {"Bash": true, "Read": true, "Write": false, ...}
    # Missing keys default to true (enabled).
    skills_config = models.JSONField(default=dict, blank=True)
    # Capability toggles — all default False (pure conversation model).
    # User enables capabilities through the frontend UI.
    enable_workspace_tools = models.BooleanField(default=False)  # Bash/Edit/Glob/Grep/Read/Write
    enable_business_tools = models.BooleanField(
        default=False
    )  # 23 platform tools (device/case/test/elements)
    enable_mcp_tools = models.BooleanField(default=False)  # User-configured MCP servers
    enable_skills = models.BooleanField(default=False)  # User-uploaded skill folders
    # Per-agent knowledge base document filter.
    # Dict: {"doc:id": true/false}.  Key presence = imported, value = enabled.
    # Empty dict = no documents imported.
    knowledge_sources = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default="active")
    # Health check fields
    last_checked_at = models.DateTimeField(null=True, blank=True)
    is_connected = models.BooleanField(default=False)
    available_models = models.TextField(default="", blank=True)  # JSON list of model names
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


class AISharedTool(models.Model):
    """共享工具箱项 — skill / mcp / extension，全局唯一，直接启用/停用。

    平台只用单一智能体：`enabled` 直接决定该智能体是否使用，
    无需 per-agent 副本或「导入」步骤。
    """

    name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=20)  # 'skill' | 'mcp' | 'extension'
    description = models.TextField(default="", blank=True)
    config_json = models.TextField(default="{}")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_shared_tools"
        verbose_name = "共享工具"
        verbose_name_plural = "共享工具"

    def __str__(self):
        return f"{self.name} [{self.item_type}]"


class AIPlatformTool(models.Model):
    """Global platform business tool enable/disable state → ai_platform_tools.

    全局开关（所有智能体共享）：AI 工具箱统一决定启用/停用哪个平台业务工具，
    智能体只保留 `enable_business_tools` 总开关。默认（无记录）＝启用；
    停用 = 记录 enabled=False；启用 = 删除记录回默认。
    """

    name = models.CharField(max_length=200, unique=True)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_platform_tools"
        verbose_name = "平台业务工具开关"
        verbose_name_plural = "平台业务工具开关"

    def __str__(self):
        return f"{self.name} [{'启用' if self.enabled else '停用'}]"


class AIConversation(models.Model):
    """Chat conversation → ai_conversations."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_conversations",
    )
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=500, default="新对话")
    status = models.CharField(max_length=20, default="active")
    agent_scope_session_id = models.CharField(
        max_length=200, default="", blank=True, help_text="AgentScope session ID for SSE streaming"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_conversations"
        verbose_name = "对话"
        verbose_name_plural = "对话"

    def __str__(self):
        return f"{self.title} [{self.agent.name}]"


class AIMessage(models.Model):
    """Chat message → ai_messages."""

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20)
    content = models.TextField(default="", blank=True)
    tool_calls = models.TextField(default="", blank=True)
    # Complete ContentBlock structure from AgentScope SSE event stream
    # Stores the full block list: [{type, id, thinking?, name?, input?, output?, state?, hint?}]
    blocks = models.TextField(default="[]", blank=True)
    # Why the reply ended: 'normal' | 'exceed_max_iters' | 'stopped' | 'error'
    reason = models.CharField(max_length=30, default="normal", blank=True)
    tokens = models.IntegerField(default=0)
    input_tokens = models.IntegerField(default=0)
    cache_input_tokens = models.IntegerField(default=0)
    cache_creation_input_tokens = models.IntegerField(default=0)
    model_name = models.CharField(max_length=100, default="", blank=True)
    # Transport used for this reply: 'sse' | 'fallback' | '' (legacy/unknown)
    flow = models.CharField(max_length=20, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_messages"
        ordering = ["created_at"]
        verbose_name = "消息"
        verbose_name_plural = "消息"

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


class AITask(models.Model):
    """Agent task → ai_tasks."""

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=500)
    description = models.TextField(default="", blank=True)
    # 任务发布字段
    goal = models.TextField(default="", blank=True)  # 任务目标（必填）
    requirements = models.TextField(default="", blank=True)  # 任务要求
    attachment = models.CharField(max_length=500, default="", blank=True)  # 任务附件文件路径
    route = models.CharField(
        max_length=50, default="device_control"
    )  # 线路：device_control/platform_task
    checklist = models.TextField(default="", blank=True)  # 任务校验清单
    report_name = models.CharField(max_length=200, default="", blank=True)  # 报告文件名
    device_serial = models.CharField(
        max_length=100, default="", blank=True
    )  # 指定设备 serial（空则第一台在线）
    status = models.CharField(max_length=20, default="pending")
    result = models.TextField(default="", blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    # ── token 用量（任务完成时由工作流采集落库）──
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_input_tokens = models.IntegerField(default=0)
    # 按模型拆分：{model_name: {"input_tokens", "output_tokens", "cache_input_tokens"}}
    # DeepSeek 费用按模型单价计价，故需保留分模型用量。
    model_usage = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_tasks"
        verbose_name = "任务"
        verbose_name_plural = "任务"

    def __str__(self):
        return f"{self.title} [{self.status}]"


class AIExecutionLog(models.Model):
    """Execution log → ai_execution_logs."""

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="logs")
    task = models.ForeignKey(
        AITask, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    level = models.CharField(max_length=10, default="info")
    message = models.TextField(default="", blank=True)
    metadata = models.TextField(default="{}", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_execution_logs"
        ordering = ["-created_at"]
        verbose_name = "执行日志"
        verbose_name_plural = "执行日志"

    def __str__(self):
        return f"[{self.level}] {self.message[:60]}"
