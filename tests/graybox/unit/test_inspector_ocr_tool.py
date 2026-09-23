"""设备检查器 OCR 工具：结果契约、中心点归一化、让路约束与工具箱注册。

spec: ai-screen-vision（智能体可读取当前页面文本坐标）。

识别依赖 cnocr 重模型、截屏依赖真实设备，故此处以桩替换 `recognize` 与
`PIL.Image.open`，只对**结果契约与归一化**下断言：零 I/O、不加载模型。
"""

from __future__ import annotations

import sys
import types

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from PIL import Image

from apps.device_inspector.api import ocr_screen
from apps.device_inspector.service import CaptureError, ocr_page_payload
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.device_inspector]

User = get_user_model()

# 与实测一致的一条 cnocr 结果：文本 + 置信度 + 原始角点（左上→右上→右下→左下）
_REGION = {
    "text": "设备",
    "confidence": 0.9996,
    "x": 49,
    "y": 109,
    "width": 116,
    "height": 66,
    "bounds": "[49,109][165,175]",
    "coordinates": [[49, 109], [165, 175]],
}


def _stub_recognize(monkeypatch, regions: list[dict]) -> None:
    """用桩模块替换 algorithms.vision.ocr，避免加载 cnocr 模型。"""
    stub = types.ModuleType("algorithms.vision.ocr")
    stub.recognize = lambda _path: regions
    monkeypatch.setitem(sys.modules, "algorithms.vision.ocr", stub)


def _stub_image_size(monkeypatch, size: tuple[int, int]) -> None:
    """替换 PIL.Image.open，让截图像素尺寸可控（不落任何文件）。"""

    class _FakeImage:
        def __init__(self):
            self.size = size

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

    monkeypatch.setattr(Image, "open", lambda _p: _FakeImage())


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


# ── 结果契约与中心点归一化 ──


def test_ocr_page_payload_returns_text_confidence_coordinates_center(monkeypatch):
    _stub_recognize(monkeypatch, [dict(_REGION)])
    _stub_image_size(monkeypatch, (1080, 2340))

    payload = ocr_page_payload("ignored.png")

    assert payload["screen_w"] == 1080
    assert payload["screen_h"] == 2340
    assert len(payload["texts"]) == 1
    item = payload["texts"][0]
    assert sorted(item) == ["center", "confidence", "coordinates", "text"]
    assert item["text"] == "设备"
    assert isinstance(item["confidence"], float)
    assert item["coordinates"] == [[49, 109], [165, 175]]
    # 包围盒中心 (49+165)/2=107、(109+175)/2=142，分母取截图像素尺寸
    assert item["center"] == [round(107 / 1080, 4), round(142 / 2340, 4)]


def test_ocr_page_payload_center_is_normalized_0_to_1_floats(monkeypatch):
    _stub_recognize(monkeypatch, [dict(_REGION)])
    _stub_image_size(monkeypatch, (1080, 2340))

    center = ocr_page_payload("ignored.png")["texts"][0]["center"]

    assert all(0 <= axis <= 1 for axis in center)
    assert all(isinstance(axis, float) for axis in center)
    # 保留 4 位小数（1080 宽下 1e-4 约 0.11px，足够点击）
    assert center == [round(axis, 4) for axis in center]


def test_ocr_page_payload_coordinates_are_two_diagonal_points(monkeypatch):
    """坐标只给左上/右下两个对角点，不再输出四个角点。"""
    _stub_recognize(monkeypatch, [dict(_REGION)])
    _stub_image_size(monkeypatch, (1080, 2340))

    coordinates = ocr_page_payload("ignored.png")["texts"][0]["coordinates"]

    assert coordinates == [[49, 109], [165, 175]]
    assert all(isinstance(point, list) and len(point) == 2 for point in coordinates)
    assert all(isinstance(n, int) for point in coordinates for n in point)


def test_ocr_page_payload_center_is_midpoint_of_the_two_diagonal_points(monkeypatch):
    _stub_recognize(monkeypatch, [dict(_REGION)])
    _stub_image_size(monkeypatch, (1080, 2340))

    item = ocr_page_payload("ignored.png")["texts"][0]
    (x1, y1), (x2, y2) = item["coordinates"]
    expected = [round((x1 + x2) / 2 / 1080, 4), round((y1 + y2) / 2 / 2340, 4)]

    assert item["center"] == expected


def test_ocr_page_payload_empty_page_returns_zero_texts(monkeypatch):
    _stub_recognize(monkeypatch, [])
    _stub_image_size(monkeypatch, (1080, 2340))

    assert ocr_page_payload("ignored.png")["texts"] == []


def test_ocr_page_payload_rejects_zero_screen_instead_of_zero_division(monkeypatch):
    _stub_recognize(monkeypatch, [dict(_REGION)])
    _stub_image_size(monkeypatch, (0, 0))

    with pytest.raises(CaptureError, match="尺寸"):
        ocr_page_payload("ignored.png")


