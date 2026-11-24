from rest_framework import serializers

from backend.apps.bug_manager.models import BugTicket


class BugListQuerySerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[choice[0] for choice in BugTicket.CATEGORY_CHOICES],
        required=False,
        allow_blank=True,
    )
    status = serializers.ChoiceField(
        choices=[choice[0] for choice in BugTicket.STATUS_CHOICES],
        required=False,
        allow_blank=True,
    )
    keyword = serializers.CharField(required=False, allow_blank=True, default="")


class BugStatusInputSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[choice[0] for choice in BugTicket.STATUS_CHOICES])
