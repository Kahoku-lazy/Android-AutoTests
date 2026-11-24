"""
模块功能：➡️ 运营后台：重置密码的一次性语义与三条边界 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ops_console/api/test_ops_reset_password.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ops_console
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import authenticate, get_user_model

from backend.apps.ops_console.views import OpsUserListView, OpsUserResetPasswordView
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]

OLD_PASSWORD = "pass-123456"


def test_reset_returns_one_time_password(operator_user, other_user):
    """运营重置普通用户：返回用户名与 16 位一次性密码。"""
    response = call(
        OpsUserResetPasswordView, method="post", user=operator_user, user_id=other_user.id
    )
    assert response.status_code == 200
    assert response.data["username"] == "other"
    assert len(response.data["password"]) == 16


def test_new_password_works_and_old_fails(operator_user, other_user):
    """新密码可登录、旧密码立即失效。"""
    response = call(
        OpsUserResetPasswordView, method="post", user=operator_user, user_id=other_user.id
    )
    new_password = response.data["password"]

    assert authenticate(username="other", password=new_password) is not None
    assert authenticate(username="other", password=OLD_PASSWORD) is None


def test_password_only_returned_once(operator_user, other_user):
    """再次读取列表时不再出现任何密码字段。"""
    call(OpsUserResetPasswordView, method="post", user=operator_user, user_id=other_user.id)

    response = call(OpsUserListView, user=operator_user)
    for row in response.data["users"]:
        assert "password" not in row
        assert "password_hash" not in row


def test_operator_cannot_reset_superuser(operator_user, admin_user):
    """运营重置超管：403，超管密码不变。"""
    response = call(
        OpsUserResetPasswordView, method="post", user=operator_user, user_id=admin_user.id
    )
    assert response.status_code == 403
    admin_user.refresh_from_db()
    assert admin_user.check_password(OLD_PASSWORD) is True


def test_operator_cannot_reset_other_operator(operator_user, operator_group):
    """运营重置另一个运营：403。"""
    peer = get_user_model().objects.create_user(username="peer", password=OLD_PASSWORD)
    peer.groups.add(operator_group)

    response = call(OpsUserResetPasswordView, method="post", user=operator_user, user_id=peer.id)
    assert response.status_code == 403
    peer.refresh_from_db()
    assert peer.check_password(OLD_PASSWORD) is True


def test_operator_cannot_reset_self(operator_user):
    """运营重置自己：403（避免把密码改到自己不知道）。"""
    response = call(
        OpsUserResetPasswordView, method="post", user=operator_user, user_id=operator_user.id
    )
    assert response.status_code == 403
    operator_user.refresh_from_db()
    assert operator_user.check_password(OLD_PASSWORD) is True


def test_reset_unknown_target_returns_404(operator_user):
    """目标不存在：404。"""
    response = call(OpsUserResetPasswordView, method="post", user=operator_user, user_id=999999)
    assert response.status_code == 404