def test_ocr_page_payload_rejects_region_without_corners(monkeypatch):
    _stub_recognize(monkeypatch, [{**_REGION, "coordinates": []}])
    _stub_image_size(monkeypatch, (1080, 2340))

    with pytest.raises(CaptureError, match="角点"):
        ocr_page_payload("ignored.png")


# ── 多文本过滤（texts 入参） ──


def _regions(*labels: str) -> list[dict]:
    return [{**_REGION, "text": label} for label in labels]


def _filtered_texts(monkeypatch, regions: list[dict], texts: str) -> list[str]:
    _stub_recognize(monkeypatch, regions)
    _stub_image_size(monkeypatch, (1080, 2340))
    return [t["text"] for t in ocr_page_payload("ignored.png", texts)["texts"]]


def test_ocr_page_payload_without_texts_returns_everything(monkeypatch):
    got = _filtered_texts(monkeypatch, _regions("设置", "WiFi", "电量"), "")
    assert got == ["设置", "WiFi", "电量"]


def test_ocr_page_payload_filters_single_text(monkeypatch):
    assert _filtered_texts(monkeypatch, _regions("设置", "WiFi", "电量"), "WiFi") == ["WiFi"]


def test_ocr_page_payload_filters_multiple_texts_with_or_semantics(monkeypatch):
    got = _filtered_texts(monkeypatch, _regions("设置", "WiFi", "电量"), "设置,电量")
    assert got == ["设置", "电量"]


def test_ocr_page_payload_filter_is_case_insensitive_substring(monkeypatch):
    # 子串 + 忽略大小写：小写 wifi 命中 WiFi，「设置」命中「设置中心」
    assert _filtered_texts(monkeypatch, _regions("WiFi", "设置中心"), "wifi") == ["WiFi"]
    assert _filtered_texts(monkeypatch, _regions("WiFi", "设置中心"), "设置") == ["设置中心"]


def test_ocr_page_payload_filter_accepts_comma_enumeration_and_newline(monkeypatch):
    regions = _regions("设置", "WiFi", "电量")
    assert _filtered_texts(monkeypatch, regions, "设置、电量") == ["设置", "电量"]
    assert _filtered_texts(monkeypatch, regions, "设置，电量") == ["设置", "电量"]
    assert _filtered_texts(monkeypatch, regions, "设置\n电量\nWiFi") == ["设置", "WiFi", "电量"]


def test_ocr_page_payload_filter_ignores_blank_and_duplicate_keywords(monkeypatch):
    got = _filtered_texts(monkeypatch, _regions("设置", "WiFi"), " , 设置 ,设置, WiFi , ")
    assert got == ["设置", "WiFi"]


def test_ocr_page_payload_filter_without_hit_returns_empty(monkeypatch):
    assert _filtered_texts(monkeypatch, _regions("设置", "WiFi"), "不存在的文本") == []


def test_ocr_page_payload_filter_keeps_match_fields(monkeypatch):
    _stub_recognize(monkeypatch, _regions("设置", "WiFi"))
    _stub_image_size(monkeypatch, (1080, 2340))

    item = ocr_page_payload("ignored.png", "WiFi")["texts"][0]

    assert sorted(item) == ["center", "confidence", "coordinates", "text"]
    assert item["coordinates"] == _REGION["coordinates"]


# ── 编排：截完即还设备、截图用完即删 ──


def test_ocr_screen_closes_engine_before_ocr_and_deletes_shot(monkeypatch):
    events: list[str] = []
    engine = object()

    monkeypatch.setattr(
        "apps.device_inspector.service.open_inspector_engine", lambda serial: engine
    )
    monkeypatch.setattr(
        "apps.device_inspector.service.capture_page_screenshot",
        lambda _engine, ts: f"inspector/shots/capture_{ts}.png",
    )

    def _payload(path: str, texts: str = "") -> dict:
        events.append(f"ocr:{texts}:{path}")
        return {"screen_w": 1080, "screen_h": 2340, "texts": []}

    monkeypatch.setattr("apps.device_inspector.service.ocr_page_payload", _payload)
    monkeypatch.setattr(
        "engines.device.registry.close_engine",
        lambda eng: events.append("close") if eng is engine else None,
    )
    monkeypatch.setattr(
        "apps.device_inspector.api._cleanup_capture_files", lambda ts: events.append("cleanup")
    )

    result = ocr_screen("SERIAL-1", "设置,WiFi")

    # 设备在 OCR 之前就已归还（OCR 不需要设备）
    assert events[0] == "close"
    # texts 过滤入参原样透传到识别层
    assert events[1].startswith("ocr:设置,WiFi:")
    # 契约只回 JSON 不回图片：截图文件在识别后被清理
    assert events[2] == "cleanup"
    assert result["serial"] == "SERIAL-1"
    assert result["count"] == 0


