"""ai-assistant ORM models — ai_ prefix tables. AgentScope-powered agent management."""

from django.db import models


class AIModelConfig(models.Model):
    """模型配置 → ai_model_configs。

    一条记录是某个密钥环境变量下的一个模型。同一个密钥可以有多条。
    只存环境变量名，不存密钥明文。
    """

    PROVIDER_CHOICES = [
        ("deepseek", "deepseek"),
        ("dashscope", "dashscope"),
        ("govee", "govee"),
    ]
    API_KEY_CHOICES = [
        ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
        ("DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
        ("GOVEE_API_KEY", "GOVEE_API_KEY"),
    ]

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
    api_key_env = models.CharField(max_length=64, choices=API_KEY_CHOICES)
    # 调用协议：deepseek / dashscope / openai。openai 表示 OpenAI 兼容协议。
    api_protocol = models.CharField(max_length=32, default="", blank=True)
    # chat=聊天，tts=语音合成，realtime=实时语音。决定后面按哪一类模型使用。
    model_kind = models.CharField(max_length=32, default="chat", blank=True)
    voice = models.CharField(max_length=64, default="", blank=True)
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
    """Agent 配置 → ai_roles。

    一条记录只登记三样：名称、一条模型配置、系统提示词。
    厂商、密钥名、地址、协议都从关联的模型配置带出，不在本表再存一份。
    """

    # 对外短标识：YYYYMMDD + 3 位随机字符，创建后不变。
    role_id = models.CharField(max_length=11, unique=True)
    # 区分大小写：MySQL 默认排序规则不区分，显式用 bin。
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


class AIAssistant(models.Model):
    """用户助手名片 → ai_assistants。

    只存展示字段、笔色、对运营 Agent 配置的引用，以及工具勾选。
    不复制系统提示词和模型连接参数。
    """

    # 对外短标识：YYYYMMDD_XXX，创建后不变。
    assistant_id = models.CharField(max_length=12, unique=True)
    display_name = models.CharField(max_length=200)
    # 压缩后的 JPEG base64；空串表示用笔色圆。
    avatar = models.TextField(default="", blank=True)
    marker = models.CharField(max_length=16)
    # 不建外键：运营配置被删后名片仍在，对话前再校验。
    role_id = models.CharField(max_length=11)
    tools = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_assistants"
        verbose_name = "助手名片"
        verbose_name_plural = "助手名片"

    def __str__(self):
        return f"{self.assistant_id} {self.display_name}"


class AISopWorkflow(models.Model):
    """SOP 工作流 → ai_sop_workflows。

    只存名称与两张名片编号。提示词、模型连接参数和工具勾选在运行时现读，
    不复制进本表。
    """

    name = models.CharField(max_length=200)
    executor_assistant_id = models.CharField(max_length=12)
    verifier_assistant_id = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_sop_workflows"
        verbose_name = "SOP 工作流"
        verbose_name_plural = "SOP 工作流"

    def __str__(self):
        return self.name


class AIAssistantThread(models.Model):
    """测试对话栏 → ai_assistant_threads。

    snapshot 在首次发送时写入，之后本栏不跟随名片修改。
    """

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
    """对话栏里的一句 → ai_assistant_messages。"""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    thread = models.ForeignKey(
        AIAssistantThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16)
    content = models.TextField()
    # 该轮时间戳目录名，不是绝对路径。空串表示这一轮还没有报告。
    report_id = models.CharField(max_length=32, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_messages"
        ordering = ["id"]
        verbose_name = "助手对话消息"
        verbose_name_plural = "助手对话消息"

    def __str__(self):
        return f"{self.role}:{self.id}"
