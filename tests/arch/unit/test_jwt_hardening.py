from __future__ import annotations

import time

import jwt as pyjwt
import pytest

from django.conf import settings
from django.test import Client

from backend.shared.auth.drf_auth import JWTAuthentication
from backend.shared.auth.jwt_auth import get_config, verify_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

PROTECTED_PATH = "/api/reports/"


def _signed_token_without_sub() -> str:
    cfg = get_config()
    now = int(time.time())
    return pyjwt.encode(
        {"jti": "no-sub", "iat": now, "exp": now + 60, "type": "access"},
        cfg.secret,
        algorithm=cfg.algorithm,
    )


def test_verify_token_rejects_token_without_sub():
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(_signed_token_without_sub(), expected_type="access")


def test_middleware_returns_401_not_500_for_token_without_sub():
    resp = Client().get(PROTECTED_PATH, HTTP_AUTHORIZATION=f"Bearer {_signed_token_without_sub()}")
    assert resp.status_code == 401, resp.content[:200]


def test_authenticate_header_does_not_leak_secret():
    header = JWTAuthentication().authenticate_header(None)
    assert "realm=" in header
    assert settings.SECRET_KEY[:8] not in header
