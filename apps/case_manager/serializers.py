"""case_manager DRF serializers — 4 case types + directory.

All four case-type models share identical collaboration/visibility/lock fields.
Each serializer handles its type-specific fields (steps_json, config_json, rows, etc.).
"""

import json

from rest_framework import serializers

from .models import CaseDirectory, TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase

# ── Helpers ──


def _parse_json_text(value):
    """Parse a TextField-stored JSON string into a Python object."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    return value if isinstance(value, (list, dict)) else []


def _ensure_json_text(value):
    """Encode a Python object as a JSON string for TextField storage."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


# ── Shared fields (all 4 case types) ──

_SHARED_FIELDS = [
    "id",
    "title",
    "case_type",
    "category",
    "priority",
    "description",
    "precondition",
    "enabled",
    "directory",
    "directory_name",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "locked",
    "visibility",
    "permitted_users",
    "permission",
    "permitted_editors",
    "editing_by",
    "editing_since",
]

_SHARED_READONLY = ["id", "created_at", "updated_at", "directory_name"]


class CaseDirectorySerializer(serializers.ModelSerializer):
    """Two-level case directory."""

    doc_count = serializers.IntegerField(read_only=True, default=0)
    children = serializers.SerializerMethodField()

    class Meta:
        model = CaseDirectory
        fields = [
            "id",
            "name",
            "case_type",
            "parent_id",
            "sort_order",
            "created_by",
            "allow_create",
            "allow_delete",
            "created_at",
            "updated_at",
            "doc_count",
            "children",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children(self, obj):
        if not hasattr(obj, "_prefetched_children"):
            children = obj.children.all().order_by("sort_order", "id")
        else:
            children = obj._prefetched_children
        return CaseDirectorySerializer(children, many=True).data


# ═══════════════════════════════════════════════════════
# TestDefinition (UI Automation)
# ═══════════════════════════════════════════════════════


class TestDefinitionSerializer(serializers.ModelSerializer):
    """UI automation test case — steps_json + watchers + IoT PRD fields."""

    directory_name = serializers.CharField(source="directory.name", read_only=True)
    steps_data = serializers.SerializerMethodField()
    steps_data_write = serializers.JSONField(source="steps_json", write_only=True, required=False)
    # watchers is a native Django JSONField — auto-handled
    permitted_users_list = serializers.SerializerMethodField()
    permitted_editors_list = serializers.SerializerMethodField()

    class Meta:
        model = TestDefinition
        fields = [
            *_SHARED_FIELDS,
            "steps",
            "steps_data",
            "steps_data_write",
            "watchers",
            "package_name",
            "design_method",
            "expected_result",
            "metrics",
            "permitted_users_list",
            "permitted_editors_list",
        ]
        read_only_fields = [*_SHARED_READONLY, "steps_data"]

    def get_steps_data(self, obj):
        return _parse_json_text(obj.steps_json)

    def get_permitted_users_list(self, obj):
        return _parse_json_text(obj.permitted_users)

    def get_permitted_editors_list(self, obj):
        return _parse_json_text(obj.permitted_editors)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Remove write-only field from output
        ret.pop("steps_data_write", None)
        # Merge steps_data_write into steps if needed
        return ret


# ═══════════════════════════════════════════════════════
# ApiTestCase (API Testing)
# ═══════════════════════════════════════════════════════


class ApiTestCaseSerializer(serializers.ModelSerializer):
    """API test case — config_json (native Django JSONField, auto-handled)."""

    directory_name = serializers.CharField(source="directory.name", read_only=True)
    permitted_users_list = serializers.SerializerMethodField()
    permitted_editors_list = serializers.SerializerMethodField()

    class Meta:
        model = ApiTestCase
        fields = [
            *_SHARED_FIELDS,
            "config_json",
            "permitted_users_list",
            "permitted_editors_list",
        ]
        read_only_fields = [*_SHARED_READONLY]

    def get_permitted_users_list(self, obj):
        return _parse_json_text(obj.permitted_users)

    def get_permitted_editors_list(self, obj):
        return _parse_json_text(obj.permitted_editors)


# ═══════════════════════════════════════════════════════
# StorageTestCase (Storage / Business Functions)
# ═══════════════════════════════════════════════════════


class StorageTestCaseSerializer(serializers.ModelSerializer):
    """Storage test case — custom_columns + rows (native JSONField)."""

    directory_name = serializers.CharField(source="directory.name", read_only=True)
    steps_data = serializers.SerializerMethodField()
    steps_data_write = serializers.JSONField(source="steps_json", write_only=True, required=False)
    permitted_users_list = serializers.SerializerMethodField()
    permitted_editors_list = serializers.SerializerMethodField()

    class Meta:
        model = StorageTestCase
        fields = [
            *_SHARED_FIELDS,
            "steps",
            "steps_data",
            "steps_data_write",
            "expected_result",
            "design_method",
            "metrics",
            "custom_columns",
            "rows",
            "permitted_users_list",
            "permitted_editors_list",
        ]
        read_only_fields = [*_SHARED_READONLY, "steps_data"]

    def get_steps_data(self, obj):
        return _parse_json_text(obj.steps_json)

    def get_permitted_users_list(self, obj):
        return _parse_json_text(obj.permitted_users)

    def get_permitted_editors_list(self, obj):
        return _parse_json_text(obj.permitted_editors)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop("steps_data_write", None)
        return ret


# ═══════════════════════════════════════════════════════
# WebTestCase (Web Automation)
# ═══════════════════════════════════════════════════════


class WebTestCaseSerializer(serializers.ModelSerializer):
    """Web automation test case — url + steps_json + custom_columns + rows."""

    directory_name = serializers.CharField(source="directory.name", read_only=True)
    steps_data = serializers.SerializerMethodField()
    steps_data_write = serializers.JSONField(source="steps_json", write_only=True, required=False)
    permitted_users_list = serializers.SerializerMethodField()
    permitted_editors_list = serializers.SerializerMethodField()

    class Meta:
        model = WebTestCase
        fields = [
            *_SHARED_FIELDS,
            "url",
            "steps",
            "steps_data",
            "steps_data_write",
            "expected_result",
            "design_method",
            "metrics",
            "custom_columns",
            "rows",
            "permitted_users_list",
            "permitted_editors_list",
        ]
        read_only_fields = [*_SHARED_READONLY, "steps_data"]

    def get_steps_data(self, obj):
        return _parse_json_text(obj.steps_json)

    def get_permitted_users_list(self, obj):
        return _parse_json_text(obj.permitted_users)

    def get_permitted_editors_list(self, obj):
        return _parse_json_text(obj.permitted_editors)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop("steps_data_write", None)
        return ret
