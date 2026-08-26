"""ai-assistant serializers — DRF 入参校验与输出 DTO。

分层约定（apps/AGENTS.md）：serializers 只做校验与 DTO，写库副作用全部走 api.py。
Batch 1/2 已全部迁移到 DRF；手写校验函数已随迁移移除。
"""

import json

from rest_framework import serializers

from apps.ai_assistant.agent_scope.provider_registry import VALID_PROVIDERS, validate_base_url

# ═══════════════════════════════════════════════════════════════════
# Agent 输入（创建/更新共用；业务默认值仍在 api.py 应用，与旧视图一致）
# ═══════════════════════════════════════════════════════════════════


class AgentInputSerializer(serializers.Serializer):
    """Agent 创建/更新入参校验 — 规则对齐旧 validate_agent_input。"""

    name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    avatar = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    model_provider = serializers.CharField(required=False, allow_blank=True)
    model_name = serializers.CharField(required=False, allow_blank=True)
    api_key = serializers.CharField(required=False, allow_blank=True)
    base_url = serializers.CharField(required=False, allow_blank=True)
    system_prompt = serializers.CharField(required=False, allow_blank=True)
    temperature = serializers.FloatField(required=False)
    max_tokens = serializers.IntegerField(required=False)
    formatter = serializers.CharField(required=False, allow_blank=True)
    max_iters = serializers.IntegerField(required=False)
    parallel_tool_calls = serializers.BooleanField(required=False)
    print_hint_msg = serializers.BooleanField(required=False)
    memory_mode = serializers.CharField(required=False, allow_blank=True)
    long_term_memory_mode = serializers.CharField(required=False, allow_blank=True)
    enable_meta_tool = serializers.BooleanField(required=False)
    enable_rewrite_query = serializers.BooleanField(required=False)
    enable_knowledge_base = serializers.BooleanField(required=False)
    enable_workspace_tools = serializers.BooleanField(required=False)
    enable_business_tools = serializers.BooleanField(required=False)
    enable_mcp_tools = serializers.BooleanField(required=False)
    enable_skills = serializers.BooleanField(required=False)
    generate_kwargs = serializers.CharField(required=False, allow_blank=True)
    compression_enabled = serializers.BooleanField(required=False)
    compression_threshold = serializers.IntegerField(required=False)
    compression_keep_recent = serializers.IntegerField(required=False)
    compression_prompt = serializers.CharField(required=False, allow_blank=True)
    compression_template = serializers.CharField(required=False, allow_blank=True)
    tts_enabled = serializers.BooleanField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    skills_config = serializers.JSONField(required=False)
    knowledge_sources = serializers.JSONField(required=False)
    tools = serializers.ListField(
        child=serializers.DictField(), required=False, default=list, allow_empty=True
    )
    platform_tools = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    def validate_name(self, value):
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Agent 名称不能为空")
        return name

    def validate_model_provider(self, value):
        provider = (value or "dashscope").strip()
        if provider not in VALID_PROVIDERS:
            raise serializers.ValidationError(f"不支持的模型提供商: {provider}")
        return provider

    def validate_base_url(self, value):
        base_url = (value or "").strip()
        if base_url:
            provider = self.initial_data.get("model_provider") or "dashscope"
            ok, msg = validate_base_url(provider, base_url)
            if not ok:
                raise serializers.ValidationError(msg)
            return base_url.rstrip("/")
        return ""

    def validate_temperature(self, value):
        if not (0 <= value <= 2):
            raise serializers.ValidationError("温度必须在 0-2 之间")
        return value

    def validate_max_tokens(self, value):
        if not (1 <= value <= 128000):
            raise serializers.ValidationError("max_tokens 必须在 1-128000 之间")
        return value

    def validate_generate_kwargs(self, value):
        gk = (value or "{}").strip()
        if gk and gk != "{}":
            try:
                json.loads(gk)
            except (json.JSONDecodeError, TypeError):
                raise serializers.ValidationError("generate_kwargs 必须是合法的 JSON 字符串")
        return gk


class ModelDetectInputSerializer(serializers.Serializer):
    """模型探测入参 — 规则对齐旧 validate_model_detect_input。"""

    model_provider = serializers.CharField(required=False, allow_blank=True)
    base_url = serializers.CharField(required=False, allow_blank=True)
    api_key = serializers.CharField(required=True, allow_blank=False)

    def validate_model_provider(self, value):
        provider = (value or "").strip()
        if provider and provider not in VALID_PROVIDERS:
            raise serializers.ValidationError(f"不支持的模型提供商: {provider}")
        return provider

    def validate_base_url(self, value):
        base_url = (value or "").strip()
        provider = (self.initial_data.get("model_provider") or "").strip()
        if base_url and provider:
            ok, msg = validate_base_url(provider, base_url)
            if not ok:
                raise serializers.ValidationError(msg)
        return base_url

    def validate_api_key(self, value):
        key = (value or "").strip()
        if not key:
            raise serializers.ValidationError("API Key 不能为空")
        return key


# ═══════════════════════════════════════════════════════════════════
# Agent 输出 DTO（字段契约对齐 PRD-08 §5.2）
# ═══════════════════════════════════════════════════════════════════


class AgentToolOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tool_type = serializers.CharField()
    config_json = serializers.CharField()
    enabled = serializers.BooleanField()


class AgentListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    status = serializers.CharField()
    tool_count = serializers.SerializerMethodField()
    created_at = serializers.CharField()

    def get_tool_count(self, obj):
        tools = obj.tools.all() if hasattr(obj, "tools") else []
        return sum(1 for t in tools if t.enabled)


class AgentDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    api_key = serializers.SerializerMethodField()
    base_url = serializers.CharField()
    system_prompt = serializers.CharField()
    temperature = serializers.FloatField()
    max_tokens = serializers.IntegerField()
    formatter = serializers.CharField()
    max_iters = serializers.IntegerField()
    parallel_tool_calls = serializers.BooleanField()
    print_hint_msg = serializers.BooleanField()
    memory_mode = serializers.CharField()
    long_term_memory_mode = serializers.CharField()
    enable_meta_tool = serializers.BooleanField()
    enable_rewrite_query = serializers.BooleanField()
    enable_knowledge_base = serializers.BooleanField()
    enable_workspace_tools = serializers.BooleanField()
    enable_business_tools = serializers.BooleanField()
    enable_mcp_tools = serializers.BooleanField()
    enable_skills = serializers.BooleanField()
    generate_kwargs = serializers.CharField()
    skills_config = serializers.JSONField()
    knowledge_sources = serializers.JSONField()
    compression_enabled = serializers.BooleanField()
    compression_threshold = serializers.IntegerField()
    compression_keep_recent = serializers.IntegerField()
    compression_prompt = serializers.CharField()
    compression_template = serializers.CharField()
    tts_enabled = serializers.BooleanField()
    status = serializers.CharField()
    tools = AgentToolOutputSerializer(many=True, source="tools.all")
    is_connected = serializers.BooleanField()
    last_checked_at = serializers.SerializerMethodField()
    available_models = serializers.SerializerMethodField()
    created_at = serializers.CharField()

    def get_api_key(self, obj):
        from .api import decrypt_key, mask_key

        return mask_key(decrypt_key(obj.api_key) if obj.api_key else "")

    def get_last_checked_at(self, obj):
        return str(obj.last_checked_at) if obj.last_checked_at else None

    def get_available_models(self, obj):
        return json.loads(obj.available_models) if obj.available_models else []


# ═══════════════════════════════════════════════════════════════════
# 对话 / 消息（Batch 2 迁 DRF）
# ═══════════════════════════════════════════════════════════════════


class ConversationCreateSerializer(serializers.Serializer):
    """新建对话入参 — title 缺省 '新对话'，截断 500。"""

    title = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_title(self, value):
        return (value or "新对话").strip() or "新对话"


class RenameInputSerializer(serializers.Serializer):
    """对话重命名入参 — 规则对齐旧 validate_rename_input。"""

    title = serializers.CharField(required=True, allow_blank=False, max_length=500)

    def validate_title(self, value):
        title = (value or "").strip()
        if not title:
            raise serializers.ValidationError("标题不能为空")
        return title[:500]


class MessageInputSerializer(serializers.Serializer):
    """保存消息入参 — 规则对齐旧 validate_message_input。"""

    role = serializers.CharField(required=False, allow_blank=True, default="assistant")
    content = serializers.CharField(required=False, allow_blank=True, default="")
    blocks = serializers.ListField(required=False, default=list, allow_empty=True)
    reason = serializers.CharField(required=False, allow_blank=True, default="normal")
    tokens = serializers.IntegerField(required=False, default=0)
    input_tokens = serializers.IntegerField(required=False, default=0)
    model_name = serializers.CharField(required=False, allow_blank=True, default="")
    flow = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        role = attrs.get("role", "assistant")
        content = (attrs.get("content") or "").strip()
        blocks = attrs.get("blocks") or []
        if role not in ("user", "assistant", "system"):
            raise serializers.ValidationError({"role": "无效的角色类型"})
        if role == "user" and not content and not blocks:
            raise serializers.ValidationError({"content": "消息内容不能为空"})
        if role == "assistant" and not content and not blocks:
            raise serializers.ValidationError({"content": "assistant 消息需要 content 或 blocks"})
        return attrs


class ConversationListSerializer(serializers.Serializer):
    """对话列表 DTO。"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    agent_scope_session_id = serializers.CharField()
    created_at = serializers.CharField()


class MessageListSerializer(serializers.Serializer):
    """消息列表 DTO — 字段契约对齐旧 list_messages。"""

    id = serializers.IntegerField()
    role = serializers.CharField()
    content = serializers.CharField()
    blocks = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    tool_calls = serializers.CharField()
    tokens = serializers.IntegerField()
    input_tokens = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    flow = serializers.SerializerMethodField()
    created_at = serializers.CharField()

    def get_blocks(self, obj):
        return json.loads(obj.blocks) if obj.blocks else []

    def get_reason(self, obj):
        return obj.reason or "normal"

    def get_input_tokens(self, obj):
        return obj.input_tokens or 0

    def get_model_name(self, obj):
        return obj.model_name or ""

    def get_flow(self, obj):
        return obj.flow or ""
