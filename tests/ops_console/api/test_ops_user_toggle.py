from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ops_console.views import OpsUserDisableView, OpsUserEnableView
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def test_disable_normal_user(operator_user, other_user):
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    assert response.data["user"]["is_active"] is False
    other_user.refresh_from_db()
    assert other_user.is_active is False


def test_disable_is_idempotent(operator_user, other_user):
    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    other_user.refresh_from_db()
    assert other_user.is_active is False


def test_enable_restores_user(operator_user, other_user):
    other_user.is_active = False
    other_user.save(update_fields=["is_active"])

    response = call(OpsUserEnableView, method="post", user=operator_user, user_id=other_user.id)
    assert response.status_code == 200
    assert response.data["user"]["is_active"] is True
    other_user.refresh_from_db()
    assert other_user.is_active is True


def test_operator_cannot_disable_superuser(operator_user, admin_user):
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=admin_user.id)
    assert response.status_code == 403
    admin_user.refresh_from_db()
    assert admin_user.is_active is True


def test_operator_cannot_disable_other_operator(operator_user, operator_group):
    peer = get_user_model().objects.create_user(username="peer", password="pass-123456")
    peer.groups.add(operator_group)

    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=peer.id)
    assert response.status_code == 403
    peer.refresh_from_db()
    assert peer.is_active is True


def test_operator_cannot_disable_self(operator_user):
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=operator_user.id)
    assert response.status_code == 403
    operator_user.refresh_from_db()
    assert operator_user.is_active is True


def test_disable_unknown_target_returns_404(operator_user):
    response = call(OpsUserDisableView, method="post", user=operator_user, user_id=999999)
    assert response.status_code == 404


def test_superuser_cannot_disable_operator(admin_user, operator_group):
    peer = get_user_model().objects.create_user(username="peer2", password="pass-123456")
    peer.groups.add(operator_group)

    response = call(OpsUserDisableView, method="post", user=admin_user, user_id=peer.id)
    assert response.status_code == 403
    peer.refresh_from_db()
    assert peer.is_active is True


def test_disabled_user_cannot_login(operator_user, other_user):
    from django.contrib.auth import authenticate

    assert authenticate(username="other", password="pass-123456") is not None

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)

    assert authenticate(username="other", password="pass-123456") is None


def test_disable_writes_user_revocation_and_enable_keeps_it(operator_user, other_user):
    from backend.apps.accounts.models import TokenRevocation

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert TokenRevocation.objects.filter(
        kind=TokenRevocation.KIND_USER, ref=str(other_user.id)
    ).exists()

    call(OpsUserEnableView, method="post", user=operator_user, user_id=other_user.id)
    assert TokenRevocation.objects.filter(
        kind=TokenRevocation.KIND_USER, ref=str(other_user.id)
    ).exists()


def test_repeated_disable_keeps_one_revocation_row(operator_user, other_user):
    from backend.apps.accounts.models import TokenRevocation

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    assert (
        TokenRevocation.objects.filter(
            kind=TokenRevocation.KIND_USER, ref=str(other_user.id)
        ).count()
        == 1
    )


def test_enabled_again_can_login(operator_user, other_user):
    from django.contrib.auth import authenticate

    call(OpsUserDisableView, method="post", user=operator_user, user_id=other_user.id)
    call(OpsUserEnableView, method="post", user=operator_user, user_id=other_user.id)

    assert authenticate(username="other", password="pass-123456") is not None
