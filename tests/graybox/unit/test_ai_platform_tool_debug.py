"""平台工具调试：schema 推导 + JWT invoke（spec: ai-platform-tool-debug）。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.ai_assistant.tools import (
    ToolNotFoundError,
    get_tool_debug_schema,
    invoke_platform_tool,
)
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


# ── schema ──


def test_schema_list_devices_has_no_params():
    schema = get_tool_debug_schema("list_devices")
    assert schema["name"] == "list_devices"
    assert schema["read_only"] is True
    assert schema["parameters"] == []
    assert "user_id" not in {p["name"] for p in schema["parameters"]}


def test_schema_acquire_device_includes_serial_not_user_id():
    schema = get_tool_debug_schema("acquire_device")
    names = [p["name"] for p in schema["parameters"]]
    assert "serial" in names
    assert "user_id" not in names
    assert schema["read_only"] is False
    serial = next(p for p in schema["parameters"] if p["name"] == "serial")
    assert serial["required"] is True
    assert serial["type"] == "str"
    timeout = next(p for p in schema["parameters"] if p["name"] == "timeout")
    assert timeout["required"] is False
    assert timeout["default"] == 300


def test_schema_unknown_tool_raises():
    with pytest.raises(ToolNotFoundError):
        get_tool_debug_schema("not_a_real_tool")


# ── invoke ──


def test_invoke_rejects_unknown_keys(monkeypatch):
    def _fake(user_id: str = ""):
        return "[]"

    monkeypatch.setitem(
        __import__("apps.ai_assistant.tools", fromlist=["TOOLS"]).TOOLS,
        "list_devices",
        (_fake, True),
    )
    with pytest.raises(ValueError, match="未知参数"):
        invoke_platform_tool("list_devices", "1", {"foo": 1})


def test_invoke_user_id_from_arg_not_body(monkeypatch):
    captured = {}

    def _fake(user_id: str = ""):
        captured["user_id"] = user_id
        return "[]"

    monkeypatch.setitem(
        __import__("apps.ai_assistant.tools", fromlist=["TOOLS"]).TOOLS,
        "list_devices",
        (_fake, True),
    )
    result = invoke_platform_tool(
        "list_devices",
        "jwt-42",
        {"user_id": "spoofed"},
    )
    assert captured["user_id"] == "jwt-42"
    assert result == []


def test_invoke_unknown_tool():
    with pytest.raises(ToolNotFoundError):
        invoke_platform_tool("nope", "1", {})


def test_removed_tool_is_gone_from_tool_surface():
    """已移除的工具不得再出现在注册表、schema、可用工具清单与 invoke 端点。"""
    from apps.ai_assistant.tools import TOOL_META, TOOLS

    assert "get_online_devices" not in TOOLS
    assert "get_online_devices" not in TOOL_META
    with pytest.raises(ToolNotFoundError):
        get_tool_debug_schema("get_online_devices")

    user = User.objects.create_user(username="gone_user", password="x")
    client = Client()
    schema_resp = client.get("/api/ai/platform-tools/get_online_devices/", **_auth_headers(user))
    assert schema_resp.status_code == 404

    listing = client.get("/api/ai/available-tools/", **_auth_headers(user)).json()
    names = [t["name"] for c in listing["data"]["categories"] for t in c["tools"]]
    assert "get_online_devices" not in names


# ── HTTP ──


def test_http_schema_ok():
    user = User.objects.create_user(username="reader", password="x")
    client = Client()
    resp = client.get("/api/ai/platform-tools/list_devices/", **_auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["name"] == "list_devices"
    assert all(p["name"] != "user_id" for p in body["data"]["parameters"])


def test_http_schema_unknown_404():
    user = User.objects.create_user(username="r2", password="x")
    client = Client()
    resp = client.get("/api/ai/platform-tools/not_exist/", **_auth_headers(user))
    assert resp.status_code == 404


def test_http_invoke_readonly_as_normal_user(monkeypatch):
    monkeypatch.setattr(
        "apps.ai_assistant.views_tool_debug_drf.invoke_platform_tool",
        lambda name, user_id, params: [{"serial": "A"}],
    )
    user = User.objects.create_user(username="normal", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/platform-tools/list_devices/invoke/",
        data={},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["result"] == [{"serial": "A"}]


def test_http_invoke_write_forbidden_for_normal_user(monkeypatch):
    called = {"n": 0}

    def _should_not_run(*_a, **_k):
        called["n"] += 1
        return {}

    monkeypatch.setattr(
        "apps.ai_assistant.views_tool_debug_drf.invoke_platform_tool",
        _should_not_run,
    )
    user = User.objects.create_user(username="normal2", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/platform-tools/acquire_device/invoke/",
        data={"serial": "S"},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 403
    assert called["n"] == 0


def test_http_invoke_write_ok_for_superuser(monkeypatch):
    monkeypatch.setattr(
        "apps.ai_assistant.views_tool_debug_drf.invoke_platform_tool",
        lambda name, user_id, params: {"ok": True, "serial": params.get("serial")},
    )
    user = User.objects.create_superuser(username="admin", email="a@t.com", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/platform-tools/acquire_device/invoke/",
        data={"serial": "RF8"},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["result"]["serial"] == "RF8"


def test_http_invoke_unknown_404():
    user = User.objects.create_user(username="r3", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/platform-tools/not_exist/invoke/",
        data={},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 404


def test_url_reverse_not_under_tools_prefix():
    schema_path = reverse("ai:platform_tool_schema", kwargs={"name": "list_devices"})
    invoke_path = reverse("ai:platform_tool_invoke", kwargs={"name": "list_devices"})
    # 全平台 /api/ 路径以 / 结尾（openspec/specs/api-path-convention）
    assert schema_path == "/api/ai/platform-tools/list_devices/"
    assert invoke_path == "/api/ai/platform-tools/list_devices/invoke/"
    assert "/api/ai/tools/" not in schema_path
    assert "/api/ai/tools/" not in invoke_path


# ── 调试候选：设备参数下拉（spec: ai-platform-tool-debug）──

# 需要 serial 并经开引擎取数的设备管理工具（acquire/release 是占用记账，不在内）
_PHONE_TOOLS = [
    "list_apps",
    "input_text",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "current_app",
    "click_ratio",
    "drag_ratio",
    "xpath_action",
]

# device_action 拆解后的 6 个单职责工具
_SPLIT_WRITE_TOOLS = ["app_control", "tap_screen", "swipe_screen", "press_key", "input_text"]


def test_schema_phone_tools_declare_serial_options():
    for tool in _PHONE_TOOLS:
        schema = get_tool_debug_schema(tool)
        serial = next(p for p in schema["parameters"] if p["name"] == "serial")
        assert serial["options_source"] == "devices:available", tool


def test_schema_bookkeeping_tools_have_no_serial_options():
    for tool in ("acquire_device", "release_device"):
        schema = get_tool_debug_schema(tool)
        serial = next(p for p in schema["parameters"] if p["name"] == "serial")
        assert "options_source" not in serial, tool


def test_device_action_split_into_single_purpose_tools():
    """device_action 已拆成 6 个单职责工具，注册表/只读标记/引擎子集同步。"""
    from apps.ai_assistant.tools import TOOL_META, TOOLS
    from engines.ai.agentscope.config import VISION_TOOLS

    assert "device_action" not in TOOLS
    assert "device_action" not in TOOL_META
    with pytest.raises(ToolNotFoundError):
        get_tool_debug_schema("device_action")

    # 5 个写工具 + 1 个只读工具（current_app 不动设备）
    for name in _SPLIT_WRITE_TOOLS:
        assert TOOLS[name][1] is False, name
    assert TOOLS["current_app"][1] is True

    # 引擎角色子集不得引用不存在的工具，且拆出的 6 个都在 executor 可用集里
    assert set(VISION_TOOLS) <= set(TOOLS)
    for name in _SPLIT_WRITE_TOOLS + ["current_app"]:
        assert name in VISION_TOOLS, name

    # 每个新工具只暴露自己动作需要的参数
    assert [p["name"] for p in get_tool_debug_schema("app_control")["parameters"]] == [
        "serial",
        "action",
        "package",
    ]
    assert [p["name"] for p in get_tool_debug_schema("press_key")["parameters"]] == ["serial"]
    assert [p["name"] for p in get_tool_debug_schema("current_app")["parameters"]] == ["serial"]
    tap = get_tool_debug_schema("tap_screen")["parameters"]
    assert [p["name"] for p in tap] == ["serial", "mode", "x", "y"]
    assert tap[1]["default"] == "click"

    user = User.objects.create_user(username="split_user", password="x")
    client = Client()
    assert (
        client.get("/api/ai/platform-tools/device_action/", **_auth_headers(user)).status_code
        == 404
    )
    listing = client.get("/api/ai/available-tools/", **_auth_headers(user)).json()
    names = [t["name"] for c in listing["data"]["categories"] for t in c["tools"]]
    assert "device_action" not in names
    for name in _SPLIT_WRITE_TOOLS + ["current_app"]:
        assert name in names, name


def test_http_schema_without_candidates_has_no_options_field():
    user = User.objects.create_user(username="no_opts", password="x")
    client = Client()
    resp = client.get("/api/ai/platform-tools/list_devices/", **_auth_headers(user))
    assert resp.status_code == 200
    assert all("options" not in p for p in resp.json()["data"]["parameters"])


def test_http_schema_device_options_exclude_busy_and_occupied():
    from apps.device_pool.models import Device

    user = User.objects.create_user(username="pick_user", password="x")
    other = User.objects.create_user(username="pick_other", password="x")
    Device.objects.create(serial="FREE-1", name="空闲机", status="ONLINE")
    Device.objects.create(serial="BUSY-1", name="使用中", status="BUSY", occupied_by=str(other.id))
    Device.objects.create(
        serial="ENGINE-1", name="引擎占用", status="ONLINE", occupied_by="ai_agent-7"
    )

    client = Client()
    resp = client.get("/api/ai/platform-tools/tap_screen/", **_auth_headers(user))
    assert resp.status_code == 200
    serial = next(p for p in resp.json()["data"]["parameters"] if p["name"] == "serial")
    assert [o["value"] for o in serial["options"]] == ["FREE-1"]
    assert serial["options"][0]["label"]


def test_http_schema_device_options_match_visible_devices():
    from apps.device_pool.api import list_devices
    from apps.device_pool.models import Device

    user = User.objects.create_user(username="vis_user", password="x")
    other = User.objects.create_user(username="vis_other", password="x")
    Device.objects.create(serial="VIS-OK", name="可见空闲", status="ONLINE")
    Device.objects.create(
        serial="VIS-HIDDEN",
        name="他人锁定",
        status="ONLINE",
        connection_type="WIFI",
        locked_by=str(other.id),
    )

    expected = [
        d["serial"]
        for d in list_devices(user_id=str(user.id))
        if d["status"] == "ONLINE" and not d["occupied_by"]
    ]

    client = Client()
    resp = client.get("/api/ai/platform-tools/xpath_action/", **_auth_headers(user))
    assert resp.status_code == 200
    serial = next(p for p in resp.json()["data"]["parameters"] if p["name"] == "serial")
    values = [o["value"] for o in serial["options"]]
    assert values == expected
    assert "VIS-HIDDEN" not in values


# ── 失败状态码按成因区分（spec: ai-platform-tool-debug）──


# 会在手机上产生副作用的控制类工具（分类「设备控制」的成员判据）
_PHONE_CONTROL_TOOLS = {
    "app_control",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "input_text",
    "click_ratio",
    "drag_ratio",
    "xpath_action",
}


def test_tool_categories_group_tools_by_nature():
    """6 个分类按工具性质分组；分类是整类启停单位，控制类必须能单独关闭。"""
    from apps.ai_assistant.tools import TOOL_CATEGORIES, TOOL_META, TOOLS

    keys = [c["key"] for c in TOOL_CATEGORIES]
    assert keys == [
        "设备管理",
        "设备控制",
        "设备信息",
        "设备检查器",
        "视觉识别工具",
        "页面流工具",
    ]
    colors = [c["color"] for c in TOOL_CATEGORIES]
    assert len(set(colors)) == len(colors)

    def in_category(cat: str) -> set[str]:
        return {name for name, meta in TOOL_META.items() if meta[0] == cat}

    assert in_category("设备管理") == {"list_devices", "acquire_device", "release_device"}
    assert in_category("设备控制") == _PHONE_CONTROL_TOOLS
    assert in_category("设备信息") == {"list_apps", "current_app"}
    assert in_category("设备检查器") == {"screenshot_page"}
    assert in_category("视觉识别工具") == {"ocr_page"}
    assert in_category("页面流工具") == {"list_page_flows", "get_page_flow"}

    # 每个工具恰属一个已登记分类，无孤儿
    covered: set[str] = set()
    for key in keys:
        bucket = in_category(key)
        assert not (covered & bucket), key
        covered |= bucket
    assert covered == set(TOOLS)

    # 控制类之外不得再出现「会在手机上产生副作用」的工具
    for cat in ("设备管理", "设备信息", "设备检查器", "视觉识别工具", "页面流工具"):
        assert not (in_category(cat) & _PHONE_CONTROL_TOOLS), cat


def test_http_invoke_tool_failure_returns_500_and_logs(monkeypatch, caplog):
    """工具/引擎内部故障 → 5xx，不是 4xx；且必须留下服务端错误日志。"""

    def _boom(*_args, **_kwargs):
        raise AttributeError("'ShellResponse' object has no attribute 'splitlines'")

    monkeypatch.setattr(
        "apps.ai_assistant.views_tool_debug_drf.invoke_platform_tool",
        _boom,
    )
    user = User.objects.create_user(username="boom_user", password="x")
    client = Client()
    with caplog.at_level("ERROR", logger="ai_assistant"):
        resp = client.post(
            "/api/ai/platform-tools/list_apps/invoke/",
            data={"serial": "S"},
            content_type="application/json",
            **_auth_headers(user),
        )

    assert resp.status_code == 500
    body = resp.json()
    assert body["status"] is False
    assert "工具执行失败" in body["message"]
    assert "list_apps" in caplog.text


def test_http_invoke_param_error_still_400():
    """入参错误仍是 4xx，不被内部故障的 5xx 吞并。"""
    user = User.objects.create_user(username="param_user", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/platform-tools/list_devices/invoke/",
        data={"nope": 1},
        content_type="application/json",
        **_auth_headers(user),
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] is False
    assert "未知参数" in body["message"]
