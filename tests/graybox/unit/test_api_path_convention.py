"""API 路径约定：全部 /api/ 路由以尾斜杠结尾，缺失即 404。

取代原「尾斜杠双向容错」用例 —— 容错中间件已随本变更删除。

两个容易误判的点，都在下面的用例里显式断言：

1. 受保护路径在**未鉴权**时会先被 JWT 中间件拦成 401，走不到路由解析 ——
   所以「缺失尾斜杠 → 404」用已鉴权客户端断言，不能用 401 反推"路径不存在"。
2. PUBLIC_PREFIXES 是**前缀匹配**：/api/auth/login（不带斜杠）能匹配无斜杠形式，
   于是缺失尾斜杠时会落到路由解析得到 404；而 /api/schema/（带斜杠）匹配不到
   /api/schema，所以它缺失尾斜杠时是 401。这是既有行为，与路由是否存在无关。
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import get_resolver

from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _walk(patterns, prefix=""):
    for p in patterns:
        route = prefix + (str(p._route) if hasattr(p, "_route") else str(p.pattern))
        if hasattr(p, "url_patterns"):
            yield from _walk(p.url_patterns, route)
        else:
            yield route, p


@pytest.fixture
def authed():
    user = User.objects.create_user(username="slash-strict", password="x", email="s@x.io")
    return Client(HTTP_AUTHORIZATION="Bearer " + create_access_token(str(user.pk)))


def test_every_api_route_ends_with_slash():
    """路由表内不得存在无尾斜杠的 /api/ 路由。

    DRF router 还会生成 ".json" 格式后缀分支（形如 ^x 加上可选的 format 捕获组），
    那是另一个特性，不计入尾斜杠判定。
    """
    bad = []
    for route, pattern in _walk(get_resolver().url_patterns):
        if not route.startswith("api/"):
            continue
        if hasattr(pattern, "_route"):
            if route and not route.endswith("/"):
                bad.append(route)
        elif "format" not in route and not route.rstrip("$").endswith("/"):
            bad.append(route)
    assert bad == [], f"以下 /api/ 路由缺尾斜杠: {bad}"


def test_public_path_without_slash_returns_404():
    """公开前缀不含尾斜杠 ⇒ 缺失尾斜杠会走到路由解析，得到确定的 404。"""
    assert Client().get("/api/auth/login").status_code == 404


@pytest.mark.parametrize("path", ["/api/auth/me", "/api/schema", "/api/devices/scan"])
def test_authenticated_missing_slash_returns_404(authed, path: str):
    """已鉴权下，任何缺失尾斜杠的路径都必须是 404（不再被重定向或改写）。"""
    assert authed.get(path).status_code == 404


@pytest.mark.parametrize("path", ["/api/schema", "/api/swagger"])
def test_slashed_public_prefix_without_slash_is_401(path: str):
    """公开前缀带尾斜杠 ⇒ 无斜杠形式匹配不到该前缀，被 JWT 中间件先行拦下（401）。

    401 只说明"未获授权"，**不能**用来推断路径是否存在 —— 这正是上面的已鉴权用例存在的理由。
    """
    assert Client().get(path).status_code == 401


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/devices/scan", "/api/auth/me"])
def test_missing_slash_never_redirects(path: str):
    """不得出现 3xx —— 301 会丢 Authorization 头，且可能把 POST 降级为 GET。"""
    resp = Client().post(path, data=json.dumps({}), content_type="application/json")
    assert not (300 <= resp.status_code < 400), f"{path} 出现重定向 {resp.status_code}"


def test_trailing_slash_form_hits_the_view(authed):
    """带尾斜杠是唯一正确写法：空 body 得到 400（已命中视图），而不是 404。"""
    resp = authed.post("/api/auth/login/", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400
    assert authed.get("/api/auth/me/").status_code == 200
