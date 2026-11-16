"""运营后台接口测试的共用夹具。

直调视图而不起 live server：与 `tests/serial_log/api` 同一范式——网关注入的
`user_id` 与 DRF 认证都用请求属性模拟，断言落库仍走真实 `accounts.api`。
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.shared.users import OPERATOR_GROUP


@pytest.fixture
def operator_group(db) -> Group:
    """运营组：与生产同一真相源（`shared.users.OPERATOR_GROUP`）。"""
    return Group.objects.get_or_create(name=OPERATOR_GROUP)[0]


@pytest.fixture
def normal_user(db):
    """普通用户。"""
    return get_user_model().objects.create_user(username="normal", password="pass-123456")


@pytest.fixture
def other_user(db):
    """另一个普通用户（作被操作目标）。"""
    return get_user_model().objects.create_user(username="other", password="pass-123456")


@pytest.fixture
def operator_user(db, operator_group):
    """运营。"""
    user = get_user_model().objects.create_user(username="ops", password="pass-123456")
    user.groups.add(operator_group)
    return user


@pytest.fixture
def admin_user(db):
    """超级管理员（天然算运营）。"""
    return get_user_model().objects.create_user(
        username="admin", password="pass-123456", is_superuser=True, is_staff=True
    )
