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
        ("openai", "openai"),
    ]
    API_KEY_CHOICES = [
        ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
        ("DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
        ("OPENAI_API_KEY", "OPENAI_API_KEY"),
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


class AIRoleKind(models.Model):
    """Agent 配置的类型标签 → ai_role_kinds。

    一行只表示「一条配置的一个类型」，类型不写进 AIRole，
    角色记录仍只描述角色本身（见 specs/ai-role-registry）。
    关联以配置为父：配置删除时标签随之删除，不留孤儿行。
    """

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
            # 需求方口径：一份配置只能是执行者 / 验收者 / 规划者之一，先由库锁 1:1。
            # 将来放开多类型只需删掉这一条，表结构与 kinds 数组契约不动。
            models.UniqueConstraint(fields=["role"], name="uniq_ai_role_kind_role"),
            models.UniqueConstraint(fields=["role", "kind"], name="uniq_ai_role_kind_pair"),
        ]

    def __str__(self):
        return f"{self.role_id} {self.kind}"


class ModelUseGrant(models.Model):
    """模型主动使用名单 → ai_model_use_grants。

    一行表示这个人可以在对话和新建助手时主动选择该模型。
    空名单表示不能主动选择任何模型，不表示全部允许。
    已发布工作流使用冻结版本，不查这张表。
    """

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


class AssistantLiveRun(models.Model):
    """一次真模型评测 → ai_assistant_live_runs。

    发布只认指纹相符、样本集是当前这份、失败清单为空的最新一次完成运行。
    逐条过程在 AssistantLiveSample。旧的 scripted 自测不再作为发布依据。
    """

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    target_kind = models.CharField(max_length=16)
    target_id = models.CharField(max_length=32)
    fingerprint = models.CharField(max_length=64)
    sample_ids = models.JSONField(default=list)
    status = models.CharField(max_length=16, default=STATUS_PENDING)
    phase = models.CharField(max_length=32, default="", blank=True)
    progress_done = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    failures = models.JSONField(default=list)
    error = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_assistant_live_runs"
        verbose_name = "助手评测运行"
        verbose_name_plural = "助手评测运行"

    def __str__(self):
        return f"{self.target_kind}:{self.target_id} [{self.status}]"


class AssistantLiveSample(models.Model):
    """一条评测样本的规则结果与过程 → ai_assistant_live_samples。

    steps 只保留展示字段：角色、原文、工具名、入参摘要、返回摘要。
    不存密钥、图片或二进制。
    """

    run = models.ForeignKey(AssistantLiveRun, on_delete=models.CASCADE, related_name="samples")
    sample_id = models.CharField(max_length=32)
    title = models.CharField(max_length=200, default="", blank=True)
    passed = models.BooleanField(default=False)
    failures = models.JSONField(default=list)
    steps = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_live_samples"
        ordering = ["id"]
        verbose_name = "助手评测样本"
        verbose_name_plural = "助手评测样本"

    def __str__(self):
        return f"{self.sample_id} [{'过' if self.passed else '未过'}]"


class AssistantEvalRun(models.Model):
    """旧自测结果 → ai_assistant_eval_runs。

    只保留历史。发布不再读取本表，改认 AssistantLiveRun。
    """

    target_kind = models.CharField(max_length=16)
    target_id = models.CharField(max_length=32)
    fingerprint = models.CharField(max_length=64)
    sample_ids = models.JSONField(default=list)
    failures = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_eval_runs"
        verbose_name = "助手自测"
        verbose_name_plural = "助手自测"

    def __str__(self):
        return f"{self.target_kind}:{self.target_id}"


class AssistantRelease(models.Model):
    """已发布版本 → ai_assistant_releases。

    一行是发布当时复制出的运行内容。之后修改草稿不改这些行。
    密钥不进 payload，只保留密钥环境变量名。
    """

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
    """助手作者授权 → ai_assistant_author_grants。

    只记录被超级管理员单独授予的账号。超级管理员不需要记录，
    判定时天然算作者。停用账号时删除对应行，重新启用不自动恢复。
    """

    user_id = models.PositiveIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_author_grants"
        verbose_name = "助手作者授权"
        verbose_name_plural = "助手作者授权"

    def __str__(self):
        return str(self.user_id)


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
    # draft 只有作者和超级管理员可见；published 才对其他人开放。
    release_state = models.CharField(max_length=16, default="draft")
    # 每次保存加一。后保存的人若仍拿旧值，整次拒绝。
    revision = models.PositiveIntegerField(default=1)

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
    # 编排与种类成对保存。现有 UI 工作流回填为 sop + ui_automation。
    orchestration = models.CharField(max_length=16, default="sop")
    kind = models.CharField(max_length=32, default="ui_automation")
    executor_assistant_id = models.CharField(max_length=12, default="", blank=True)
    verifier_assistant_id = models.CharField(max_length=12, default="", blank=True)
    # Team 才使用。成员项为 {assistant_id, description}。
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
