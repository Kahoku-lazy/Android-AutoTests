from __future__ import annotations

import pytest

from django.test import RequestFactory

from backend.apps.ops_console.views import OpsUserListView
from backend.gateway.middleware import JWTAuthenticationMiddleware
from tests.ops_console.api._helpers import call

pytestmark = [pytest.mark.django_db, pytest.mark.api]

ROW_FIELDS = {"id", "username", "email", "identity", "is_active", "date_joined", "last_login"}


def test_middleware_rejects_missing_token():
    request = RequestFactory().get("/api/ops/users/")
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 401


def test_list_forbidden_for_normal_user(normal_user):
    response = call(OpsUserListView, user=normal_user)
    assert response.status_code == 403
    assert "users" not in response.data


def test_list_allowed_for_operator(operator_user, normal_user):
    response = call(OpsUserListView, user=operator_user)
    assert response.status_code == 200
    names = {row["username"] for row in response.data["users"]}
    assert {"ops", "normal"} <= names
    assert response.data["total"] >= 2


def test_list_allowed_for_superuser(admin_user, normal_user):
    response = call(OpsUserListView, user=admin_user)
    assert response.status_code == 200
    assert response.data["total"] >= 2


def test_list_identity_labels(operator_user, admin_user, normal_user):
    response = call(OpsUserListView, user=admin_user)
    labels = {row["username"]: row["identity"] for row in response.data["users"]}
    assert labels["admin"] == "superuser"
    assert labels["ops"] == "operator"
    assert labels["normal"] == "user"


def test_list_row_has_no_sensitive_fields(admin_user, normal_user):
    response = call(OpsUserListView, user=admin_user)
    row = response.data["users"][0]
    assert set(row) == ROW_FIELDS


def test_list_filters_by_keyword_and_status(operator_user, normal_user, other_user):
    other_user.is_active = False
    other_user.save(update_fields=["is_active"])

    response = call(
        OpsUserListView,
        path="/api/ops/users/?keyword=other&active=false",
        user=operator_user,
    )
    assert response.status_code == 200
    assert [row["username"] for row in response.data["users"]] == ["other"]
    assert response.data["users"][0]["is_active"] is False


def test_list_pagination(operator_user, normal_user, other_user):
    response = call(OpsUserListView, path="/api/ops/users/?page=1&page_size=1", user=operator_user)
    assert response.status_code == 200
    assert len(response.data["users"]) == 1
    assert response.data["page"] == 1
    assert response.data["page_size"] == 1
    assert response.data["total"] >= 2
