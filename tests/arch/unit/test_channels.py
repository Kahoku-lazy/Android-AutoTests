import re

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

pytestmark = [pytest.mark.unit, pytest.mark.arch]


class TestHttpChannel:
    def test_api_client_base_url_is_api(self):
        content = (ROOT / "frontend" / "src" / "shared" / "api-client.ts").read_text(
            encoding="utf-8"
        )
        assert 'baseURL: "/api"' in content

    def test_all_app_includes_under_api_prefix(self):
        content = (ROOT / "backend" / "config" / "urls.py").read_text(encoding="utf-8")
        for m in re.finditer(r'path\("([^"]+)",\s*include\("backend\.apps\.', content):
            assert m.group(1).startswith("api/"), f"业务路由 {m.group(1)!r} 未挂 /api/ 前缀"

    def test_public_prefixes_no_business_routes(self):
        from backend.gateway.middleware import PUBLIC_PREFIXES

        business = [
            "/api/dashboard",
            "/api/devices",
            "/api/cases",
            "/api/runner",
            "/api/reports",
            "/api/evaluator",
            "/api/inspector",
            "/api/elements",
        ]
        for b in business:
            assert b not in PUBLIC_PREFIXES, f"{b} 被误列为公开路径（绕过 JWT）"


class TestWebSocketChannel:
    def test_ws_routing_is_empty(self):
        from backend.gateway.routing import websocket_urlpatterns

        patterns = [str(pattern.pattern) for pattern in websocket_urlpatterns]
        assert patterns == [], f"当前不应有任何 WS 生产点，实际 {patterns}"


class TestEngineChannel:
    def test_upper_layers_do_not_import_engine_libs(self):
        forbidden = (
            "import uiautomator2",
            "from uiautomator2",
            "from engines.device.android",
            "import engines.device.android",
        )
        for scan_dir in ("backend/apps", "backend/gateway"):
            for py in (ROOT / scan_dir).rglob("*.py"):
                if "migrations" in str(py) or "__pycache__" in str(py):
                    continue
                content = py.read_text(encoding="utf-8")
                for pat in forbidden:
                    assert pat not in content, f"{py.relative_to(ROOT)} 上层直触引擎：{pat}"
