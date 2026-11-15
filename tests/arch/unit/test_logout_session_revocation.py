"""登出 = 退出本次登录 —— 会话级吊销契约（OpenSpec: db-backed-token-revocation）。

逐条对应该变更 specs/auth-session/spec.md 的 Scenario。
吊销记录持久化在数据库（测试库为 SQLite 内存库），不再依赖 Redis；
记录带失效时刻，用例之间用不同 sid 相互隔离。
"""

from __future__ import annotations

import json

from datetime import timedelta

import jwt as pyjwt
import pytest

from django.contrib.auth.models import User
from django.db import OperationalError
from django.test import Client
from django.utils import timezone

from backend.apps.accounts import api
from backend.apps.accounts.models import TokenRevocation
from backend.shared.auth import jwt_auth
from backend.shared.auth.jwt_auth import (
    create_access_token,
    create_token_pair,
    session_id_of,
    verify_token,
)

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

PASSWORD = "pw123456"


def _post(c, path, payload=None, **kw):
    body = json.dumps(payload) if payload is not None else None
    return c.post(path, data=body, content_type="application/json", **kw)


@pytest.fixture
def user():
    return User.objects.create_user(username="logout_probe", password=PASSWORD)


def _login(c, username="logout_probe"):
    r = _post(c, "/api/auth/login/", {"username": username, "password": PASSWORD})
    assert r.status_code == 200, r.content
    return r.json()["data"]


def _auth(token):
    return {"HTTP_AUTHORIZATION": "Bearer " + token}


def test_session_ids_are_shared_by_the_pair(user):
    """不变量：一次登录签发的 access 与 refresh 属于同一个会话。"""
    tokens = create_token_pair(str(user.id))
    assert session_id_of(tokens["access_token"]) == session_id_of(tokens["refresh_token"]) != ""