def test_ocr_screen_cleans_shot_even_when_ocr_fails(monkeypatch):
    events: list[str] = []

    monkeypatch.setattr(
        "apps.device_inspector.service.open_inspector_engine", lambda serial: object()
    )
    monkeypatch.setattr(
        "apps.device_inspector.service.capture_page_screenshot",
        lambda _engine, ts: f"inspector/shots/capture_{ts}.png",
    )

    def _boom(_path: str, texts: str = "") -> dict:
        raise CaptureError("OCR 失败", status_code=500)

    monkeypatch.setattr("apps.device_inspector.service.ocr_page_payload", _boom)
    monkeypatch.setattr("engines.device.registry.close_engine", lambda _eng: None)
    monkeypatch.setattr(
        "apps.device_inspector.api._cleanup_capture_files", lambda ts: events.append("cleanup")
    )

    with pytest.raises(CaptureError):
        ocr_screen("SERIAL-1")

    assert events == ["cleanup"]


# ── 设备可用性让路约束 ──


@pytest.mark.django_db
def test_ocr_screen_rejects_unregistered_device():
    with pytest.raises(CaptureError, match="设备未注册"):
        ocr_screen("no-such-serial")


@pytest.mark.django_db
def test_ocr_screen_rejects_device_occupied_by_executor():
    from apps.device_pool.models import Device

    Device.objects.create(serial="OCR-BUSY1", status="BUSY", occupied_by="runner-42")

    with pytest.raises(CaptureError, match="执行引擎占用"):
        ocr_screen("OCR-BUSY1")


# ── 工具箱注册 ──


def test_ocr_page_registered_as_read_only_vision_tool():
    from apps.ai_assistant.tools import (
        AUTO_ALLOW_TOOLS,
        TOOLS,
        get_tool_debug_schema,
        list_tool_schemas,
    )

    _func, read_only = TOOLS["ocr_page"]
    assert read_only is True
    # OCR 无设备副作用，不属「设备控制类自动放行」名单
    assert "ocr_page" not in AUTO_ALLOW_TOOLS

    # texts 过滤入参经 docstring + 注解推导进调试表单（非必填、类型 str）
    debug = get_tool_debug_schema("ocr_page")
    params = {p["name"]: p for p in debug["parameters"]}
    assert set(params) == {"serial", "texts"}
    assert params["serial"]["required"] is True
    assert params["texts"]["type"] == "str"
    assert params["texts"]["required"] is False

    schema = next(s for s in list_tool_schemas() if s["name"] == "ocr_page")
    assert schema["category"] == "视觉识别工具"
    assert schema["read_only"] is True
    assert schema["icon"] == "🔍"
    assert schema["module"] == "inspector"
    assert schema["action"] == "ocr"


def test_vision_category_registered_with_distinct_color():
    from apps.ai_assistant.tools import TOOL_CATEGORIES, TOOL_META, resolve_by_module_action

    assert TOOL_META["ocr_page"] == ("视觉识别工具", "inspector", "ocr")
    assert resolve_by_module_action("inspector", "ocr").__name__ == "ocr_page"

    colors = [c["color"] for c in TOOL_CATEGORIES]
    assert len(set(colors)) == len(colors)
    assert {"key": "视觉识别工具", "icon": "🔍", "color": "#A78BFA"} in TOOL_CATEGORIES


@pytest.mark.django_db
def test_available_tools_endpoint_exposes_vision_category():
    user = User.objects.create_user(username="ocr-tools-reader", password="x")
    resp = Client().get("/api/ai/available-tools/", **_auth_headers(user))

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    categories = {c["key"]: c for c in body["data"]["categories"]}
    assert "视觉识别工具" in categories
    vision = categories["视觉识别工具"]
    assert vision["icon"] == "🔍"
    assert "ocr_page" in {t["name"] for t in vision["tools"]}


@pytest.mark.django_db
def test_toggle_vision_category_disables_then_restores_ocr_page():
    admin = User.objects.create_superuser(username="ocr-tools-admin", password="x")
    client = Client()
    toggle_url = "/api/ai/platform-tools/toggle/"

    def _vision_tools():
        listed = client.get("/api/ai/available-tools/", **_auth_headers(admin)).json()
        categories = {c["key"]: c for c in listed["data"]["categories"]}
        return categories["视觉识别工具"]["tools"]

    off = client.post(
        toggle_url,
        {"category": "视觉识别工具", "enabled": False},
        content_type="application/json",
        **_auth_headers(admin),
    )
    assert off.status_code == 200
    assert "ocr_page" in off.json()["data"]["updated"]
    assert [t["enabled"] for t in _vision_tools()] == [False]

    on = client.post(
        toggle_url,
        {"category": "视觉识别工具", "enabled": True},
        content_type="application/json",
        **_auth_headers(admin),
    )
    assert on.status_code == 200
    assert [t["enabled"] for t in _vision_tools()] == [True]
