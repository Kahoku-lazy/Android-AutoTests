"""字段形状校验。不查库。存在性由 agent_configs / model_configs 负责。"""

from rest_framework import serializers

# 类型取值：执行者 / 验收者 / 规划者。与 AIRoleKind.KIND_CHOICES 同源，改一处必须改两处。
ROLE_KIND_VALUES = ("executor", "verifier", "planner")


def _valid_http_url(value, schemes: set[str] | None = None) -> str:
    """地址必须是带主机名的链接。实时语音额外允许 ws 与 wss。"""
    from urllib.parse import urlparse

    url = str(value or "").strip()
    if not url:
        raise serializers.ValidationError("API 地址不能为空")
    parsed = urlparse(url)
    allowed = schemes or {"http", "https"}
    if parsed.scheme not in allowed or not parsed.netloc:
        names = "、".join(sorted(allowed))
        raise serializers.ValidationError(f"API 地址必须是 {names} 链接")
    return url


class ModelConfigSerializer(serializers.Serializer):
    """模型配置入参与出参。只校验字段形状，不创建模型。"""

    id = serializers.IntegerField(read_only=True)
    provider = serializers.ChoiceField(choices=["deepseek", "dashscope", "govee"])
    api_protocol = serializers.ChoiceField(choices=["deepseek", "dashscope", "openai"])
    model_kind = serializers.ChoiceField(choices=["chat", "tts", "realtime"], default="chat")
    voice = serializers.CharField(required=False, allow_blank=True, max_length=64)
    api_key_env = serializers.ChoiceField(
        choices=["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "GOVEE_API_KEY"]
    )
    base_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    model_name = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate(self, attrs):
        provider = attrs.get("provider")
        key = attrs.get("api_key_env")
        if provider and key:
            from engines.backend_bridge.models.catalog import expected_key

            try:
                expected = expected_key(provider)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc
            if key != expected:
                raise serializers.ValidationError("厂商与密钥环境变量不匹配")
        kind = attrs.get("model_kind") or "chat"
        if kind in {"chat", "realtime"} and ("base_url" in attrs or not self.partial):
            schemes = {"http", "https", "ws", "wss"} if kind == "realtime" else {"http", "https"}
            attrs["base_url"] = _valid_http_url(attrs.get("base_url"), schemes)
        attrs["model_name"] = (attrs.get("model_name") or "").strip()
        if self.context.get("require_model_name") and not attrs["model_name"]:
            raise serializers.ValidationError("模型名称不能为空")
        return attrs


class RoleInputSerializer(serializers.Serializer):
    """Agent 配置入参。不查模型配置是否存在。

    `kinds`：新建 MUST 恰好 1 项（在视图里校验，因为 PATCH 缺省表示不改动）；
    更新时显式提交 [] 表示置为未分类。一份配置 MUST NOT 同时有多个类型。
    """

    name = serializers.CharField(required=False, max_length=200)
    model_config_id = serializers.IntegerField(required=False, min_value=1)
    system_prompt = serializers.CharField(required=False, allow_blank=True)
    kinds = serializers.ListField(
        child=serializers.ChoiceField(choices=ROLE_KIND_VALUES),
        required=False,
    )

    def validate_name(self, value):
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("名称不能为空")
        return name

    def validate_kinds(self, value):
        kinds = list(dict.fromkeys(value))
        if len(kinds) != len(value):
            raise serializers.ValidationError("类型不能重复")
        if len(kinds) > 1:
            raise serializers.ValidationError("一份配置只能有一个类型")
        return kinds


class AssistantInputSerializer(serializers.Serializer):
    """助手名片入参。头像字节由视图解码后传入写库层。"""

    display_name = serializers.CharField(required=False, max_length=200)
    role_id = serializers.CharField(required=False, max_length=11)
    tools = serializers.ListField(required=False, child=serializers.DictField())
    revision = serializers.IntegerField(required=False)

    def validate_display_name(self, value):
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("名称不能为空")
        return name


class AssistantOutputSerializer(serializers.Serializer):
    """助手列表出参。不下发头像正文。"""

    assistant_id = serializers.CharField()
    display_name = serializers.CharField()
    has_avatar = serializers.SerializerMethodField()
    marker = serializers.CharField()
    role_id = serializers.CharField()
    role_name = serializers.SerializerMethodField()
    tools = serializers.JSONField()
    release_state = serializers.CharField()
    revision = serializers.IntegerField()
    created_at = serializers.DateTimeField()

    def get_has_avatar(self, obj) -> bool:
        return bool(obj.avatar)

    def get_role_name(self, obj) -> str:
        names = self.context.get("role_names") or {}
        return names.get(obj.role_id, "")


class SopWorkflowInputSerializer(serializers.Serializer):
    """新建或编辑工作流入参。编排与种类只在新建时生效。"""

    name = serializers.CharField(max_length=200)
    orchestration = serializers.CharField(max_length=16, required=False, default="sop")
    kind = serializers.CharField(max_length=32, required=False, default="ui_automation")
    executor_assistant_id = serializers.CharField(max_length=12, required=False, allow_blank=True)
    verifier_assistant_id = serializers.CharField(max_length=12, required=False, allow_blank=True)
    leader_assistant_id = serializers.CharField(max_length=12, required=False, allow_blank=True)
    members = serializers.ListField(child=serializers.DictField(), required=False, default=list)

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("名称不能为空")
        return name


class SopWorkflowOutputSerializer(serializers.Serializer):
    """工作流出参。不下发提示词、模型参数或工具勾选。"""

    id = serializers.IntegerField()
    name = serializers.CharField()
    orchestration = serializers.CharField()
    kind = serializers.CharField()
    executor_assistant_id = serializers.CharField()
    verifier_assistant_id = serializers.CharField()
    leader_assistant_id = serializers.CharField()
    members = serializers.JSONField()
    release_state = serializers.CharField()
    revision = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class RoleOutputSerializer(serializers.Serializer):
    """Agent 配置出参。关联字段由写库层 select_related 后交给这里。"""

    role_id = serializers.CharField()
    name = serializers.CharField()
    model_config_id = serializers.IntegerField(source="model_config.id", allow_null=True)
    provider = serializers.CharField(source="model_config.provider", default="")
    api_key_env = serializers.CharField(source="model_config.api_key_env", default="")
    model_name = serializers.CharField(source="model_config.model_name", default="")
    base_url = serializers.CharField(source="model_config.base_url", default="")
    api_protocol = serializers.CharField(source="model_config.api_protocol", default="")
    system_prompt = serializers.CharField()
    kinds = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_kinds(self, obj) -> list[str]:
        """类型标签数组；未分类时为空数组。prefetch_related 生效时不额外查库。"""
        return [item.kind for item in obj.kinds.all()]
