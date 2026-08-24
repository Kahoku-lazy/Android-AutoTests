"""api.list_devices — 设备管理口径全量列表（AI 助手 list_devices 工具数据源）单元测试。"""

from datetime import datetime
from types import SimpleNamespace

import pytest

from apps.device_pool import api as api_module
from apps.device_pool import service as service_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _fake_device(serial, status="ONLINE", **overrides) -> SimpleNamespace:
    base = dict(
        id=1,
        serial=serial,
        name="",
        model="",
        brand="",
        screen_w=0,
        screen_h=0,
        status=status,
        connection_type="USB",
        connection_addr="",
        locked_by="",
        locked_at=None,
        occupied_by="",
        occupied_at=None,
        connected_at=None,
        added_by="",
        last_seen=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _patch_env(monkeypatch, devices: list, *, visible=None):
    """替换 Device.objects / pool 单例 / service 依赖，构造纯逻辑运行环境。"""

    class _FakeObjects:
        def all(self):
            return devices

    monkeypatch.setattr(api_module, "Device", SimpleNamespace(objects=_FakeObjects()))
    monkeypatch.setattr(api_module, "device", SimpleNamespace(current_serial=""))
    monkeypatch.setattr(service_module, "resolve_admin_ids", lambda users: set())
    monkeypatch.setattr(
        service_module, "is_device_visible", visible or (lambda d, uid, admins: True)
    )
    monkeypatch.setattr(service_module, "usernames_by_ids", lambda ids: {"1": "admin"})

    class _FakeLockObjects:
        def filter(self, **kwargs):
            return self

        def order_by(self, *args):
            return self

        def first(self):
            return None

    monkeypatch.setattr(service_module, "DeviceLock", SimpleNamespace(objects=_FakeLockObjects()))


def test_list_devices_includes_busy_and_sorts_online_first(monkeypatch):
    """使用中（BUSY）设备包含在结果中，ONLINE 排在 BUSY 前（设备管理页顺序）。"""
    busy = _fake_device(
        "RF8N", status="BUSY", occupied_by="1", occupied_at=datetime(2026, 8, 19, 10, 0, 0)
    )
    online = _fake_device("R5CT", status="ONLINE")
    _patch_env(monkeypatch, [busy, online])

    result = api_module.list_devices(user_id="7")

    assert [d["serial"] for d in result] == ["R5CT", "RF8N"]
    assert result[0]["status"] == "ONLINE"
    assert result[1]["status"] == "BUSY"


def test_list_devices_resolves_occupied_by_username(monkeypatch):
    """使用人数字 ID 经 usernames_by_ids 转为用户名（设备管理页口径）。"""
    busy = _fake_device("RF8N", status="BUSY", occupied_by="1")
    _patch_env(monkeypatch, [busy])

    result = api_module.list_devices()

    assert result[0]["occupied_by"] == "admin"


def test_list_devices_applies_visibility_filter(monkeypatch):
    """不可见设备被过滤（is_device_visible 规则生效）。"""
    hidden = _fake_device("WIFI-LOCKED", connection_type="WIFI", locked_by="2")
    visible = _fake_device("USB-1")
    _patch_env(
        monkeypatch,
        [hidden, visible],
        visible=lambda d, uid, admins: d.serial != "WIFI-LOCKED",
    )

    result = api_module.list_devices(user_id="7")

    assert [d["serial"] for d in result] == ["USB-1"]


def test_list_devices_marks_current_device(monkeypatch):
    """当前活动设备 is_current=True（复用 device.current_serial）。"""
    a = _fake_device("A", status="ONLINE")
    b = _fake_device("B", status="ONLINE")
    _patch_env(monkeypatch, [a, b])
    monkeypatch.setattr(api_module, "device", SimpleNamespace(current_serial="B"))

    result = api_module.list_devices()

    assert result[0]["is_current"] is False
    assert result[1]["is_current"] is True
