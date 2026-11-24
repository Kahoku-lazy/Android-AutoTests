from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.serial_log import port_service
from backend.apps.serial_log.models import LogPort
from backend.apps.serial_log.views import (
    LogPortDetailAPIView,
    LogPortListAPIView,
)

pytestmark = [pytest.mark.django_db, pytest.mark.api]

CONFIG_SOURCES = '{"7005": {"sku": "H6810", "baud": 921600}}'


class _FakeSwitch:
    def __init__(self):
        self.opened: set[int] = set()

    def is_listening(self, port: int) -> bool:
        return int(port) in self.opened

    def is_reserved(self, port: int) -> bool:
        return int(port) in self.opened

    def reserved_count(self) -> int:
        return len(self.opened)

    def open(self, params) -> None:
        self.opened.add(int(params.port))

    def close(self, port: int) -> None:
        self.opened.discard(int(port))


@pytest.fixture
def fake_switch(monkeypatch):
    switch = _FakeSwitch()
    monkeypatch.setattr(port_service, "get_port_switch", lambda: switch)
    monkeypatch.setattr(port_service, "_await_listening", lambda port, timeout=1.0: True)
    return switch


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(username="normal", password="pass")


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


def _call(view_cls, *, method: str, user=None, data=None, path="/api/serial-log/ports/", **kw):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **kw)


@override_settings(
    DEVICE_LOG_SOURCES=CONFIG_SOURCES,
    DEVICE_LOG_ENABLED=False,
    DEVICE_LOG_ADVERTISE_HOST="10.0.0.9",
)
def test_list_contains_listen_ip_origin_address(normal_user):
    response = _call(LogPortListAPIView, method="get", user=normal_user)
    assert response.status_code == 200
    assert response.data["listen_ip"] == "10.0.0.9"
    row = response.data["ports"][0]
    assert {"origin", "address"} <= set(row)
    assert row["origin"] == "config"
    assert row["address"] == "10.0.0.9:7005"


def test_create_forbidden_for_normal_user(normal_user):
    response = _call(
        LogPortListAPIView,
        method="post",
        user=normal_user,
        data={"port": 7008, "sku": "H717D", "baud": 115200},
    )
    assert response.status_code == 403
    assert not LogPort.objects.filter(port=7008).exists()


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_returns_201_and_listens(admin_user, fake_switch):
    response = _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7008, "sku": "H717D", "baud": 115200},
    )
    assert response.status_code == 201
    assert response.data["origin"] == "custom"
    assert response.data["listening"] is True
    assert LogPort.objects.get(port=7008).origin == LogPort.ORIGIN_CUSTOM
    assert 7008 in fake_switch.opened


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_duplicate_and_invalid_return_400(admin_user, fake_switch):
    _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7008, "sku": "H717D", "baud": 115200},
    )
    dup = _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7008, "sku": "X", "baud": 9600},
    )
    assert dup.status_code == 400 and "7008" in str(dup.data)
    bad = _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 70000, "sku": "X", "baud": 9600},
    )
    assert bad.status_code == 400
    no_sku = _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7009, "sku": "", "baud": 9600},
    )
    assert no_sku.status_code == 400


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_patch_custom_200_and_config_400(admin_user, fake_switch):
    _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7008, "sku": "H717D", "baud": 115200},
    )
    ok = _call(
        LogPortDetailAPIView,
        method="patch",
        user=admin_user,
        data={"sku": "H717D-V2"},
        path="/api/serial-log/ports/7008/",
        port=7008,
    )
    assert ok.status_code == 200
    assert ok.data["sku"] == "H717D-V2"
    cfg = _call(
        LogPortDetailAPIView,
        method="patch",
        user=admin_user,
        data={"sku": "X"},
        path="/api/serial-log/ports/7005/",
        port=7005,
    )
    assert cfg.status_code == 400 and "配置端口" in str(cfg.data)


def test_patch_and_delete_forbidden_for_normal_user(normal_user):
    patch = _call(
        LogPortDetailAPIView,
        method="patch",
        user=normal_user,
        data={"sku": "X"},
        path="/api/serial-log/ports/7008/",
        port=7008,
    )
    delete = _call(
        LogPortDetailAPIView,
        method="delete",
        user=normal_user,
        path="/api/serial-log/ports/7008/",
        port=7008,
    )
    assert patch.status_code == 403 and delete.status_code == 403


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_delete_custom_200_and_config_400(admin_user, fake_switch):
    _call(
        LogPortListAPIView,
        method="post",
        user=admin_user,
        data={"port": 7008, "sku": "H717D", "baud": 115200},
    )
    ok = _call(
        LogPortDetailAPIView,
        method="delete",
        user=admin_user,
        path="/api/serial-log/ports/7008/",
        port=7008,
    )
    assert ok.status_code == 200 and ok.data["deleted"] is True
    assert not LogPort.objects.filter(port=7008).exists()
    cfg = _call(
        LogPortDetailAPIView,
        method="delete",
        user=admin_user,
        path="/api/serial-log/ports/7005/",
        port=7005,
    )
    assert cfg.status_code == 400


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/serial-log/ports/", "post"),
        ("/api/serial-log/ports/7008/", "patch"),
        ("/api/serial-log/ports/7008/", "delete"),
    ],
)
def test_new_paths_resolve(path, method):
    match = resolve(path)
    assert match.url_name in ("ports", "port_detail")
