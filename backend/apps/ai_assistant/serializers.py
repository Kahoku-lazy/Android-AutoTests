"""ai-assistant serializers — DRF 入参校验与输出 DTO。

分层约定（apps/AGENTS.md）：serializers 只做校验与 DTO，写库副作用全部走 api.py。
Batch 1/2 已全部迁移到 DRF；手写校验函数已随迁移移除。
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

# ═══════════════════════════════════════════════════════════════════
# Agent 输入（创建/更新共用；业务默认值仍在 api.py 应用，与旧视图一致）
# ═══════════════════════════════════════════════════════════════════


class AgentInputSerializer(serializers.Serializer):
    """Agent 基本信息入参 — 模型/线路改由后台维护，不再经配置页提交。"""

    name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    avatar = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Agent 名称不能为空")
        return name


# ═══════════════════════════════════════════════════════════════════
# Agent 输出 DTO（字段契约与需求一致）
# ═══════════════════════════════════════════════════════════════════


class AgentListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    task_kind = serializers.CharField()
    route_configs = serializers.SerializerMethodField()
    status = serializers.CharField()
    created_at = serializers.CharField()

    def get_route_configs(self, obj):
        """看板展示用：线路 name/avatar + 各角色 model_name/provider，不含 api_key。"""
        result = {}
        for route, route_data in (obj.route_configs or {}).items():
            if not isinstance(route_data, dict):
                continue
            entry = {
                "name": route_data.get("name") or "",
                "avatar": route_data.get("avatar") or "",
            }
            for role in ("planner", "executor", "verifier"):
                cfg = route_data.get(role)
                if isinstance(cfg, dict):
                    entry[role] = {
                        "model_name": cfg.get("model_name") or "",
                        "provider": cfg.get("provider") or "",
                    }
            result[route] = entry
        return result


class AgentDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    avatar = serializers.CharField()
    tags = serializers.CharField()
    description = serializers.CharField()
    model_provider = serializers.CharField()
    model_name = serializers.CharField()
    task_kind = serializers.CharField()
    vision_model_name = serializers.CharField()
    strong_model_name = serializers.CharField()
    strong_enabled = serializers.BooleanField()
    api_key = serializers.SerializerMethodField()
    base_url = serializers.SerializerMethodField()
    route_configs = serializers.SerializerMethodField()
    max_loops = serializers.IntegerField()
    status = serializers.CharField()
    created_at = serializers.CharField()

    def _is_superuser(self):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return bool(user is not None and getattr(user, "is_superuser", False))

    @extend_schema_field(OpenApiTypes.STR)
    def get_api_key(self, obj):
        if not self._is_superuser():
            return ""
        from .api import decrypt_key, mask_key

        return mask_key(decrypt_key(obj.api_key) if obj.api_key else "")

    @extend_schema_field(OpenApiTypes.STR)
    def get_base_url(self, obj):
        return obj.base_url if self._is_superuser() else ""

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_route_configs(self, obj):
        if not self._is_superuser():
            return {}
        from .api import decrypt_route_configs, mask_route_configs

        return mask_route_configs(decrypt_route_configs(obj.route_configs or {}))
