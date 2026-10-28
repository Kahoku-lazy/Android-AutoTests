"""
注册时创建用户。

业务：
1. 创建平台用户，并返回账号编号、用户名和邮箱。
2. 用户名已存在时拒绝创建。
"""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

__all__ = ["ConflictError", "create_user"]


class ConflictError(Exception):
    """写入与既有数据冲突（当前唯一来源：用户名已存在）。"""


def create_user(username: str, password: str, email: str) -> dict:
    """创建平台用户。

    Raises:
        ConflictError: 用户名已存在（由数据库唯一约束判定）。

    Returns:
        dict: {"id": int, "username": str, "email": str}
    """
    try:
        # savepoint：IntegrityError 之后外层事务仍可用，否则调用方（含用例事务）
        # 的后续查询会抛 TransactionManagementError
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, email=email)
    except IntegrityError as exc:
        raise ConflictError("用户名已存在") from exc
    return {"id": user.id, "username": user.username, "email": user.email}
