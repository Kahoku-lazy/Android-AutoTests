"""accounts 写操作 — 用户创建收敛到本文件。

写操作铁律：View 调用 api.py 函数写 DB，禁止直接 ORM INSERT/UPDATE/DELETE。

__all__ 白名单，供 views.py 调用。
"""

from django.contrib.auth.models import User

__all__ = ["create_user"]


def create_user(username: str, password: str, email: str) -> dict:
    """创建平台用户。

    Returns:
        dict: {"id": int, "username": str, "email": str}
    """
    user = User.objects.create_user(username=username, password=password, email=email)
    return {"id": user.id, "username": user.username, "email": user.email}
