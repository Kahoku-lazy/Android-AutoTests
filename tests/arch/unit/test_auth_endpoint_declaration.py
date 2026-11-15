"""认证端点的鉴权姿态不变量：AllowAny 当且仅当 authentication_classes 为空。

为什么需要这条
--------------
认证模块里三种姿态共存：公开端点显式置空 `authentication_classes`，
需要身份的端点继承 `REST_FRAMEWORK` 默认的 `shared.auth.drf_auth.JWTAuthentication`。
“允许任何人”与“不做 DRF 鉴权”必须成对出现 —— 只写一半会造成两种危险：
公开端点误继承鉴权类（鉴权失败在前）、受保护端点被误开放。

视图类经 URL conf 解析取得，不直接 import `apps.accounts.views`：
断言的是实际挂载的视图，而不是源码里定义了却没挂上的类。
规格：`openspec/specs/auth-session`。
"""

from __future__ import annotations

from typing import Any, Iterator

import pytest

from django.urls import get_resolver, resolve
from rest_framework.permissions import AllowAny

pytestmark = [pytest.mark.unit, pytest.mark.auth]

NL = chr(10)
AUTH_ROUTE_PREFIX = "api/auth/"

PUBLIC_PATHS = ("/api/auth/login/", "/api/auth/register/", "/api/auth/refresh/")
PROTECTED_PATHS = ("/api/auth/logout/", "/api/auth/me/")


def _iter_url_patterns(patterns: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    for pattern in patterns:
        route = prefix + str(getattr(pattern, "_route", pattern.pattern))
        if hasattr(pattern, "url_patterns"):
            yield from _iter_url_patterns(pattern.url_patterns, route)
        else:
            yield route, pattern


def _mounted_auth_views() -> dict[str, type]:
    """从 URL conf 取出 `/api/auth/` 下每个叶子路由实际挂载的视图类：{path: view_class}。"""
    views: dict[str, type] = {}
    for route, _pattern in _iter_url_patterns(get_resolver().url_patterns):
        if not route.startswith(AUTH_ROUTE_PREFIX):
            continue
        path = "/" + route
        views[path] = resolve(path).func.view_class
    return views


AUTH_VIEWS = _mounted_auth_views()


def test_scanner_covers_every_session_endpoint():
    """认证模块至少应有 5 个端点；扫不到就说明解析失效，后面的断言会空跑。"""
    assert len(AUTH_VIEWS) >= 5, f"只找到 {len(AUTH_VIEWS)} 个认证端点：{sorted(AUTH_VIEWS)}"


@pytest.mark.parametrize("path", PUBLIC_PATHS)
def test_public_endpoint_pairs_allow_any_with_empty_authentication(path: str):
    """公开端点：AllowAny 与空 authentication_classes 必须成对。"""
    view_class = AUTH_VIEWS[path]
    assert AllowAny in view_class.permission_classes, (
        f"{path} → {view_class.__name__} 未声明 AllowAny"
    )
    assert list(view_class.authentication_classes) == [], (
        f"{path} → {view_class.__name__} 未置空 authentication_classes，"
        "会在进入视图前被 DRF 鉴权拦下"
    )


@pytest.mark.parametrize("path", PROTECTED_PATHS)
def test_protected_endpoint_pairs_non_public_with_authentication(path: str):
    """需要身份的端点：非 AllowAny 与非空 authentication_classes 必须成对。"""
    view_class = AUTH_VIEWS[path]
    assert AllowAny not in view_class.permission_classes, (
        f"{path} → {view_class.__name__} 意外地对任何人开放"
    )
    assert list(view_class.authentication_classes), (
        f"{path} → {view_class.__name__} 的 authentication_classes 为空，请求将无法解析出用户"
    )


def test_invariant_holds_for_every_mounted_auth_view():
    """穷举形式：未来新增第六个认证端点时自动被覆盖。"""
    violations = []
    for path, view_class in sorted(AUTH_VIEWS.items()):
        allow_any = AllowAny in view_class.permission_classes
        empty_authentication = list(view_class.authentication_classes) == []
        if allow_any != empty_authentication:
            violations.append(
                f"{path} → {view_class.__name__}: "
                f"AllowAny={allow_any} 空authentication_classes={empty_authentication}"
            )
    assert violations == [], (
        "以下认证端点的鉴权姿态只写了一半：" + NL + NL.join(f"  - {v}" for v in violations)
    )
