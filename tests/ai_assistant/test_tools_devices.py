"""list_devices 平台工具 — schema / handler 单元测试（tool_registry 单一真相源）。"""

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def test_list_devices_schema_registered():
    """TOOL_SCHEMAS 含 list_devices：devices/list_all，只读，设备管理分类。"""
    schema = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "list_devices")
    assert schema["module"] == "devices"
    assert schema["action"] == "list_all"
    assert schema["read_only"] is True
    assert schema["category"] == "设备管理"


def test_schema_names_unique_and_count_minimum():
    """工具名唯一且数量不低于基线（防误删；具体数量随工具增长，精确计数易碎）。"""
    names = [t["name"] for t in tool_registry.TOOL_SCHEMAS]
    assert len(names) == len(set(names))
    assert len(names) >= 26


def test_resolve_list_all_handler():
    """devices/list_all 有注册 handler。"""
    assert tool_registry.resolve("devices", "list_all") is not None


def test_handler_calls_device_api_with_user_id(monkeypatch):
    """handler 透传 user_id 到 device_pool.api.list_devices，返回其 dict 列表。"""
    from apps.device_pool import api as device_api

    fake = [
        {"serial": "R5CT", "status": "ONLINE"},
        {"serial": "RF8N", "status": "BUSY", "occupied_by": "admin"},
    ]
    captured = {}

    def fake_list_devices(user_id=""):
        captured["user_id"] = user_id
        return fake

    monkeypatch.setattr(device_api, "list_devices", fake_list_devices)

    handler = tool_registry.resolve("devices", "list_all")
    assert handler("7") == fake
    assert captured["user_id"] == "7"


def test_device_action_schema_registered():
    """TOOL_SCHEMAS 含 device_action：devices/action，写工具，设备管理分类。"""
    schema = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "device_action")
    assert schema["module"] == "devices"
    assert schema["action"] == "action"
    assert schema["read_only"] is False
    assert schema["category"] == "设备管理"


def test_resolve_devices_action_handler():
    """devices/action 有注册 handler。"""
    assert tool_registry.resolve("devices", "action") is not None


def test_device_action_handler_calls_api(monkeypatch):
    """handler 透传 serial/action 到 device_pool.api.device_action，返回前台 dict。"""
    from apps.device_pool import api as device_api

    captured = {}

    def fake_device_action(serial, action, **kwargs):
        captured["serial"] = serial
        captured["action"] = action
        captured["kwargs"] = kwargs
        return {"package": "com.x", "activity": "Main"}

    monkeypatch.setattr(device_api, "device_action", fake_device_action)

    handler = tool_registry.resolve("devices", "action")
    result = handler("7", serial="R5CT", action="back")

    assert result == {"package": "com.x", "activity": "Main"}
    assert captured["serial"] == "R5CT"
    assert captured["action"] == "back"


def test_list_apps_schema_registered():
    """TOOL_SCHEMAS 含 list_apps：devices/list_apps，只读，设备管理分类。"""
    schema = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "list_apps")
    assert schema["module"] == "devices"
    assert schema["action"] == "list_apps"
    assert schema["read_only"] is True
    assert schema["category"] == "设备管理"


def test_list_apps_handler_calls_api(monkeypatch):
    """handler 透传 serial/query 到 device_pool.api.list_apps。"""
    from apps.device_pool import api as device_api

    captured = {}

    def fake_list_apps(serial, query=""):
        captured["serial"] = serial
        captured["query"] = query
        return {"packages": ["com.govee.home"], "count": 1}

    monkeypatch.setattr(device_api, "list_apps", fake_list_apps)

    handler = tool_registry.resolve("devices", "list_apps")
    result = handler("7", serial="R5CT", query="govee")

    assert result == {"packages": ["com.govee.home"], "count": 1}
    assert captured["serial"] == "R5CT"
    assert captured["query"] == "govee"
