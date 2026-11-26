from __future__ import annotations

import json

import pytest

from django.contrib.auth.models import User
from django.test import Client, RequestFactory

from backend.gateway import middleware
from backend.shared import auth as shared_auth
from backend.shared.auth.drf_auth import JWTAuthentication
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

PASSWORD = "pw123456"


@pytest.fixture
def user():
    return User.objects.create_user(username="single_verify_probe", password=PASSWORD)


def _login(c) -> str:
    body = json.dumps({"username": "single_verify_probe", "password": PASSWORD})
    r = c.post("/api/auth/login/", data=body, content_type="application/json")
    assert r.status_code == 200, r.content
    return r.json()["data"]["access_token"]


def _count_calls(monkeypatch) -> dict:
    calls = {"middleware": 0, "drf": 0}
    real = shared_auth.jwt_auth.verify_token

    def _middleware_verify(token, expected_type=None):
        calls["middleware"] += 1
        return real(token, expected_type=expected_type)

    def _drf_verify(token, expected_type=None):
        calls["drf"] += 1
        return real(token, expected_type=expected_type)

    monkeypatch.setattr(middleware, "verify_token", _middleware_verify)
    monkeypatch.setattr(shared_auth.drf_auth, "verify_token", _drf_verify)
    return calls


def test_drf_request_verifies_token_only_once(user, monkeypatch):
    c = Client()
    token = _login(c)
    calls = _count_calls(monkeypatch)

    r = c.get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer " + token)

    assert r.status_code == 200, r.content
    assert calls["middleware"] == 1
    assert calls["drf"] == 0


def test_drf_auth_still_works_without_middleware(user, monkeypatch):
    token = create_access_token(str(user.id))
    request = RequestFactory().get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer " + token)
    assert not getattr(request, "user_id", "")

    authenticated, _ = JWTAuthentication().authenticate(request)

    assert authenticated.id == user.id


def test_deleted_user_still_rejected(user):
    c = Client()
    token = _login(c)
    assert c.get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer " + token).status_code == 200

    User.objects.filter(username="single_verify_probe").delete()

    assert c.get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer " + token).status_code == 401
