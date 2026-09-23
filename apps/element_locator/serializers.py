"""element_locator DRF serializers — PageFlow."""

from rest_framework import serializers

from .models import PageFlow

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
