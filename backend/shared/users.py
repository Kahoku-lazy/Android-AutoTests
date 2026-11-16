"""通用用户工具 — 跨 App 可 import 的共享能力（shared 层）。"""

import logging

logger = logging.getLogger(__name__)


def resolve_username(user_id):
    """Convert Django user ID to username string. Already-usernames pass through."""
    if not user_id:
        return ""
    s = str(user_id)
    if not s.isdigit():
        return s
    try:
        from django.contrib.auth.models import User

        return User.objects.get(id=int(s)).username
    except Exception:
        return s


def is_superuser(user_id) -> bool:
    """按 ``user_id`` 判定是否为超级管理员（跨 App 唯一实现）。

    Args:
        user_id: 用户主键；空值、非数字或查无此人都算 False。

    Returns:
        是否为超级管理员。
    """
    if not user_id:
        return False
    try:
        from django.contrib.auth import get_user_model

        return get_user_model().objects.filter(pk=int(str(user_id)), is_superuser=True).exists()
    except (ValueError, TypeError):
        return False


# 运营身份的用户组名。真相源：openspec/changes/add-ops-user-console；
# 授予方式由超级管理员在 Django Admin 的组成员里维护。
OPERATOR_GROUP = "运营"


def is_operator(user_id) -> bool:
    """按 ``user_id`` 判定是否为运营（超级管理员天然算运营）。

    运营身份用内置用户组表示，不新增用户表：属于 ``OPERATOR_GROUP`` 或
    ``is_superuser`` 为真即视为运营。

    Args:
        user_id: 用户主键；空值、非数字或查无此人都算 False。

    Returns:
        是否为运营。
    """
    if not user_id:
        return False
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Q

        return (
            get_user_model()
            .objects.filter(pk=int(str(user_id)))
            .filter(Q(is_superuser=True) | Q(groups__name=OPERATOR_GROUP))
            .exists()
        )
    except (ValueError, TypeError):
        return False
