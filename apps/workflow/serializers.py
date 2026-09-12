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


class WorkflowDirectoryTreeSerializer(serializers.ModelSerializer):
    """目录树 — 递归 children + 文档摘要."""

    children = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowDirectory
        fields = [
            "id",
            "name",
            "prototype_id",
            "parent_id",
            "sort_order",
            "doc_count",
            "created_at",
            "updated_at",
            "children",
            "documents",
        ]

    def get_children(self, obj):
        if not hasattr(obj, "_prefetched_children"):
            children = obj.children.all().order_by("sort_order", "id")
        else:
            children = obj._prefetched_children
        return WorkflowDirectoryTreeSerializer(children, many=True).data

    def get_documents(self, obj):
        if not hasattr(obj, "_prefetched_documents"):
            docs = obj.documents.filter(
                doc_type__in=WorkflowDocument.SUPPORTED_TYPES
            ).order_by("title")
        else:
            docs = [
                d
                for d in obj._prefetched_documents
                if d.doc_type in WorkflowDocument.SUPPORTED_TYPES
            ]
        return [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "doc_type": d.doc_type,
                "updated_at": d.updated_at.isoformat() if d.updated_at else "",
            }
            for d in docs
        ]


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

    config = serializers.JSONField(source="config_json")

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
