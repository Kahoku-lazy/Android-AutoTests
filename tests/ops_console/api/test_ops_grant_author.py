"""
模块功能：➡️ 助手作者授予接口：超管可授，作者不能转授，自己不能授给自己 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ops_console/api/test_ops_grant_author.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant、backend/apps/ops_console
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author, has_assistant_author_grant
from backend.apps.ops_console.views import OpsUserGrantAuthorView, OpsUserRevokeAuthorView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _user(name: str, *, superuser: bool = False):
    return get_user_model().objects.create_user(
        username=name,
        password="pass",
        is_superuser=superuser,
    )


def _call(actor, target_id: int, *, revoke: bool = False):
    factory = APIRequestFactory()
    path = f"/api/ops/users/{target_id}/{'revoke' if revoke else 'grant'}-author/"
    request = factory.post(path, {}, format="json")
    request.user_id = str(actor.id)
    force_authenticate(request, user=actor)
    view = OpsUserRevokeAuthorView.as_view() if revoke else OpsUserGrantAuthorView.as_view()
    return view(request, user_id=target_id)


def test_routes_resolve():
    assert resolve("/api/ops/users/3/grant-author/").func.cls is OpsUserGrantAuthorView
    assert resolve("/api/ops/users/3/revoke-author/").func.cls is OpsUserRevokeAuthorView


def test_superuser_can_grant_and_revoke():
    root = _user("author-root", superuser=True)
    target = _user("author-target")

    granted = _call(root, target.id)
    assert granted.status_code == 200
    assert has_assistant_author_grant(target.id) is True

    revoked = _call(root, target.id, revoke=True)
    assert revoked.status_code == 200
    assert has_assistant_author_grant(target.id) is False


def test_author_cannot_transfer_or_grant_self():
    root = _user("author-root-2", superuser=True)
    author = _user("author-holder")
    other = _user("author-other")
    grant_assistant_author(author.id)

    transferred = _call(author, other.id)
    self_grant = _call(author, author.id)

    assert transferred.status_code == 403
    assert self_grant.status_code == 403
    assert has_assistant_author_grant(other.id) is False
    assert has_assistant_author_grant(author.id) is True
    assert root.id != author.id
