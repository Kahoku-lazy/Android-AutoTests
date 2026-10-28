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
    # 任务类型：device_control=设备执行；case_authoring=家电测试用例编写。
    task_kind = models.CharField(max_length=32, default="device_control")
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
