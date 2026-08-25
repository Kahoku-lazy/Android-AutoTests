"""device_inspector 结构分析 — service/api 单测（纯逻辑，无 DB / 无设备 IO）。"""

from types import SimpleNamespace

import pytest

from apps.device_inspector import api as api_module
from apps.device_inspector import service as service_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _snapshot(dump_json, screen_h=3040):
    return SimpleNamespace(
        package="com.govee.home",
        activity=".main.MainTabActivity",
        screen_h=screen_h,
        dump_json=dump_json,
    )


def _el(**kw):
    base = {
        "class_name": "android.view.ViewGroup",
        "text": "",
        "content_desc": "",
        "resource_id": "",
        "package": "com.govee.home",
        "index": "0",
        "bounds": "[0,0][0,0]",
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
        "clickable": False,
        "scrollable": False,
        "checkable": False,
    }
    base.update(kw)
    return base


class TestAnalyzeSnapshotPayload:
    def test_empty_dump(self):
        result = service_module.analyze_snapshot_payload(_snapshot({}))
        assert result == {
            "package": "com.govee.home",
            "activity": ".main.MainTabActivity",
            "is_webview": False,
            "sections": [],
            "elements": [],
        }

    def test_classifies_elements(self):
        els = [
            _el(
                package="com.android.systemui",
                class_name="android.widget.TextView",
                y=33,
                height=117,
            ),
            _el(class_name="android.widget.TextView", text="设备", y=110, height=211),
            _el(
                class_name="android.widget.ImageView",
                resource_id="x:id/ivSwitch",
                y=901,
                height=150,
                clickable=True,
            ),
        ]
        result = service_module.analyze_snapshot_payload(_snapshot({"elements": els}))
        roles = {s["role"] for s in result["sections"]}
        assert {"status_bar", "header", "content"} <= roles
        assert result["is_webview"] is False

    def test_preserves_existing_xpaths(self):
        e = _el(class_name="android.widget.TextView", text="设备", y=110, height=211)
        e["xpaths"] = [
            {"type": "text", "xpath": "//android.widget.TextView[@text='设备']", "count": 1}
        ]
        result = service_module.analyze_snapshot_payload(_snapshot({"elements": [e]}))
        out = result["elements"][0]
        assert out["xpaths"] == e["xpaths"]  # XPath 原样保留，不重复生成
        assert out["role"] == "header"
        assert out["metrics"] == []

    def test_webview_detected(self):
        els = [_el(class_name="android.webkit.WebView", y=1, height=2500)]
        result = service_module.analyze_snapshot_payload(_snapshot({"elements": els}))
        assert result["is_webview"] is True


class TestAnalyzeSnapshotApi:
    def test_not_found_returns_none(self, monkeypatch):
        from apps.device_inspector import models as di_models

        class _Query:
            def first(self):
                return None

        monkeypatch.setattr(
            di_models,
            "Snapshot",
            SimpleNamespace(objects=SimpleNamespace(filter=lambda **k: _Query())),
        )
        assert api_module.analyze_snapshot(999) is None
