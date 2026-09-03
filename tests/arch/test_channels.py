"""通信通道架构契约测试 — 单文件，按类区分四条通道。

校验「四条内部通信通道」的结构不变量（architecture.md §一 逐通道规则）：
  - ① HTTP REST + JWT：前端唯一出口 baseURL、后端业务路由挂 /api/、JWT 白名单无业务路由
  - ② WebSocket + JWT：路由真相源恒 2 个生产点
  - ③ AgentScope 进程内：无 adapters/、rag/
  - ④ 引擎中转：上层（apps/gateway）不直触引擎库/具体实现

运行：pytest tests/arch/test_channels.py -v   或   pytest -m arch -v
"""

import re

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [pytest.mark.unit, pytest.mark.arch]


class TestHttpChannel:
    """① 前端 ↔ Django — HTTP REST + JWT"""

    def test_api_client_base_url_is_api(self):
        """前端唯一出口必须指向后端 /api 前缀（契约锚点）。"""
        content = (ROOT / "frontend" / "src" / "shared" / "api-client.ts").read_text(
            encoding="utf-8"
        )
        assert 'baseURL: "/api"' in content

    def test_all_app_includes_under_api_prefix(self):
        """后端所有业务 include 必须挂 /api/ 前缀（否则绕过 JWT 中间件）。"""
        content = (ROOT / "config" / "urls.py").read_text(encoding="utf-8")
        for m in re.finditer(r'path\("([^"]+)",\s*include\("apps\.', content):
            assert m.group(1).startswith("api/"), f"业务路由 {m.group(1)!r} 未挂 /api/ 前缀"

    def test_public_prefixes_no_business_routes(self):
        """JWT 白名单不得含业务路由（含业务前缀 = 认证绕过）。"""
        from gateway.middleware import PUBLIC_PREFIXES

        business = [
            "/api/dashboard",
            "/api/devices",
            "/api/cases",
            "/api/runner",
            "/api/reports",
            "/api/workflow",
            "/api/evaluator",
            "/api/inspector",
            "/api/elements",
        ]
        for b in business:
            assert b not in PUBLIC_PREFIXES, f"{b} 被误列为公开路径（绕过 JWT）"


class TestWebSocketChannel:
    """② Django → 前端 — WebSocket + JWT"""

    def test_ws_routing_has_exactly_two(self):
        """WS 路由真相源恒 2 个生产点（执行进度 + 编辑锁），禁止新增。"""
        from gateway.routing import websocket_urlpatterns

        assert len(websocket_urlpatterns) == 2, (
            f"WS 生产点应为 2 个，实际 {len(websocket_urlpatterns)}"
        )


class TestAgentScopeChannel:
    """③ AgentScope → Django — 进程内直接调用"""

    def test_agent_scope_no_adapters_or_rag(self):
        """AgentScope 引擎不得自建数据库适配器（adapters/）或检索增强（rag/）。"""
        scope = ROOT / "engines" / "ai" / "agentscope"
        assert scope.is_dir(), "engines/ai/agentscope 目录不存在"
        assert not (scope / "adapters").exists(), "engines/ai/agentscope 下禁止新增 adapters/"
        assert not (scope / "rag").exists(), "engines/ai/agentscope 下禁止新增 rag/"


class TestEngineChannel:
    """④ Django ↔ 设备 — 引擎中转（UiEngine 协议）"""

    def test_upper_layers_do_not_import_engine_libs(self):
        """上层（apps/gateway）不得直触引擎库或具体引擎实现。"""
        forbidden = (
            "import uiautomator2",
            "from uiautomator2",
            "from engines.device.android",
            "import engines.device.android",
        )
        for scan_dir in ("apps", "gateway"):
            for py in (ROOT / scan_dir).rglob("*.py"):
                if "migrations" in str(py) or "__pycache__" in str(py):
                    continue
                content = py.read_text(encoding="utf-8")
                for pat in forbidden:
                    assert pat not in content, f"{py.relative_to(ROOT)} 上层直触引擎：{pat}"
