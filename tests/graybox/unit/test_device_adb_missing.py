"""adb 缺失时设备接口返回 503 + 可操作提示（对应 adb-platform-bootstrap 需求三）。

用 DRF 视图的 `cls` 关掉鉴权后直调，覆盖「用空列表冒充成功」之外的错误分支。
"""

from __future__ import annotations

import pytest

from rest_framework.test import APIRequestFactory

from backend.apps.device_pool import views
from backend.apps.device_pool.manager import detector, state_machine
from utils.adb import AdbUnavailableError

pytestmark = [pytest.mark.unit]

_MESSAGE = "未找到可用的 adb：请运行 `python run.py setup` 安装平台自带 platform-tools。"


def _call(view, request, monkeypatch):
    """关闭该视图的鉴权/权限后直调，只验证错误分支。"""
    monkeypatch.setattr(view.cls, "permission_classes", [])
    monkeypatch.setattr(view.cls, "authentication_classes", [])
    return view(request)


def _boom():
    raise AdbUnavailableError(_MESSAGE)


def test_list_devices_returns_503_when_adb_missing(monkeypatch):
    """GET /api/devices/ 在 adb 不可用时返回 503 与安装提示。"""
    monkeypatch.setattr(state_machine, "update_device_status", _boom)

    response = _call(views.list_devices, APIRequestFactory().get("/api/devices/"), monkeypatch)

    assert response.status_code == 503
    assert "run.py setup" in response.data["message"]


def test_scan_devices_returns_503_when_adb_missing(monkeypatch):
    """POST /api/devices/scan/ 在 adb 不可用时返回 503。"""
    monkeypatch.setattr(detector, "connectable_serials", _boom)

    request = APIRequestFactory().post("/api/devices/scan/", {}, format="json")
    response = _call(views.scan_device, request, monkeypatch)

    assert response.status_code == 503
    assert "run.py setup" in response.data["message"]


def test_list_devices_other_errors_still_500(monkeypatch):
    """非 adb 的异常仍走原有 500 分支，不被误报成环境问题。"""

    def _runtime_error():
        raise RuntimeError("db down")

    monkeypatch.setattr(state_machine, "update_device_status", _runtime_error)

    response = _call(views.list_devices, APIRequestFactory().get("/api/devices/"), monkeypatch)

    assert response.status_code == 500
    assert response.data["message"] == "设备列表加载失败"
