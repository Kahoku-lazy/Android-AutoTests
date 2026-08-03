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
    api_key = models.CharField(max_length=500, default="", blank=True)
    base_url = models.CharField(max_length=500, default="", blank=True)
    system_prompt = models.TextField(default="", blank=True)
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=4096)
    # AgentScope 2.0 fields
    formatter = models.CharField(max_length=50, default="dashscope")
    max_iters = models.IntegerField(default=10)
    parallel_tool_calls = models.BooleanField(default=True)
    print_hint_msg = models.BooleanField(default=False)
    memory_mode = models.CharField(max_length=20, default="inmemory")  # inmemory | longterm
    long_term_memory_mode = models.CharField(max_length=20, default="both")
    enable_meta_tool = models.BooleanField(default=False)
    enable_rewrite_query = models.BooleanField(default=True)
    generate_kwargs = models.TextField(default="{}", blank=True)
    compression_enabled = models.BooleanField(default=False)
    compression_threshold = models.IntegerField(default=10000)
    compression_keep_recent = models.IntegerField(default=3)
    compression_prompt = models.TextField(default="", blank=True)
    compression_template = models.TextField(default="", blank=True)
    tts_enabled = models.BooleanField(default=False)
    enable_knowledge_base = models.BooleanField(default=True)
    # Per-agent workspace skill toggles.
    # JSON object: {"Bash": true, "Read": true, "Write": false, ...}
    # Missing keys default to true (enabled).
    skills_config = models.JSONField(default=dict, blank=True)
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
    # Cached AgentScope credential — reused across sessions until API key / base_url changes
    agent_scope_credential_id = models.CharField(max_length=100, default="", blank=True)
    credential_hash = models.CharField(max_length=64, default="", blank=True)
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


class AITool(models.Model):
    """Tool / MCP / Skill config → ai_tools."""

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="tools")
    name = models.CharField(max_length=200)
    tool_type = models.CharField(max_length=20, default="mcp")
    config_json = models.TextField(default="{}")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_tools"
        verbose_name = "工具配置"
        verbose_name_plural = "工具配置"

    def __str__(self):
        return f"{self.name} [{self.tool_type}]"


class AISharedTool(models.Model):
    """Shared toolbox item — skills, tools, and extensions reusable across agents.

    Unlike AITool (which is per-agent), items here are global and can be
    imported into any agent via POST /agents/{id}/tools/import-from-toolbox.
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
    status = models.CharField(max_length=20, default="pending")
    result = models.TextField(default="", blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
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
