"""串口日志接口契约：鉴权、权限、路径与开关落库。

用视图直调 + 轻量请求工厂，不依赖运行中的 Redis / 现场端口：
- 未登录 401 由网关中间件负责；
- 端口开关的 TCP 监听用假 switch 替身，真实落库仍走 `apps.serial_log.api`。
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.serial_log import port_service
from backend.apps.serial_log.models import LogPort
from backend.apps.serial_log.views import (
    LogKeywordCatalogAPIView,
    LogPortLinesAPIView,
    LogPortListAPIView,
    LogPortToggleAPIView,
)
from backend.gateway.middleware import JWTAuthenticationMiddleware

pytestmark = [pytest.mark.django_db, pytest.mark.api]


class _FakeSwitch:
    """只记录开关状态的替身：不绑定任何真实 TCP 端口。"""

    def __init__(self) -> None:
        self.opened: set[int] = set()

    def is_listening(self, port: int) -> bool:
        return int(port) in self.opened

    def is_reserved(self, port: int) -> bool:
        return False

    def reserved_count(self) -> int:
        return len(self.opened)

    def open(self, params) -> None:
        self.opened.add(int(params.port))

    def close(self, port: int) -> None:
        self.opened.discard(int(port))


@pytest.fixture
def factory() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(username="normal", password="pass")


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


def _call(
    view_cls,
    *,
    method: str = "get",
    path: str = "/api/serial-log/ports/",
    user=None,
    data=None,
    **url_kwargs,
):
    """用请求工厂直调视图：模拟网关注入 user_id，并让 DRF 鉴权通过。"""
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **url_kwargs)


def test_middleware_rejects_missing_token():
    request = RequestFactory().get("/api/serial-log/ports/")
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 401


@override_settings(DEVICE_LOG_ENABLED=False)
def test_port_list_readable_by_normal_user(normal_user):
    response = _call(LogPortListAPIView, user=normal_user)
    assert response.status_code == 200
    ports = response.data["ports"]
    assert ports and {"port", "sku", "baud", "enabled", "listening", "log_file"} <= set(ports[0])


def test_toggle_forbidden_for_normal_user(normal_user):
    response = _call(
        LogPortToggleAPIView,
        method="post",
        user=normal_user,
        data={"port": 7005, "enabled": False},
    )
    assert response.status_code == 403


def test_toggle_persists_for_superuser(admin_user, monkeypatch):
    monkeypatch.setattr(port_service, "get_port_switch", lambda: _FakeSwitch())
    response = _call(
        LogPortToggleAPIView,
        method="post",
        user=admin_user,
        data={"port": 7005, "enabled": False},
    )
    assert response.status_code == 200
    assert response.data["enabled"] is False
    assert LogPort.objects.get(port=7005).enabled is False


def test_toggle_unknown_port_returns_readable_400(admin_user, monkeypatch):
    monkeypatch.setattr(port_service, "get_port_switch", lambda: _FakeSwitch())
    response = _call(
        LogPortToggleAPIView,
        method="post",
        user=admin_user,
        data={"port": 7004, "enabled": False},
    )
    assert response.status_code == 400
    assert "7004" in str(response.data)


@override_settings(DEVICE_LOG_ENABLED=False)
def test_lines_unknown_port_returns_readable_conclusion(normal_user):
    response = _call(
        LogPortLinesAPIView,
        path="/api/serial-log/ports/7004/lines/",
        user=normal_user,
        port=7004,
    )
    assert response.status_code == 200
    assert response.data["conclusion"] == "port_not_configured"


def test_keyword_catalog_readable(normal_user):
    response = _call(
        LogKeywordCatalogAPIView,
        path="/api/serial-log/keywords/",
        user=normal_user,
    )
    assert response.status_code == 200
    assert "keywords" in response.data
    assert "keyword_count" in response.data


@pytest.mark.parametrize("path", ["/api/ai/log-ports/", "/api/ai/log-keywords/"])
def test_old_paths_are_gone(path):
    with pytest.raises(Resolver404):
        resolve(path)
