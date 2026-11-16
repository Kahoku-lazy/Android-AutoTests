"""账号写口：停用与改密的落库语义（运营后台经 `accounts.api` 调用）。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.accounts import api

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def user(db):
    """被操作的普通账号。"""
    return get_user_model().objects.create_user(username="target", password="pass-123456")


def test_set_user_active_disables_and_restores(user):
    """停用置假、启用置真，都落库。"""
    assert api.set_user_active(user.id, False).is_active is False
    user.refresh_from_db()
    assert user.is_active is False

    assert api.set_user_active(user.id, True).is_active is True
    user.refresh_from_db()
    assert user.is_active is True


def test_set_user_active_is_idempotent(user):
    """重复停用不报错，状态保持停用。"""
    api.set_user_active(user.id, False)
    assert api.set_user_active(user.id, False).is_active is False
    user.refresh_from_db()
    assert user.is_active is False


def test_set_user_password_stores_hash_only(user):
    """改密后能校验新密码，且库里没有明文。"""
    api.set_user_password(user.id, "new-secret-123")
    user.refresh_from_db()
    assert user.check_password("new-secret-123") is True
    assert "new-secret-123" not in user.password


def test_set_user_password_rejects_empty(user):
    """空密码拒绝写入。"""
    with pytest.raises(ValueError):
        api.set_user_password(user.id, "")


def test_writers_reject_unknown_user():
    """账号不存在时抛 ValueError，而不是静默成功。"""
    with pytest.raises(ValueError):
        api.set_user_active(999999, False)
    with pytest.raises(ValueError):
        api.set_user_password(999999, "whatever-123")
