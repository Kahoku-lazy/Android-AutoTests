"""运营后台：停用 / 启用的幂等与四条边界。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ops_console.views import OpsUserDisableView, OpsUserEnableView
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def test_disable_normal_user(operator_user, other_user):
    """运营停用普通用户：状态落库，响应回带最新状态。"""
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    assert response.data["user"]["is_active"] is False
    other_user.refresh_from_db()
    assert other_user.is_active is False


def test_disable_is_idempotent(operator_user, other_user):
    """重复停用不报错，状态保持停用。"""
    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    other_user.refresh_from_db()
    assert other_user.is_active is False


def test_enable_restores_user(operator_user, other_user):
    """启用把停用账号恢复回来。"""
    other_user.is_active = False
    other_user.save(update_fields=["is_active"])

    response = call(OpsUserEnableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    assert response.data["user"]["is_active"] is True
    other_user.refresh_from_db()
    assert other_user.is_active is True


def test_operator_cannot_disable_superuser(operator_user, admin_user):
    """运营停用超管：403，目标状态不变。"""
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=admin_user.id)
    assert response.status_code == 403
    admin_user.refresh_from_db()
    assert admin_user.is_active is True


def test_operator_cannot_disable_other_operator(operator_user, operator_group):
    """运营停用另一个运营：403，目标状态不变。"""
    peer = get_user_model().objects.create_user(username="peer", password="pass-123456")
    peer.groups.add(operator_group)

    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=peer.id)
    assert response.status_code == 403
    peer.refresh_from_db()
    assert peer.is_active is True


def test_operator_cannot_disable_self(operator_user):
    """运营停用自己：403，自己仍可登录。"""
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=operator_user.id)
    assert response.status_code == 403
    operator_user.refresh_from_db()
    assert operator_user.is_active is True


def test_disable_unknown_target_returns_404(operator_user):
    """目标不存在：404。"""
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=999999)
    assert response.status_code == 404


def test_superuser_can_disable_operator(admin_user, operator_group):
    """超管可以管理运营账号（运营不行的那条约束不约束超管）。"""
    peer = get_user_model().objects.create_user(username="peer2", password="pass-123456")
    peer.groups.add(operator_group)

    response = call(OpsUserDisableView, method="post", user=admin_user, user_id=peer.id)
    assert response.status_code == 200
    peer.refresh_from_db()
    assert peer.is_active is False


def test_disabled_user_cannot_login(operator_user, other_user):
    """停用即时阻断登录：原密码在 authenticate 上已经过不去（登录接口因此返回 401）。"""
    from django.contrib.auth import authenticate

    assert authenticate(username="other", password="pass-123456") is not None

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)

    assert authenticate(username="other", password="pass-123456") is None


def test_enabled_again_can_login(operator_user, other_user):
    """恢复启用后原密码重新可用。"""
    from django.contrib.auth import authenticate

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    call(OpsUserEnableView, method="post", user=operator_user, user_id=other_user.id)

    assert authenticate(username="other", password="pass-123456") is not None
