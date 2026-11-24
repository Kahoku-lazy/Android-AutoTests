from __future__ import annotations

import pytest

from django.contrib.auth.models import User
from django.test import Client

from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

POST_PATH = "/api/auth/logout/"


@pytest.fixture
def user():
    return User.objects.create_user(username="csrf_probe", password="pw123456")


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def strict_client():
    return Client(enforce_csrf_checks=True)


def _jwt_header(user_id: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user_id)}"}


def test_jwt_request_is_not_csrf_blocked(strict_client, user):
    resp = strict_client.post(POST_PATH, **_jwt_header(str(user.id)))
    assert resp.status_code == 200, resp.content[:200]
    assert resp.json()["status"] is True


def test_unauthenticated_post_rejected_by_jwt_before_csrf(strict_client):
    resp = strict_client.post(POST_PATH)
    assert resp.status_code == 401


def test_invalid_jwt_rejected_without_csrf_403(strict_client):
    resp = strict_client.post(POST_PATH, HTTP_AUTHORIZATION="Bearer not-a-real-token")
    assert resp.status_code == 401


def test_admin_login_without_csrf_token_is_rejected(strict_client):
    resp = strict_client.post("/admin/login/", {"username": "nobody", "password": "bad"})
    assert resp.status_code == 403


def test_admin_login_with_csrf_token_passes_csrf_check(strict_client):
    strict_client.get("/admin/login/")
    token = strict_client.cookies["csrftoken"].value
    resp = strict_client.post(
        "/admin/login/",
        {"username": "nobody", "password": "bad", "csrfmiddlewaretoken": token},
    )
    assert resp.status_code != 403, resp.content[:200]


def test_cors_preflight_not_csrf_blocked(strict_client):
    resp = strict_client.options(
        POST_PATH,
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert resp.status_code != 403
