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


def test_schema_count_is_26():
    """平台工具总数 26（25 + 执行状态 get_run_status）。"""
    assert len(tool_registry.TOOL_SCHEMAS) == 26


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
