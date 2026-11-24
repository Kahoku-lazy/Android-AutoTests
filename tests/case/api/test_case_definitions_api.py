from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory

from backend.apps.case_manager import views_drf
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.api, pytest.mark.django_db]

User = get_user_model()


def _request(method: str, path: str, user, body=None):
    factory = RequestFactory()
    raw = getattr(factory, method)(
        path,
        data=json.dumps(body or {}),
        content_type="application/json",
    )
    raw.user_id = str(user.id)
    raw.META["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(user.id))}"
    return raw


def test_create_requires_library_kind():
    user = User.objects.create_user(username="sheet-user", password="x")
    request = _request("post", "/api/cases/projects/", user, {"name": "回归"})
    response = views_drf.CaseProjectViewSet.as_view({"post": "create"})(request)
    assert response.status_code == 400


def test_old_directory_route_is_not_registered():
    from backend.apps.case_manager.urls import urlpatterns

    paths = [str(getattr(item, "pattern", "")) for item in urlpatterns]
    assert not any("directories" in path or "files" in path for path in paths)
