"""知识库检索请求与响应序列化器。"""

from rest_framework import serializers

from .models import KnowledgeModule


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
