"""
模块功能：➡️ 串口日志接口契约：鉴权、权限、路径与开关落库 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/serial_log/api/test_serial_log_api.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/serial_log、backend/gateway/middleware.py
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.serial_log import port_service
from backend.apps.serial_log.models import LogKeyword, LogPort
from backend.apps.serial_log.views import (
    LogKeywordCatalogAPIView,
    LogKeywordDetailAPIView,
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
    """关键词目录契约：来源 db、功能点带 scope、无 keyword_file、计数与更新时间。"""
    from backend.apps.serial_log import api as serial_api

    serial_api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功", feature_id=0, scope="*"
    )
    serial_api.upsert_keyword(
        "h6601_boot", module="设备开关", feature="H6601开机完成", feature_id=56, scope="H6601"
    )
    response = _call(
        LogKeywordCatalogAPIView,
        path="/api/serial-log/keywords/",
        user=normal_user,
    )
    assert response.status_code == 200
    data = response.data
    assert data["origin"] == "db"
    assert "keyword_file" not in data
    assert data["keyword_count"] == 2
    assert data["feature_count"] == 2
    assert data["updated_at"]
    entries = {item["keyword"]: item["features"] for item in data["keywords"]}
    assert entries["switch_on"] == [
        {
            "row_id": LogKeyword.objects.get(keyword="switch_on", feature_id=0).pk,
            "id": 0,
            "module": "设备开关",
            "feature": "打开设备成功",
            "scope": "*",
        }
    ]
    assert entries["h6601_boot"][0]["scope"] == "H6601"
    assert entries["h6601_boot"][0]["row_id"]


def test_keyword_catalog_empty_table_readable(normal_user):
    """空表给可读空态：origin none + note，不抛错。"""
    response = _call(
        LogKeywordCatalogAPIView,
        path="/api/serial-log/keywords/",
        user=normal_user,
    )
    assert response.status_code == 200
    assert response.data["origin"] == "none"
    assert response.data["keywords"] == []
    assert response.data["note"]


@pytest.mark.parametrize("path", ["/api/ai/log-ports/", "/api/ai/log-keywords/"])
def test_old_paths_are_gone(path):
    with pytest.raises(Resolver404):
        resolve(path)


# ── 关键词维护接口（仅超管）─────────────────────────────────────────────────


def _seed_keyword(keyword="switch_on", feature_id=0, scope="*"):
    """经 api 登记一条关键词，返回行。"""
    from backend.apps.serial_log import api as serial_api

    return serial_api.create_keyword(
        keyword, module="设备开关", feature="打开设备成功", feature_id=feature_id, scope=scope
    )


def test_keyword_create_superuser_201(admin_user):
    response = _call(
        LogKeywordCatalogAPIView,
        method="post",
        path="/api/serial-log/keywords/",
        user=admin_user,
        data={
            "keyword": "h6601_boot",
            "module": "设备开关",
            "feature": "H6601开机完成",
            "scope": "H6601",
        },
    )
    assert response.status_code == 201
    row = response.data["row"]
    assert row["keyword"] == "h6601_boot"
    assert row["scope"] == "H6601"
    assert row["row_id"] == LogKeyword.objects.get(keyword="h6601_boot").pk


def test_keyword_create_forbidden_for_normal_user(normal_user):
    response = _call(
        LogKeywordCatalogAPIView,
        method="post",
        path="/api/serial-log/keywords/",
        user=normal_user,
        data={"keyword": "x", "module": "m", "feature": "f"},
    )
    assert response.status_code == 403
    assert LogKeyword.objects.count() == 0


def test_keyword_create_duplicate_readable_400(admin_user):
    _seed_keyword()
    response = _call(
        LogKeywordCatalogAPIView,
        method="post",
        path="/api/serial-log/keywords/",
        user=admin_user,
        data={
            "keyword": "switch_on",
            "module": "设备开关",
            "feature": "打开设备成功",
            "feature_id": 0,
        },
    )
    assert response.status_code == 400
    assert "已登记" in str(response.data)
    assert LogKeyword.objects.count() == 1


def test_keyword_patch_partial_update(admin_user):
    row = _seed_keyword()
    response = _call(
        LogKeywordDetailAPIView,
        method="patch",
        path=f"/api/serial-log/keywords/{row.pk}/",
        user=admin_user,
        data={"feature": "打开设备成功（改）"},
        row_id=row.pk,
    )
    assert response.status_code == 200
    assert response.data["row"]["feature"] == "打开设备成功（改）"
    assert response.data["row"]["keyword"] == "switch_on"


def test_keyword_patch_collision_readable_400(admin_user):
    first = _seed_keyword(keyword="a", feature_id=0)
    second = _seed_keyword(keyword="b", feature_id=1)
    response = _call(
        LogKeywordDetailAPIView,
        method="patch",
        path=f"/api/serial-log/keywords/{second.pk}/",
        user=admin_user,
        data={"keyword": "a", "feature_id": 0},
        row_id=second.pk,
    )
    assert response.status_code == 400
    assert LogKeyword.objects.get(pk=second.pk).keyword == "b"
    assert LogKeyword.objects.get(pk=first.pk).keyword == "a"


def test_keyword_patch_forbidden_for_normal_user(normal_user):
    row = _seed_keyword()
    response = _call(
        LogKeywordDetailAPIView,
        method="patch",
        path=f"/api/serial-log/keywords/{row.pk}/",
        user=normal_user,
        data={"feature": "x"},
        row_id=row.pk,
    )
    assert response.status_code == 403
    assert LogKeyword.objects.get(pk=row.pk).feature == "打开设备成功"


def test_keyword_detail_unknown_row_readable_400(admin_user):
    for method in ("patch", "delete"):
        response = _call(
            LogKeywordDetailAPIView,
            method=method,
            path="/api/serial-log/keywords/999999/",
            user=admin_user,
            data={"feature": "x"} if method == "patch" else None,
            row_id=999999,
        )
        assert response.status_code == 400
        assert "不存在" in str(response.data)


def test_keyword_delete_superuser_keeps_ports(admin_user):
    from backend.apps.serial_log import api as serial_api

    serial_api.create_custom_port(7008, "H717D", 115200)
    row = _seed_keyword()
    response = _call(
        LogKeywordDetailAPIView,
        method="delete",
        path=f"/api/serial-log/keywords/{row.pk}/",
        user=admin_user,
        row_id=row.pk,
    )
    assert response.status_code == 200
    assert response.data["deleted"] is True
    assert LogKeyword.objects.count() == 0
    assert LogPort.objects.filter(port=7008).exists()  # 删除关键词不动端口
