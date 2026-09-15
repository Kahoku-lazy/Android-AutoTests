"""element_locator DRF serializers — WebGroup, ApiGroup, WebElement, ApiEndpoint, PageFlow, WebPageFlow."""

from rest_framework import serializers

from .models import (
    ApiEndpoint,
    ApiGroup,
    PageFlow,
    WebElement,
    WebGroup,
    WebPageFlow,
)

# ── WebGroup ──


class WebGroupSerializer(serializers.ModelSerializer):
    element_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = WebGroup
        fields = [
            "id",
            "name",
            "parent_id",
            "is_folder",
            "sort_order",
            "created_at",
            "element_count",
            "children",
        ]
        read_only_fields = ["id", "created_at"]

    def get_element_count(self, obj) -> int:
        return getattr(obj, "element_count", obj.elements.count())

    def get_children(self, obj) -> list[dict]:
        children = (
            obj._prefetched_children
            if hasattr(obj, "_prefetched_children")
            else obj.children.all().order_by("sort_order", "id")
        )
        return WebGroupSerializer(children, many=True).data


# ── WebElement ──


class WebElementSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = WebElement
        fields = [
            "id",
            "name",
            "group_id",
            "group_name",
            "locator_type",
            "locator_value",
            "page_url",
            "description",
            "tags",
            "is_test_point",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── ApiGroup ──


class ApiGroupSerializer(serializers.ModelSerializer):
    endpoint_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = ApiGroup
        fields = [
            "id",
            "name",
            "parent_id",
            "is_folder",
            "sort_order",
            "created_at",
            "endpoint_count",
            "children",
        ]
        read_only_fields = ["id", "created_at"]

    def get_endpoint_count(self, obj) -> int:
        return getattr(obj, "endpoint_count", obj.endpoints.count())

    def get_children(self, obj) -> list[dict]:
        children = (
            obj._prefetched_children
            if hasattr(obj, "_prefetched_children")
            else obj.children.all().order_by("sort_order", "id")
        )
        return ApiGroupSerializer(children, many=True).data


# ── ApiEndpoint ──


class ApiEndpointSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = ApiEndpoint
        fields = [
            "id",
            "name",
            "group_id",
            "group_name",
            "method",
            "url",
            "headers",
            "request_body_schema",
            "response_body_schema",
            "description",
            "tags",
            "is_test_point",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── PageFlow ──


class PageFlowSerializer(serializers.ModelSerializer):
    from_label = serializers.CharField(source="from_page.label", read_only=True)
    to_label = serializers.CharField(source="to_page.label", read_only=True)
    trigger_text = serializers.CharField(source="trigger_element.text_val", read_only=True)

    class Meta:
        model = PageFlow
        fields = [
            "id",
            "from_page_id",
            "to_page_id",
            "trigger_element_id",
            "from_label",
            "to_label",
            "trigger_text",
            "trigger_action",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── WebPageFlow ──


class WebPageFlowSerializer(serializers.ModelSerializer):
    from_name = serializers.CharField(source="from_group.name", read_only=True)
    to_name = serializers.CharField(source="to_group.name", read_only=True)
    # FK 用裸 id 而非 PrimaryKeyRelatedField：存在性与业务规则（目录判定）归 view / api.py，
    # 且 DRF 会把 FK 的 `*_id` attname 建成只读字段 —— 不改则 create 必现 NOT NULL 500。
    from_group_id = serializers.IntegerField()
    to_group_id = serializers.IntegerField()
    trigger_element_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = WebPageFlow
        fields = [
            "id",
            "from_group_id",
            "to_group_id",
            "trigger_element_id",
            "from_name",
            "to_name",
            "trigger_action",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
