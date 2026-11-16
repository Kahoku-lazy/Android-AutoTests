"""运营后台的出参 DTO（账号行）。

业务：
1. OpsUserRowSerializer: 把账号实例转成一行，身份统一成 superuser / operator / user。
"""

from rest_framework import serializers


def _fmt(value) -> str:
    """把时间格式化成 `YYYY-MM-DD HH:MM`；空值返回空串。

    Args:
        value: datetime 或 None。

    Returns:
        格式化后的字符串。
    """
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


class OpsUserRowSerializer(serializers.Serializer):
    """一行账号：身份标签、启用状态与时间都在这里定形。

    Attributes:
        context["operator_ids"]: 运营账号主键集合。列表场景一次性查好后传入，
            避免每行再查一次组关系。
    """

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    identity = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    def get_identity(self, obj) -> str:
        """返回身份标签：superuser / operator / user。

        Args:
            obj: 账号实例。

        Returns:
            身份标签字符串。
        """
        if obj.is_superuser:
            return "superuser"
        operator_ids = (self.context or {}).get("operator_ids") or set()
        return "operator" if obj.id in operator_ids else "user"

    def get_date_joined(self, obj) -> str:
        """注册时间（精确到分钟）。

        Args:
            obj: 账号实例。

        Returns:
            形如 `2026-11-15 21:30` 的字符串。
        """
        return _fmt(obj.date_joined)

    def get_last_login(self, obj) -> str:
        """最后登录时间；从未登录返回空串。

        Args:
            obj: 账号实例。

        Returns:
            形如 `2026-11-15 21:30` 的字符串或空串。
        """
        return _fmt(obj.last_login)
