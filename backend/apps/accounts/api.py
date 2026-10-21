"""accounts 写操作 — 用户创建收敛到本文件。

写操作铁律：View 调用 api.py 函数写 DB，禁止直接 ORM INSERT/UPDATE/DELETE。

唯一性权威：用户名的唯一性以**数据库唯一约束**为准。本文件负责把 `IntegrityError`
翻译为领域错误 :class:`ConflictError`（视图映射为 409）；输入校验层不做唯一性保证。

__all__ 白名单，供 views.py 调用。
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
