"""字段形状校验。不查库。存在性由 agent_configs / model_configs 负责。"""

from rest_framework import serializers


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
    """Agent 配置入参。不查模型配置是否存在。"""

    name = serializers.CharField(required=False, max_length=200)
    model_config_id = serializers.IntegerField(required=False, min_value=1)
    system_prompt = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("名称不能为空")
        return name


class AssistantInputSerializer(serializers.Serializer):
    """助手名片入参。头像字节由视图解码后传入写库层。"""

    display_name = serializers.CharField(required=False, max_length=200)
    role_id = serializers.CharField(required=False, max_length=11)
    tools = serializers.ListField(required=False, child=serializers.DictField())

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
    created_at = serializers.DateTimeField()

    def get_has_avatar(self, obj) -> bool:
        return bool(obj.avatar)

    def get_role_name(self, obj) -> str:
        names = self.context.get("role_names") or {}
        return names.get(obj.role_id, "")


class SopWorkflowInputSerializer(serializers.Serializer):
    """新建 SOP 工作流入参。只收名称与两个名片编号。"""

    name = serializers.CharField(max_length=200)
    executor_assistant_id = serializers.CharField(max_length=12)
    verifier_assistant_id = serializers.CharField(max_length=12)

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("名称不能为空")
        return name


class SopWorkflowOutputSerializer(serializers.Serializer):
    """工作流出参。不下发提示词、模型参数或工具勾选。"""

    id = serializers.IntegerField()
    name = serializers.CharField()
    executor_assistant_id = serializers.CharField()
    verifier_assistant_id = serializers.CharField()
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
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
