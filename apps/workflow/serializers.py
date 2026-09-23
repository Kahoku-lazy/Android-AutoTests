"""workflow DRF serializers — WorkflowPrototype, WorkflowDirectory, WorkflowDocument."""

from rest_framework import serializers

from .models import WorkflowDirectory, WorkflowDocument, WorkflowPrototype


class WorkflowPrototypeSerializer(serializers.ModelSerializer):
    """原型序列化器 — 含文档数量."""

    doc_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorkflowPrototype
        fields = [
            "id",
            "name",
            "description",
            "doc_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowDirectorySerializer(serializers.ModelSerializer):
    """目录序列化器 — 含文档数量."""

    doc_count = serializers.IntegerField(read_only=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    # parent_id 为裸 ID（int/null，null = 移到根，见 API-工作流.md §3.4）；
    # 存在性 / 跨原型判定属业务规则，归 api.py，故不用 PrimaryKeyRelatedField。
    parent_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = WorkflowDirectory
        fields = [
            "id",
            "name",
            "prototype_id",
            "parent_id",
            "parent_name",
            "sort_order",
            "doc_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowDocumentListSerializer(serializers.ModelSerializer):
    """文档列表 — 不含 config_json（体积大）."""

    class Meta:
        model = WorkflowDocument
        fields = [
            "id",
            "doc_id",
            "title",
            "doc_type",
            "prototype_id",
            "directory_id",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "doc_id", "created_at", "updated_at"]


class WorkflowDocumentDetailSerializer(serializers.ModelSerializer):
    """文档详情 — 含 config_json（前端字段名 config，读写均支持）."""

    # 写入统一经 api.py，故 config 非必填：局部提交（例如只改标题）不该被判"字段缺失"而 400。
    config = serializers.JSONField(source="config_json", required=False)
    # directory_id 为裸 ID（int/null，null = 移到原型根）；
    # DRF 默认把 FK 的 attname 当只读字段，显式声明才可写。
    # 存在性 / 跨原型判定属业务规则，归 api.py，故不用 PrimaryKeyRelatedField。
    directory_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = WorkflowDocument
        fields = [
            "id",
            "doc_id",
            "title",
            "doc_type",
            "prototype_id",
            "directory_id",
            "description",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "doc_id", "created_at", "updated_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if isinstance(ret.get("config"), str):
            import json

            try:
                ret["config"] = json.loads(ret["config"])
            except (json.JSONDecodeError, TypeError):
                ret["config"] = {}
        return ret
