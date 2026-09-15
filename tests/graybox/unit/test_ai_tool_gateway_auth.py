"""工具网关内部令牌鉴权契约（D1 通道边界）。"""

from __future__ import annotations

import pytest

from django.test import Client, override_settings

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.ai_assistant]

TOKEN = "unit-test-internal-token"
GATEWAY_PATH = "/api/ai/tools/devices/list_all"


@pytest.fixture
def client():
    return Client()


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_missing_token_rejected(client):
    resp = client.post(GATEWAY_PATH, data="{}", content_type="application/json")
    assert resp.status_code == 401
    assert resp.json()["status"] is False


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_wrong_token_rejected(client):
    resp = client.post(
        GATEWAY_PATH,
        data="{}",
        content_type="application/json",
        HTTP_X_INTERNAL_TOKEN="wrong-token",
    )
    assert resp.status_code == 401


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_correct_token_allowed(client):
    resp = client.post(
        GATEWAY_PATH,
        data="{}",
        content_type="application/json",
        HTTP_X_INTERNAL_TOKEN=TOKEN,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True


@override_settings(AI_TOOL_GATEWAY_TOKEN="")
def test_unconfigured_token_fails_closed(client):
    resp = client.post(
        GATEWAY_PATH,
        data="{}",
        content_type="application/json",
        HTTP_X_INTERNAL_TOKEN=TOKEN,
    )
    assert resp.status_code == 401


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_business_endpoint_still_requires_jwt(client):
    assert client.get("/api/devices/").status_code == 401


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_public_doc_endpoints_stay_public(client):
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/schema/").status_code == 200


@override_settings(AI_TOOL_GATEWAY_TOKEN=TOKEN)
def test_cors_preflight_not_blocked(client):
    resp = client.options(
        GATEWAY_PATH,
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert resp.status_code != 401
