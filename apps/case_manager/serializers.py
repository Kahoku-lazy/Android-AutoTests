"""case_manager DRF serializers — projects, directories, document cases."""

from rest_framework import serializers

from .models import (
    BUSINESS_TYPE_CHOICES,
    TEST_TYPE_CHOICES,
    CaseDirectory,
    CaseProject,
    TestDefinition,
)


class CaseProjectSerializer(serializers.ModelSerializer):
    case_count = serializers.IntegerField(read_only=True, required=False, default=0)

    class Meta:
        model = CaseProject
        fields = [
            "id",
            "name",
            "description",
            "created_by",
            "created_at",
            "updated_at",
            "case_count",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "case_count"]


class CaseDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDirectory
        fields = [
            "id",
            "project",
            "parent",
            "name",
            "sort_order",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class TestDefinitionSerializer(serializers.ModelSerializer):
    created_at_display = serializers.SerializerMethodField()
    updated_at_display = serializers.SerializerMethodField()

    class Meta:
        model = TestDefinition
        fields = [
            "id",
            "project",
            "directory",
            "title",
            "test_type",
            "business_type",
            "module",
            "precondition",
            "steps",
            "expected_result",
            "sort_order",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "created_at_display",
            "updated_at_display",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "created_at_display",
            "updated_at_display",
        ]
        extra_kwargs = {
            "test_type": {"choices": TEST_TYPE_CHOICES},
            "business_type": {"choices": BUSINESS_TYPE_CHOICES},
        }

    def get_created_at_display(self, obj):
        from .api_definitions import format_display_time

        return format_display_time(obj.created_at)

    def get_updated_at_display(self, obj):
        from .api_definitions import format_display_time

        return format_display_time(obj.updated_at)
