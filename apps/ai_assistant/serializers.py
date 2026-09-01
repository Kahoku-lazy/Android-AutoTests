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
    vision_model_name = serializers.CharField(required=False, allow_blank=True)
    strong_model_name = serializers.CharField(required=False, allow_blank=True)
    strong_enabled = serializers.BooleanField(required=False)
    api_key = serializers.CharField(required=False, allow_blank=True)
    base_url = serializers.CharField(required=False, allow_blank=True)
    enable_knowledge_base = serializers.BooleanField(required=False)
    enable_workspace_tools = serializers.BooleanField(required=False)
    enable_business_tools = serializers.BooleanField(required=False)
    enable_mcp_tools = serializers.BooleanField(required=False)
    enable_skills = serializers.BooleanField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    skills_config = serializers.JSONField(required=False)
    knowledge_sources = serializers.JSONField(required=False)
    route_configs = serializers.JSONField(required=False)
    max_loops = serializers.IntegerField(required=False)

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


class AgentListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.CharField()


class AgentDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    vision_model_name = serializers.CharField()
    strong_model_name = serializers.CharField()
    strong_enabled = serializers.BooleanField()
    api_key = serializers.SerializerMethodField()
    base_url = serializers.SerializerMethodField()
    enable_knowledge_base = serializers.BooleanField()
    enable_workspace_tools = serializers.BooleanField()
    enable_business_tools = serializers.BooleanField()
    enable_mcp_tools = serializers.BooleanField()
    enable_skills = serializers.BooleanField()
    skills_config = serializers.JSONField()
    knowledge_sources = serializers.JSONField()
    route_configs = serializers.SerializerMethodField()
    max_loops = serializers.IntegerField()
    status = serializers.CharField()
    is_connected = serializers.BooleanField()
    last_checked_at = serializers.SerializerMethodField()
    available_models = serializers.SerializerMethodField()
    created_at = serializers.CharField()

    def _is_superuser(self):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return bool(user is not None and getattr(user, "is_superuser", False))

    def get_api_key(self, obj):
        if not self._is_superuser():
            return ""
        from .api import decrypt_key, mask_key

        return mask_key(decrypt_key(obj.api_key) if obj.api_key else "")

    def get_base_url(self, obj):
        return obj.base_url if self._is_superuser() else ""

    def get_last_checked_at(self, obj):
        return str(obj.last_checked_at) if obj.last_checked_at else None

    def get_available_models(self, obj):
        return json.loads(obj.available_models) if obj.available_models else []

    def get_route_configs(self, obj):
        if not self._is_superuser():
            return {}
        from .api import decrypt_route_configs, mask_route_configs

        return mask_route_configs(decrypt_route_configs(obj.route_configs or {}))


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


class TaskSubmitInputSerializer(serializers.Serializer):
    """任务提交入参 — goal 必填、route 枚举（device_control/platform_task）。"""

    goal = serializers.CharField(required=True, allow_blank=False)
    requirements = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.CharField(required=False, allow_blank=True, default="")
    route = serializers.ChoiceField(choices=["device_control", "platform_task"], required=True)
    report_name = serializers.CharField(required=False, allow_blank=True, default="")
    checklist = serializers.CharField(required=False, allow_blank=True, default="")
    device_serial = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_goal(self, value):
        goal = (value or "").strip()
        if not goal:
            raise serializers.ValidationError("任务目标不能为空")
        return goal
