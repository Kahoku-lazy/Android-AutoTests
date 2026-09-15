"""CSRF 保护与 JWT 豁免契约（D0 安全配置 + D1 通道）。

注意：Django 测试客户端默认 `enforce_csrf_checks=False`（即默认豁免 CSRF），
因此验证「保护是否生效」必须显式用 `Client(enforce_csrf_checks=True)`。
"""

from __future__ import annotations

import pytest

from django.test import Client

from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

POST_PATH = "/api/reports/"  # 该视图非 DRF、未 @csrf_exempt，但会忽略请求方法直接返回 JSON


@pytest.fixture
def client():
    """默认客户端（Django 默认不强制 CSRF 校验）。"""
    return Client()


@pytest.fixture
def strict_client():
    """强制 CSRF 校验的客户端 —— 只有它能证明保护真的生效。"""
    return Client(enforce_csrf_checks=True)


def _jwt_header(user_id: str = "u-csrf-test") -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user_id)}"}


def test_jwt_request_is_not_csrf_blocked(strict_client):
    """强制 CSRF 下，有效 JWT 的 POST 仍必须到达视图（200，非 403）。"""
    resp = strict_client.post(POST_PATH, **_jwt_header())
    assert resp.status_code == 200, resp.content[:200]
    assert resp.json()["status"] is True


def test_unauthenticated_post_rejected_by_jwt_before_csrf(strict_client):
    """无令牌的 POST 由 JWT 中间件先行 401（不会走到 CSRF 检查）。"""
    resp = strict_client.post(POST_PATH)
    assert resp.status_code == 401


def test_invalid_jwt_rejected_without_csrf_403(strict_client):
    """非法令牌同样先被 JWT 中间件拒绝，不产生 403。"""
    resp = strict_client.post(POST_PATH, HTTP_AUTHORIZATION="Bearer not-a-real-token")
    assert resp.status_code == 401


def test_admin_login_without_csrf_token_is_rejected(strict_client):
    """后台是 session 表单面：缺 CSRF token 的登录 POST 必须 403。"""
    resp = strict_client.post("/admin/login/", {"username": "nobody", "password": "bad"})
    assert resp.status_code == 403


def test_admin_login_with_csrf_token_passes_csrf_check(strict_client):
    """带页面下发的 csrfmiddlewaretoken 时通过 CSRF 校验（凭证错误 → 重新渲染登录页）。"""
    strict_client.get("/admin/login/")  # 取得 csrftoken cookie
    token = strict_client.cookies["csrftoken"].value
    resp = strict_client.post(
        "/admin/login/",
        {"username": "nobody", "password": "bad", "csrfmiddlewaretoken": token},
    )
    assert resp.status_code != 403, resp.content[:200]


def test_cors_preflight_not_csrf_blocked(strict_client):
    """CORS 预检（OPTIONS）不应被 CSRF 中间件拦截。"""
    resp = strict_client.options(
        POST_PATH,
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert resp.status_code != 403