def test_logout_kills_refresh_token(user):
    """Scenario: 登出后刷新令牌失效。"""
    c = Client()
    tokens = _login(c)

    assert _post(c, "/api/auth/logout/", None, **_auth(tokens["access_token"])).status_code == 200

    r = _post(c, "/api/auth/refresh/", {"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401, r.content


def test_logout_kills_access_token(user):
    """Scenario: 登出后原 access 失效。"""
    c = Client()
    tokens = _login(c)

    _post(c, "/api/auth/logout/", None, **_auth(tokens["access_token"]))

    assert c.get("/api/auth/me/", **_auth(tokens["access_token"])).status_code == 401


def test_refresh_keeps_session_ownership(user):
    """Scenario: 续期保持会话归属 —— 续期后的新 access 不能脱离会话管辖。"""
    c = Client()
    tokens = _login(c)

    r = _post(c, "/api/auth/refresh/", {"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.content
    new_access = r.json()["data"]["access_token"]

    # 续期前后属同一会话
    assert session_id_of(new_access) == session_id_of(tokens["access_token"])
    assert c.get("/api/auth/me/", **_auth(new_access)).status_code == 200

    # 用续期后的 access 登出，则该会话的原 refresh 也应失效
    _post(c, "/api/auth/logout/", None, **_auth(new_access))
    assert c.get("/api/auth/me/", **_auth(new_access)).status_code == 401
    assert (
        _post(c, "/api/auth/refresh/", {"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )


def test_other_session_is_unaffected(user):
    """Scenario: 其他会话不受影响。"""
    a, b = Client(), Client()
    ta, tb = _login(a), _login(b)
    assert session_id_of(ta["access_token"]) != session_id_of(tb["access_token"])

    _post(a, "/api/auth/logout/", None, **_auth(ta["access_token"]))

    assert a.get("/api/auth/me/", **_auth(ta["access_token"])).status_code == 401
    assert b.get("/api/auth/me/", **_auth(tb["access_token"])).status_code == 200
    assert _post(b, "/api/auth/refresh/", {"refresh_token": tb["refresh_token"]}).status_code == 200


def test_logout_fails_closed_when_store_unavailable(user, monkeypatch):
    """Scenario: 吊销存储不可用时拒绝登出（503 + retry），不假装成功。"""

    def _broken(*_args, **_kwargs):
        raise OperationalError("revocation store unavailable")

    c = Client()
    tokens = _login(c)

    monkeypatch.setattr(api, "revoke_session", _broken)
    r = _post(c, "/api/auth/logout/", None, **_auth(tokens["access_token"]))

    assert r.status_code == 503, r.content
    assert r.json()["retry"] is True
    assert r.json()["message"] == "吊销服务不可用，请稍后重试"

    # 未成功吊销 —— 会话仍然可用（fail-closed 的语义是「拒绝」而不是「假装成功」）
    monkeypatch.undo()
    assert c.get("/api/auth/me/", **_auth(tokens["access_token"])).status_code == 200


def test_legacy_token_without_sid_still_logs_out(user):
    """Scenario: 缺少会话标识的旧令牌 —— 校验端不报错，登出仍按 jti 吊销。"""
    legacy = create_access_token(str(user.id))  # 不带 sid
    assert session_id_of(legacy) == ""
    assert verify_token(legacy, expected_type="access")["sub"] == str(user.id)

    c = Client()
    assert _post(c, "/api/auth/logout/", None, **_auth(legacy)).status_code == 200
    assert c.get("/api/auth/me/", **_auth(legacy)).status_code == 401


def test_verify_token_rejects_revoked_session(user):
    """单元层：sid 被吊销后，同会话的 refresh 令牌在校验层即被拒。"""
    tokens = create_token_pair(str(user.id))
    sid = session_id_of(tokens["refresh_token"])
    jwt_auth.revoke_session(sid)

    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(tokens["refresh_token"], expected_type="refresh")
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(tokens["access_token"], expected_type="access")


def test_revocation_ttl_covers_refresh_lifetime(user, monkeypatch):
    """不变量：会话吊销记录的有效期必须覆盖 refresh 的寿命，否则 refresh 会「复活」。"""
    captured = {}
    monkeypatch.setattr(
        jwt_auth,
        "_revocation_add",
        lambda kind, ref, ttl: captured.update(kind=kind, ref=ref, ttl=ttl),
    )

    jwt_auth.revoke_session("sid-under-test")

    assert captured["kind"] == "session"
    assert captured["ref"] == "sid-under-test"
    assert captured["ttl"] == jwt_auth.get_config().refresh_ttl


def test_revocation_row_is_persisted(user):
    """Scenario: 吊销记录跨服务重启仍然有效 —— 记录落在库里，不在进程内存。"""
    tokens = create_token_pair(str(user.id))
    sid = session_id_of(tokens["access_token"])
    jwt_auth.revoke_session(sid)

    row = TokenRevocation.objects.get(kind=TokenRevocation.KIND_SESSION, ref=sid)
    remaining = (row.expires_at - timezone.now()).total_seconds()
    assert remaining > jwt_auth.get_config().refresh_ttl - 60


def test_expired_revocation_no_longer_blocks(user):
    """Scenario: 吊销记录过期后不再生效。"""
    tokens = create_token_pair(str(user.id))
    sid = session_id_of(tokens["access_token"])
    jwt_auth.revoke_session(sid)

    TokenRevocation.objects.filter(ref=sid).update(expires_at=timezone.now() - timedelta(seconds=1))

    assert verify_token(tokens["access_token"], expected_type="access")["sub"] == str(user.id)


def test_purge_expired_keeps_live_records(user):
    """清理只删过期行，未过期记录的行为不变。"""
    now = timezone.now()
    TokenRevocation.objects.create(
        kind=TokenRevocation.KIND_SESSION,
        ref="expired-sid",
        expires_at=now - timedelta(hours=1),
    )
    TokenRevocation.objects.create(
        kind=TokenRevocation.KIND_SESSION,
        ref="live-sid",
        expires_at=now + timedelta(hours=1),
    )

    assert api.purge_expired() == 1
    assert not TokenRevocation.objects.filter(ref="expired-sid").exists()
    assert TokenRevocation.objects.filter(ref="live-sid").exists()
    assert api.is_revoked(sid="live-sid") is True
    assert api.is_revoked(sid="expired-sid") is False
