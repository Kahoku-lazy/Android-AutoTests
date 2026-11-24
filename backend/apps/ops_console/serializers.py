from rest_framework import serializers


def _fmt(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


class OpsUserRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    identity = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    def get_identity(self, obj) -> str:
        if obj.is_superuser:
            return "superuser"
        operator_ids = (self.context or {}).get("operator_ids") or set()
        return "operator" if obj.id in operator_ids else "user"

    def get_date_joined(self, obj) -> str:
        return _fmt(obj.date_joined)

    def get_last_login(self, obj) -> str:
        return _fmt(obj.last_login)
