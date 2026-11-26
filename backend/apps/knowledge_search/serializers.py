from rest_framework import serializers

from .models import KnowledgeModule, KsEvalQuery, KsEvalRun


class KnowledgeModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeModule
        fields = ["id", "name", "description", "data_dir", "enabled", "created_at", "updated_at"]
        read_only_fields = fields


class ModuleWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64)
    description = serializers.CharField(max_length=200)
    data_dir = serializers.CharField(max_length=500)
    enabled = serializers.BooleanField(required=False, default=True)


class ModulePatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=False)
    description = serializers.CharField(max_length=200, required=False)
    data_dir = serializers.CharField(max_length=500, required=False)
    enabled = serializers.BooleanField(required=False)


class RetrievalSettingsSerializer(serializers.Serializer):
    embedding_model_id = serializers.IntegerField(min_value=1)
    top_k = serializers.IntegerField(min_value=1)
    score_threshold = serializers.FloatField(min_value=0, max_value=1)
    chunk_size = serializers.IntegerField(min_value=1)
    chunk_overlap = serializers.IntegerField(min_value=1)
    index_epoch = serializers.IntegerField(read_only=True)
    reindex_required = serializers.BooleanField(read_only=True)


class QuerySerializer(serializers.Serializer):
    question = serializers.CharField(allow_blank=False)
    bases = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    top_k = serializers.IntegerField(required=False, min_value=1)


class EvalTriggerSerializer(serializers.Serializer):
    module_id = serializers.IntegerField()
    model_config_id = serializers.IntegerField()
    pos_count = serializers.IntegerField(required=False, min_value=1, max_value=100, default=30)
    neg_count = serializers.IntegerField(required=False, min_value=0, max_value=100, default=10)


class EvalRunSerializer(serializers.ModelSerializer):
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
            "phase",
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
