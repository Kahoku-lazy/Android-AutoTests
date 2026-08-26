"""api.use_device / api.device_action — AI 设备动作入口单元测试（纯逻辑，mock 单例）。"""

from types import SimpleNamespace

import pytest

from apps.device_pool import api as api_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


class _DoesNotExist(Exception):
    pass


def _fake_device(serial="R5CT", status="ONLINE", occupied_by="", **overrides):
    base = dict(
        serial=serial,
        status=status,
        occupied_by=occupied_by,
        connection_type="USB",
        connection_addr="",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _patch_env(monkeypatch, device=None, get_raises=None, shell_output=""):
    """替换 Device.objects.get 与 device 单例，返回动作/切换调用记录。"""

    class _Objects:
        def get(self, serial=""):
            if get_raises is not None:
                raise get_raises
            return device

    class _Device:
        DoesNotExist = _DoesNotExist
        objects = _Objects()

    monkeypatch.setattr(api_module, "Device", _Device)

    calls = SimpleNamespace(switched=[], actions=[], shells=[])
    fake_pool = SimpleNamespace(
        current_serial="",
        switch_to=lambda serial, ct, addr: calls.switched.append((serial, ct, addr)),
        action_start_app=lambda pkg: calls.actions.append(("start_app", pkg)),
        action_stop_app=lambda pkg: calls.actions.append(("stop_app", pkg)),
        action_press_key=lambda key="back": calls.actions.append(("press_key", key)),
        action_click=lambda x, y: calls.actions.append(("click", x, y)),
        action_longclick=lambda x, y: calls.actions.append(("long_click", x, y)),
        action_swipe=lambda direction, distance: calls.actions.append(
            ("swipe", direction, distance)
        ),
        action_input=lambda text, x, y, clear_first: calls.actions.append(
            ("input_text", text, x, y, clear_first)
        ),
        action_shell=lambda cmd: calls.shells.append(cmd) or shell_output,
        app_current=lambda: {"package": "com.x", "activity": "Main"},
    )
    monkeypatch.setattr(api_module, "device", fake_pool)
    return calls


def test_use_device_empty_serial_raises():
    """空 serial 抛 ValueError。"""
    with pytest.raises(ValueError):
        api_module.use_device("")


def test_use_device_unregistered_raises(monkeypatch):
    """未注册设备抛 ValueError。"""
    _patch_env(monkeypatch, get_raises=_DoesNotExist())
    with pytest.raises(ValueError):
        api_module.use_device("UNKNOWN")


def test_use_device_execution_occupied_raises(monkeypatch):
    """执行引擎占用（runner- 前缀）抛 ValueError。"""
    _patch_env(monkeypatch, device=_fake_device(status="BUSY", occupied_by="runner-1"))
    with pytest.raises(ValueError):
        api_module.use_device("R5CT")


def test_use_device_plain_user_busy_allowed_and_switches(monkeypatch):
    """普通用户占用（非执行前缀）放行并切换到目标设备。"""
    calls = _patch_env(monkeypatch, device=_fake_device(status="BUSY", occupied_by="1"))
    api_module.use_device("R5CT")
    assert calls.switched == [("R5CT", "USB", "")]


def test_device_action_start_app_dispatches_and_returns_current(monkeypatch):
    """start_app 分发到单例并返回 app_current。"""
    calls = _patch_env(monkeypatch, device=_fake_device())
    result = api_module.device_action("R5CT", "start_app", package="com.x")
    assert calls.actions == [("start_app", "com.x")]
    assert result == {"package": "com.x", "activity": "Main"}


def test_device_action_back_dispatches_press_key(monkeypatch):
    """back 动作分发到 action_press_key('back')。"""
    calls = _patch_env(monkeypatch, device=_fake_device())
    api_module.device_action("R5CT", "back")
    assert calls.actions == [("press_key", "back")]


def test_device_action_click_normalizes_coords(monkeypatch):
    """click 将字符串坐标归一为 int 并分发。"""
    calls = _patch_env(monkeypatch, device=_fake_device())
    api_module.device_action("R5CT", "click", x="100", y="200")
    assert calls.actions == [("click", 100, 200)]


def test_device_action_swipe_dispatches(monkeypatch):
    """swipe 分发方向与距离。"""
    calls = _patch_env(monkeypatch, device=_fake_device())
    api_module.device_action("R5CT", "swipe", direction="left", distance=300)
    assert calls.actions == [("swipe", "left", 300)]


def test_device_action_click_requires_coords(monkeypatch):
    """click 缺坐标抛 ValueError。"""
    _patch_env(monkeypatch, device=_fake_device())
    with pytest.raises(ValueError):
        api_module.device_action("R5CT", "click")


def test_device_action_start_app_requires_package(monkeypatch):
    """start_app 缺包名抛 ValueError。"""
    _patch_env(monkeypatch, device=_fake_device())
    with pytest.raises(ValueError):
        api_module.device_action("R5CT", "start_app")


def test_device_action_unsupported_action_raises(monkeypatch):
    """不支持的 action 抛 ValueError。"""
    _patch_env(monkeypatch, device=_fake_device())
    with pytest.raises(ValueError):
        api_module.device_action("R5CT", "explode")


def test_list_apps_filters_by_query(monkeypatch):
    """list_apps 按 query 子串过滤包名。"""
    shell = "package:com.govee.home\npackage:com.android.settings\npackage:com.govee.test"
    _patch_env(monkeypatch, device=_fake_device(), shell_output=shell)

    result = api_module.list_apps("R5CT", query="govee")

    assert result["packages"] == ["com.govee.home", "com.govee.test"]
    assert result["count"] == 2


def test_list_apps_returns_all_without_query(monkeypatch):
    """list_apps 无 query 返回全部包名。"""
    shell = "package:com.govee.home\npackage:com.android.settings"
    _patch_env(monkeypatch, device=_fake_device(), shell_output=shell)

    result = api_module.list_apps("R5CT")

    assert result["packages"] == ["com.govee.home", "com.android.settings"]
    assert result["count"] == 2
