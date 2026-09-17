"""尾斜杠双向容错契约（OpenSpec: normalize-trailing-slash-both-ways）。

该中间件此前零覆盖。集成用例需要一个真实令牌：受保护路径在未鉴权时会被 JWT 中间件
**先于路由解析**拦成 401，那样无法区分"命中"与"未解析"。
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import Resolver404

from gateway import normalize_slash as ns

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

PASSWORD = "pw123456"


@pytest.fixture
def authed():
    """带真实访问令牌的客户端 + 请求头。"""
    User.objects.create_user(username="slash_probe", password=PASSWORD)
    c = Client()
    r = c.post(
        "/api/auth/login",
        data=json.dumps({"username": "slash_probe", "password": PASSWORD}),
        content_type="application/json",
    )
    return c, {"HTTP_AUTHORIZATION": "Bearer " + r.json()["data"]["access_token"]}


def test_slash_request_hits_slashless_route(authed):
    """Scenario: 带斜杠调用无斜杠路由 —— 此前是 404。"""
    c, h = authed
    assert c.get("/api/auth/me", **h).status_code == 200
    assert c.get("/api/auth/me/", **h).status_code == 200, "带斜杠请求未命中无斜杠路由"

    # 公开端点同样：400（空请求体）而不是 404
    assert c.post("/api/auth/login/").status_code == 400


def test_slashless_request_hits_slash_route(authed):
    """Scenario: 无斜杠调用带斜杠路由 —— 原有的补斜杠行为不得回归。"""
    c, h = authed
    assert c.get("/api/dashboard/stats/", **h).status_code == 200
    assert c.get("/api/dashboard/stats", **h).status_code == 200


def test_nonexistent_path_stays_404(authed):
    """Scenario: 两种形式都不存在时保持 404。"""
    c, h = authed
    assert c.get("/api/no-such-route", **h).status_code == 404
    assert c.get("/api/no-such-route/", **h).status_code == 404


class _StubResolver:
    """只认给定的 path 集合，用于精确断言"是否发生改写"。"""

    def __init__(self, known):
        self.known = set(known)

    def resolve(self, path):
        if path in self.known:
            return object()
        raise Resolver404(path)


def _run(middleware_input, known):
    """跑一遍中间件，返回它交给下游的 path_info。"""
    seen = {}

    def get_response(request):
        seen["path_info"] = request.path_info
        return "ok"

    import gateway.normalize_slash as mod

    original = mod.get_resolver
    mod.get_resolver = lambda: _StubResolver(known)
    try:
        ns.NormalizeTrailingSlashMiddleware(get_response)(RequestFactory().get(middleware_input))
    finally:
        mod.get_resolver = original
    return seen["path_info"]


def test_no_rewrite_when_original_path_resolves():
    """Scenario: 原路径可解析时不改写（x 与 x/ 并存的资源语义必须保持）。"""
    assert _run("/api/both", {"/api/both", "/api/both/"}) == "/api/both"
    assert _run("/api/both/", {"/api/both", "/api/both/"}) == "/api/both/"


def test_no_rewrite_when_neither_form_resolves():
    """Scenario: 两种形式都不存在时不改写，保持 404。"""
    assert _run("/api/nope", set()) == "/api/nope"
    assert _run("/api/nope/", set()) == "/api/nope/"


def test_non_api_prefix_untouched():
    """Scenario: 非 /api 前缀不受影响。"""
    assert _run("/admin/", {"/admin"}) == "/admin/"
    assert _run("/static/x.js", {"/static/x.js/"}) == "/static/x.js"
