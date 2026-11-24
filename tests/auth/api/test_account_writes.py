from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.accounts import api

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="target", password="pass-123456")


def test_set_user_active_disables_and_restores(user):
    assert api.set_user_active(user.id, False).is_active is False
    user.refresh_from_db()
    assert user.is_active is False

    assert api.set_user_active(user.id, True).is_active is True
    user.refresh_from_db()
    assert user.is_active is True


def test_set_user_active_is_idempotent(user):
    api.set_user_active(user.id, False)
    assert api.set_user_active(user.id, False).is_active is False
    user.refresh_from_db()
    assert user.is_active is False


def test_set_user_password_stores_hash_only(user):
    api.set_user_password(user.id, "new-secret-123")
    user.refresh_from_db()
    assert user.check_password("new-secret-123") is True
    assert "new-secret-123" not in user.password


def test_set_user_password_rejects_empty(user):
    with pytest.raises(ValueError):
        api.set_user_password(user.id, "")


def test_set_operator_grants_and_revokes(user):
    from backend.shared.users import OPERATOR_GROUP

    granted = api.set_operator(user.id, True)
    assert granted.groups.filter(name=OPERATOR_GROUP).exists()

    revoked = api.set_operator(user.id, False)
    assert not revoked.groups.filter(name=OPERATOR_GROUP).exists()


def test_set_operator_is_idempotent(user):
    from backend.shared.users import OPERATOR_GROUP

    api.set_operator(user.id, True)
    api.set_operator(user.id, True)
    assert user.groups.filter(name=OPERATOR_GROUP).count() == 1

    api.set_operator(user.id, False)
    assert api.set_operator(user.id, False).groups.filter(name=OPERATOR_GROUP).count() == 0


def test_set_operator_creates_group_when_missing(user):
    from django.contrib.auth.models import Group

    from backend.shared.users import OPERATOR_GROUP

    Group.objects.filter(name=OPERATOR_GROUP).delete()
    api.set_operator(user.id, True)
    assert Group.objects.filter(name=OPERATOR_GROUP).exists()


def test_set_operator_rejects_unknown_user():
    with pytest.raises(ValueError):
        api.set_operator(999999, True)


def test_writers_reject_unknown_user():
    with pytest.raises(ValueError):
        api.set_user_active(999999, False)
    with pytest.raises(ValueError):
        api.set_user_password(999999, "whatever-123")
