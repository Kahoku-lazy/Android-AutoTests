from rest_framework import serializers

from .models import LIBRARY_KIND_CHOICES, CaseProject


class CaseProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseProject
        fields = [
            "id",
            "name",
            "description",
            "library_kind",
            "created_by",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"library_kind": {"choices": LIBRARY_KIND_CHOICES}}
