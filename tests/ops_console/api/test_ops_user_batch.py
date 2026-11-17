"""运营后台：本页批量停用与仅超管批量注销。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.case_manager.models import CaseProject
from backend.apps.ops_console.views import OpsUserBatchDisableView, OpsUserPurgeView
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def test_batch_disable_normal_users(operator_user, other_user):
    """运营批量停用普通用户：逐行成功。"""
    peer = get_user_model().objects.create_user(username="peer-normal", password="pass-123456")
    response = call(
        OpsUserBatchDisableView,
        method="post",
        user=operator_user,
        path="/api/ops/users/disable/",
        data={"user_ids": [other_user.id, peer.id]},
    )
    assert response.status_code == 200
    assert response.data["counts"]["disabled"] == 2
    other_user.refresh_from_db()
    peer.refresh_from_db()
    assert other_user.is_active is False
    assert peer.is_active is False


def test_batch_disable_skips_already_disabled(operator_user, other_user):
    """已停用记为跳过，其余可管理的行仍被停用。"""
    other_user.is_active = False
    other_user.save(update_fields=["is_active"])
    peer = get_user_model().objects.create_user(username="still-on", password="pass-123456")

    response = call(
        OpsUserBatchDisableView,
        method="post",
        user=operator_user,
        path="/api/ops/users/disable/",
        data={"user_ids": [other_user.id, peer.id]},
    )
    assert response.status_code == 200
    outcomes = {row["user_id"]: row["outcome"] for row in response.data["results"]}
    assert outcomes[other_user.id] == "skipped"
    assert outcomes[peer.id] == "disabled"


def test_batch_disable_rejects_unmanageable_without_aborting(operator_user, admin_user, operator_group):
    """自己、超管、其他运营被拒绝，普通用户仍被停用。"""
    peer = get_user_model().objects.create_user(username="peer-ops", password="pass-123456")
    peer.groups.add(operator_group)
    target = get_user_model().objects.create_user(username="target", password="pass-123456")

    response = call(
        OpsUserBatchDisableView,
        method="post",
        user=operator_user,
        path="/api/ops/users/disable/",
        data={"user_ids": [target.id, operator_user.id, admin_user.id, peer.id]},
    )
    assert response.status_code == 200
    outcomes = {row["user_id"]: row["outcome"] for row in response.data["results"]}
    assert outcomes[target.id] == "disabled"
    assert outcomes[operator_user.id] == "rejected"
    assert outcomes[admin_user.id] == "rejected"
    assert outcomes[peer.id] == "rejected"
    admin_user.refresh_from_db()
    peer.refresh_from_db()
    assert admin_user.is_active is True
    assert peer.is_active is True


def test_superuser_cannot_batch_disable_operator(admin_user, operator_user, other_user):
    """超管批量停用时，运营行被拒绝，普通用户仍被停用。"""
    response = call(
        OpsUserBatchDisableView,
        method="post",
        user=admin_user,
        path="/api/ops/users/disable/",
        data={"user_ids": [operator_user.id, other_user.id]},
    )
    assert response.status_code == 200
    outcomes = {row["user_id"]: row["outcome"] for row in response.data["results"]}
    assert outcomes[operator_user.id] == "rejected"
    assert outcomes[other_user.id] == "disabled"
    operator_user.refresh_from_db()
    assert operator_user.is_active is True


def test_batch_disable_rejects_over_limit(operator_user):
    """超过 100 个整批拒绝，不写库。"""
    response = call(
        OpsUserBatchDisableView,
        method="post",
        user=operator_user,
        path="/api/ops/users/disable/",
        data={"user_ids": list(range(1, 102))},
    )
    assert response.status_code == 400


def test_operator_cannot_purge(operator_user, other_user):
    """运营调用注销被拒，目标仍在。"""
    response = call(
        OpsUserPurgeView,
        method="post",
        user=operator_user,
        path="/api/ops/users/purge/",
        data={"user_ids": [other_user.id]},
    )
    assert response.status_code == 403
    assert get_user_model().objects.filter(pk=other_user.id).exists()


def test_purge_deletes_account_but_keeps_business_row(admin_user, other_user):
    """注销只删账号；该用户创建的项目仍在，创建者字段不变。"""
    project = CaseProject.objects.create(name="kept", created_by=str(other_user.id))
    old_id = other_user.id

    response = call(
        OpsUserPurgeView,
        method="post",
        user=admin_user,
        path="/api/ops/users/purge/",
        data={"user_ids": [old_id]},
    )
    assert response.status_code == 200
    assert old_id in response.data["deleted"]
    assert not get_user_model().objects.filter(pk=old_id).exists()
    project.refresh_from_db()
    assert project.created_by == str(old_id)

    reborn = get_user_model().objects.create_user(username="other", password="pass-123456")
    assert reborn.id != old_id


def test_purge_aborts_when_list_contains_operator(admin_user, operator_user, other_user):
    """名单含运营时整批不删。"""
    response = call(
        OpsUserPurgeView,
        method="post",
        user=admin_user,
        path="/api/ops/users/purge/",
        data={"user_ids": [other_user.id, operator_user.id]},
    )
    assert response.status_code == 403
    assert get_user_model().objects.filter(pk=other_user.id).exists()
    assert get_user_model().objects.filter(pk=operator_user.id).exists()


def test_purge_aborts_when_list_contains_superuser(admin_user, other_user):
    """名单含超管时整批不删。"""
    peer = get_user_model().objects.create_superuser(username="root2", password="pass-123456")
    response = call(
        OpsUserPurgeView,
        method="post",
        user=admin_user,
        path="/api/ops/users/purge/",
        data={"user_ids": [other_user.id, peer.id]},
    )
    assert response.status_code == 403
    assert get_user_model().objects.filter(pk=other_user.id).exists()
    assert get_user_model().objects.filter(pk=peer.id).exists()
