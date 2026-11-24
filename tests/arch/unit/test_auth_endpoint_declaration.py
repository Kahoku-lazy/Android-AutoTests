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
    views: dict[str, type] = {}
    for route, _pattern in _iter_url_patterns(get_resolver().url_patterns):
        if not route.startswith(AUTH_ROUTE_PREFIX):
            continue
        path = "/" + route
        views[path] = resolve(path).func.view_class
    return views


AUTH_VIEWS = _mounted_auth_views()


def test_scanner_covers_every_session_endpoint():
    assert len(AUTH_VIEWS) >= 5, f"只找到 {len(AUTH_VIEWS)} 个认证端点：{sorted(AUTH_VIEWS)}"


@pytest.mark.parametrize("path", PUBLIC_PATHS)
def test_public_endpoint_pairs_allow_any_with_empty_authentication(path: str):
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
    view_class = AUTH_VIEWS[path]
    assert AllowAny not in view_class.permission_classes, (
        f"{path} → {view_class.__name__} 意外地对任何人开放"
    )
    assert list(view_class.authentication_classes), (
        f"{path} → {view_class.__name__} 的 authentication_classes 为空，请求将无法解析出用户"
    )


def test_invariant_holds_for_every_mounted_auth_view():
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
