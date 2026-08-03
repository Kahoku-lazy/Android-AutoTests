"""tests/ 共享 fixtures 和 helper。

为 auth 相关测试提供：
- Django USER_MODEL fixture（带 @pytest.mark.django_db）
- 测试用户 fixture
- 通用的 login helper
"""

import pytest


@pytest.fixture
def test_user(db):
    """创建一个测试用户，返回 User 实例。"""
    from django.contrib.auth.models import User
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户（用于跨用户权限隔离测试）。"""
    from django.contrib.auth.models import User
    return User.objects.create_user(username="testuser2", password="testpass456")


@pytest.fixture
def auth_headers(test_user):
    """返回一个带合法 JWT token 的 Authorization header dict。"""
    from shared.auth.jwt_auth import create_access_token
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(test_user2):
    """返回用户 2 的 Authorization header dict。"""
    from shared.auth.jwt_auth import create_access_token
    token = create_access_token(str(test_user2.id))
    return {"Authorization": f"Bearer {token}"}
