"""
模块功能：➡️ 运营后台接口用例的共用夹具：超管、运营与普通用户 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ops_console/api/conftest.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 被 tests/ops_console/api 用例共用（无独立用例）
🏁
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
