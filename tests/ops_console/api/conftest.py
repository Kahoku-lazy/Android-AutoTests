from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.shared.users import OPERATOR_GROUP


@pytest.fixture
def operator_group(db) -> Group:
    return Group.objects.get_or_create(name=OPERATOR_GROUP)[0]


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(username="normal", password="pass-123456")


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(username="other", password="pass-123456")


@pytest.fixture
def operator_user(db, operator_group):
    user = get_user_model().objects.create_user(username="ops", password="pass-123456")
    user.groups.add(operator_group)
    return user


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass-123456", is_superuser=True, is_staff=True
    )
