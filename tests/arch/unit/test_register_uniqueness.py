from __future__ import annotations

import inspect
import json

import pytest

from django.contrib.auth.models import User
from django.db import transaction
from django.test import Client

from backend.apps.accounts import api
from backend.apps.accounts.serializers import RegisterSerializer

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

PASSWORD = "pw123456"


def _register(c, username, **over):
    body = {
        "username": username,
        "password": PASSWORD,
        "password2": PASSWORD,
        "email": f"{username}@test.local",
    }
    body.update(over)
    return c.post("/api/auth/register/", data=json.dumps(body), content_type="application/json")


def test_sequential_duplicate_returns_409():
    c = Client()
    assert _register(c, "dup_seq").status_code == 200

    r = _register(c, "dup_seq")
    assert r.status_code == 409, r.content
    assert r.json()["message"] == "用户名已存在"


def test_duplicate_appearing_at_write_time_returns_409(monkeypatch):
    c = Client()
    original = api.create_user

    def preempted(username, password, email):
        User.objects.create_user(username=username, password="other", email="x@y.z")
        return original(username=username, password=password, email=email)

    monkeypatch.setattr(api, "create_user", preempted)

    r = _register(c, "dup_race")
    assert r.status_code == 409, r.content
    assert r.json()["message"] == "用户名已存在"


def test_write_port_translates_integrity_error():
    api.create_user(username="dup_port", password=PASSWORD, email="a@b.c")

    with pytest.raises(api.ConflictError) as ei:
        api.create_user(username="dup_port", password=PASSWORD, email="a@b.c")

    assert ei.value.__cause__ is not None
    assert ei.value.__cause__.__class__.__name__ == "IntegrityError"


def test_conflict_does_not_break_caller_transaction():
    api.create_user(username="dup_tx", password=PASSWORD, email="a@b.c")

    with transaction.atomic():
        with pytest.raises(api.ConflictError):
            api.create_user(username="dup_tx", password=PASSWORD, email="a@b.c")
        assert User.objects.filter(username="dup_tx").count() == 1
        api.create_user(username="after_tx", password=PASSWORD, email="c@d.e")

    assert User.objects.filter(username="after_tx").exists()


def test_serializer_does_not_guarantee_uniqueness():
    src = inspect.getsource(RegisterSerializer)
    assert "User.objects" not in src, "校验层重新引入了唯一性前置检查（唯一性应由写口保证）"
