"""设备检查器 AI 工具 — schema / handler / AI 裁剪 单元测试（v6.5）。"""

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def test_capture_page_schema_registered():
    """capture_page：inspector/capture，只读，设备检查器分类。"""
    schema = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "capture_page")
    assert schema["module"] == "inspector"
    assert schema["action"] == "capture"
    assert schema["read_only"] is True
    assert schema["category"] == "设备检查器"
    assert any(p["name"] == "serial" and p["required"] for p in schema["params"])


def test_save_page_to_elements_schema_registered():
    """save_page_to_elements：inspector/save_elements，写工具。"""
    schema = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "save_page_to_elements")
    assert schema["module"] == "inspector"
    assert schema["action"] == "save_elements"
    assert schema["read_only"] is False
    assert {p["name"] for p in schema["params"] if p.get("required")} == {
        "snapshot_id",
        "page_label",
    }


def test_schema_count_is_30():
    """平台工具总数 30（26 + 执行状态 get_run_status + 页面结构分析 analyze_page/save_page_semantic + 预存新增 2 个）。"""
    assert len(tool_registry.TOOL_SCHEMAS) == 30


def test_inspector_category_registered():
    """「设备检查器」分类存在。"""
    assert any(c["key"] == "设备检查器" for c in tool_registry.TOOL_CATEGORIES)


def test_resolve_inspector_handlers():
    assert tool_registry.resolve("inspector", "capture") is not None
    assert tool_registry.resolve("inspector", "save_elements") is not None


def test_trim_capture_for_ai_strips_thumbnails_and_caps():
    """AI 通道：texts 去缩略图、actionable 上限 50。"""
    texts = [
        {
            "text": "欢迎",
            "confidence": 0.9,
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 40,
            "thumbnail_path": "inspector/thumbs/x/ocr_0.png",
        },
    ]
    data = {
        "snapshot_id": 1,
        "serial": "A",
        "method": "both",
        "package": "com.demo",
        "activity": "Main",
        "element_count": 100,
        "actionable_count": 60,
        "actionable": [{"text": f"e{i}", "xpaths": []} for i in range(60)],
        "ocr_count": 1,
        "texts": texts,
        "screenshot_path": "inspector/shots/a.png",
    }
    out = tool_registry._trim_capture_for_ai(data)
    assert len(out["actionable"]) == 50
    assert len(out["texts"]) == 1
    assert "thumbnail_path" not in out["texts"][0]
    assert out["snapshot_id"] == 1 and out["element_count"] == 100


def test_save_handler_calls_inspector_api(monkeypatch):
    """save handler 透传参数到 device_inspector.api.save_snapshot_to_elements。"""
    from apps.device_inspector import api as inspector_api

    captured = {}

    def fake_save(snapshot_id, page_label, folder_path="", include_ocr=True):
        captured.update(
            snapshot_id=snapshot_id,
            page_label=page_label,
            folder_path=folder_path,
            include_ocr=include_ocr,
        )
        return {"saved": 1, "updated": 0, "skipped": 0, "page_id": 7}

    monkeypatch.setattr(inspector_api, "save_snapshot_to_elements", fake_save)

    handler = tool_registry.resolve("inspector", "save_elements")
    result = handler("1", snapshot_id=5, page_label="登录页", folder_path="AI/冒烟")
    assert result == {"saved": 1, "updated": 0, "skipped": 0, "page_id": 7}
    assert captured == {
        "snapshot_id": 5,
        "page_label": "登录页",
        "folder_path": "AI/冒烟",
        "include_ocr": True,
    }
