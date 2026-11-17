"""停用账号：旧令牌作废，受保护请求返回专用拒绝，续期失败。"""

from __future__ import annotations

import time

import pytest

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from django.utils import timezone

from backend.apps.accounts.api import set_user_active
from backend.apps.accounts.models import TokenRevocation
from backend.gateway.middleware import ACCOUNT_DISABLED_CODE, JWTAuthenticationMiddleware
from backend.shared.auth.jwt_auth import create_token_pair, verify_token

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def user(db):
    """被停用的普通账号。"""
    return get_user_model().objects.create_user(username="disabled-probe", password="pass-123456")


def _auth(token: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_disable_revokes_previously_issued_access(user):
    """停用前签发的 access 验签失败；启用后新签发的 access 验签成功。"""
    tokens = create_token_pair(str(user.id))
    set_user_active(user.id, False)
    with pytest.raises(Exception):
        verify_token(tokens["access_token"], expected_type="access")

    time.sleep(2)
    set_user_active(user.id, True)
    fresh = create_token_pair(str(user.id))
    assert verify_token(fresh["access_token"], expected_type="access")["sub"] == str(user.id)
    with pytest.raises(Exception):
        verify_token(tokens["access_token"], expected_type="access")


def test_disabled_account_gets_dedicated_rejection(user):
    """停用账号携带尚未过期的访问令牌请求受保护端点，得到专用 403。"""
    tokens = create_token_pair(str(user.id))
    user.is_active = False
    user.save(update_fields=["is_active"])

    request = RequestFactory().get("/api/auth/me/", **_auth(tokens["access_token"]))
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 403
    import json

    body = json.loads(response.content.decode())
    assert body["code"] == ACCOUNT_DISABLED_CODE
    assert body["message"] == "你的账号已被超管停用，10 秒后将退出登录"


def test_expired_token_of_active_user_stays_401(user):
    """启用账号的过期令牌仍是 401，不走停用文案。"""
    import jwt

    from django.conf import settings

    expired = jwt.encode(
        {"sub": str(user.id), "type": "access", "exp": int(time.time()) - 10, "jti": "old"},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    request = RequestFactory().get("/api/auth/me/", **_auth(expired))
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 401


def test_disabled_refresh_is_rejected(user):
    """停用后用停用前的 refresh 续期，返回 401 且没有新 access。"""
    tokens = create_token_pair(str(user.id))
    set_user_active(user.id, False)
    response = Client().post(
        "/api/auth/refresh/",
        data={"refresh_token": tokens["refresh_token"]},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert "access_token" not in response.content.decode()


def test_old_refresh_stays_rejected_after_enable(user):
    """启用后，停用前的 refresh 仍然不能换新 access。"""
    tokens = create_token_pair(str(user.id))
    set_user_active(user.id, False)
    time.sleep(2)
    set_user_active(user.id, True)
    row = TokenRevocation.objects.get(kind=TokenRevocation.KIND_USER, ref=str(user.id))
    assert row.created_at <= timezone.now()

    response = Client().post(
        "/api/auth/refresh/",
        data={"refresh_token": tokens["refresh_token"]},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert "access_token" not in response.content.decode()
