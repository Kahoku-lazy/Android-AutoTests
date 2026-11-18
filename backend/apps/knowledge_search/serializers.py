"""知识库检索请求与响应序列化器。"""

from rest_framework import serializers

from .models import KnowledgeModule, KsEvalQuery, KsEvalRun


class KnowledgeModuleSerializer(serializers.ModelSerializer):
    """模块登记响应形状（snake_case，前端侧转 camelCase）。"""

    class Meta:
        model = KnowledgeModule
        fields = ["id", "name", "description", "data_dir", "enabled", "created_at", "updated_at"]
        read_only_fields = fields


class ModuleWriteSerializer(serializers.Serializer):
    """新增模块入参。"""

    name = serializers.CharField(max_length=64)
    description = serializers.CharField(max_length=200)
    data_dir = serializers.CharField(max_length=500)
    enabled = serializers.BooleanField(required=False, default=True)


class ModulePatchSerializer(serializers.Serializer):
    """编辑模块入参（至少一个字段）。"""

    name = serializers.CharField(max_length=64, required=False)
    description = serializers.CharField(max_length=200, required=False)
    data_dir = serializers.CharField(max_length=500, required=False)
    enabled = serializers.BooleanField(required=False)


class QuerySerializer(serializers.Serializer):
    """多选提问入参：问题与勾选库名均非空。"""

    question = serializers.CharField(allow_blank=False)
    bases = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    top_k = serializers.IntegerField(required=False, min_value=1)


class EvalTriggerSerializer(serializers.Serializer):
    """触发自动评测入参：模块 + chat 模型配置 + 题量（默认 30 正 + 10 负）。"""

    module_id = serializers.IntegerField()
    model_config_id = serializers.IntegerField()
    pos_count = serializers.IntegerField(required=False, min_value=1, max_value=100, default=30)
    neg_count = serializers.IntegerField(required=False, min_value=0, max_value=100, default=10)


class EvalRunSerializer(serializers.ModelSerializer):
    """评测运行响应形状。"""

    class Meta:
        model = KsEvalRun
        fields = [
            "id",
            "run_id",
            "module_name",
            "model_snapshot",
            "pos_count",
            "neg_count",
            "status",
            "progress_done",
            "progress_total",
            "metrics",
            "cost_estimate",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EvalQuerySerializer(serializers.ModelSerializer):
    """评测逐题明细响应形状。"""

    class Meta:
        model = KsEvalQuery
        fields = [
            "id",
            "kind",
            "question",
            "gold_document_id",
            "gold_source",
            "source_chunk_index",
            "source_text",
            "hits",
            "rank",
            "is_hit",
        ]
        read_only_fields = fields
