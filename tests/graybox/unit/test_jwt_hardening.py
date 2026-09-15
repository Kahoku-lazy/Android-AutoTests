"""D1 鉴权硬化契约：缺 sub 的合法令牌必须 401（不是 500）；WWW-Authenticate realm 不得含密钥材料。"""

from __future__ import annotations

import time

import jwt as pyjwt
import pytest

from django.conf import settings
from django.test import Client

from shared.auth.drf_auth import JWTAuthentication
from shared.auth.jwt_auth import get_config, verify_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

# 受 JWT 中间件保护、且非 DRF 的稳定端点（与 test_csrf_protection 同口径）
PROTECTED_PATH = "/api/reports/"


def _signed_token_without_sub() -> str:
    """用真实密钥签一个签名合法但缺 sub 的 access 令牌（模拟异常签发来源）。"""
    cfg = get_config()
    now = int(time.time())
    return pyjwt.encode(
        {"jti": "no-sub", "iat": now, "exp": now + 60, "type": "access"},
        cfg.secret,
        algorithm=cfg.algorithm,
    )


def test_verify_token_rejects_token_without_sub():
    """verify_token 是不变量唯一落点：缺 sub 直接判无效。"""
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(_signed_token_without_sub(), expected_type="access")


def test_middleware_returns_401_not_500_for_token_without_sub():
    """修复前：中间件直接 payload["sub"] → KeyError → 500。"""
    resp = Client().get(PROTECTED_PATH, HTTP_AUTHORIZATION=f"Bearer {_signed_token_without_sub()}")
    assert resp.status_code == 401, resp.content[:200]


def test_authenticate_header_does_not_leak_secret():
    """realm 是协议标识，禁止携带密钥前缀（可被任意客户端/日志收集）。"""
    header = JWTAuthentication().authenticate_header(None)
    assert "realm=" in header
    assert settings.SECRET_KEY[:8] not in header
