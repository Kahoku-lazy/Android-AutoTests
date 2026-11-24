from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ops_console.views import OpsUserGrantOperatorView, OpsUserRevokeOperatorView
from backend.shared.users import is_operator
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def test_superuser_grants_operator(admin_user, other_user):
    response = call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=other_user.id)
    assert response.status_code == 200
    assert response.data["user"]["identity"] == "operator"
    assert is_operator(other_user.id) is True


def test_superuser_revokes_operator(admin_user, operator_user):
    response = call(
        OpsUserRevokeOperatorView, method="post", user=admin_user, user_id=operator_user.id
    )
    assert response.status_code == 200
    assert response.data["user"]["identity"] == "user"
    assert is_operator(operator_user.id) is False


def test_operator_cannot_grant(operator_user, other_user):
    response = call(
        OpsUserGrantOperatorView, method="post", user=operator_user, user_id=other_user.id
    )
    assert response.status_code == 403
    assert is_operator(other_user.id) is False


def test_operator_cannot_revoke_peer(operator_user, operator_group):
    peer = get_user_model().objects.create_user(username="peer", password="pass-123456")
    peer.groups.add(operator_group)

    response = call(OpsUserRevokeOperatorView, method="post", user=operator_user, user_id=peer.id)
    assert response.status_code == 403
    assert is_operator(peer.id) is True


def test_superuser_cannot_grant_self(admin_user):
    response = call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=admin_user.id)
    assert response.status_code == 403


def test_superuser_cannot_grant_another_superuser(admin_user):
    peer = get_user_model().objects.create_user(
        username="root2", password="pass-123456", is_superuser=True, is_staff=True
    )
    response = call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=peer.id)
    assert response.status_code == 403
    peer.refresh_from_db()
    assert peer.groups.count() == 0


def test_grant_is_idempotent(admin_user, other_user):
    call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=other_user.id)
    response = call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=other_user.id)
    assert response.status_code == 200
    assert other_user.groups.count() == 1


def test_revoke_normal_user_is_idempotent(admin_user, other_user):
    response = call(
        OpsUserRevokeOperatorView, method="post", user=admin_user, user_id=other_user.id
    )
    assert response.status_code == 200
    assert response.data["user"]["identity"] == "user"


def test_grant_unknown_target_returns_404(admin_user):
    response = call(OpsUserGrantOperatorView, method="post", user=admin_user, user_id=999999)
    assert response.status_code == 404
