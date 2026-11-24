"""
模块功能：➡️ 通信通道架构契约测试 — 单文件，按类区分四条通道 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_channels.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/gateway/middleware.py、backend/gateway/routing.py
🏁
"""

import re

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

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
        content = (ROOT / "backend" / "config" / "urls.py").read_text(encoding="utf-8")
        for m in re.finditer(r'path\("([^"]+)",\s*include\("backend\.apps\.', content):
            assert m.group(1).startswith("api/"), f"业务路由 {m.group(1)!r} 未挂 /api/ 前缀"

    def test_public_prefixes_no_business_routes(self):
        """JWT 白名单不得含业务路由（含业务前缀 = 认证绕过）。"""
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
    """② Django → 前端 — WebSocket + JWT"""

    def test_ws_routing_is_empty(self):
        """知识助手语音下线后不再有 WS 生产点；新增须先走 OpenSpec。"""
        from backend.gateway.routing import websocket_urlpatterns

        patterns = [str(pattern.pattern) for pattern in websocket_urlpatterns]
        assert patterns == [], f"当前不应有任何 WS 生产点，实际 {patterns}"


class TestAgentScopeChannel:
    """③ AgentScope → Django — 进程内直接调用"""

    def test_agent_scope_no_adapters(self):
        """AgentScope 引擎不得自建数据库适配器（adapters/）。

        引擎层现行目录为 `engines/agents`（角色 / 消息与事件 / 工具 / 工作流 /
        提示词 / 技能 / MCP 配置）；禁止项覆盖引擎根与其每个子包。
        `rag/` 是引擎自己的能力目录（见 `engines/agents/rag/AGENTS.md`），不在禁止之列。
        """
        root = ROOT / "engines" / "agents"
        assert root.is_dir(), "engines/agents 引擎目录不存在"
        assert not (root / "agentscope").exists(), (
            "禁止再出现 engines/agents/agentscope（框架实现在 engines/agents/role）"
        )
        assert not (root / "adapters").exists(), "engines/agents 下禁止新增 adapters/"
        for part in ("role", "messaging", "tools", "workflow", "prompts", "skills"):
            base = root / part
            assert not (base / "adapters").exists(), f"engines/agents/{part} 下禁止新增 adapters/"
            assert not (base / "rag").exists(), f"engines/agents/{part} 下禁止新增 rag/"


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
        for scan_dir in ("backend/apps", "backend/gateway"):
            for py in (ROOT / scan_dir).rglob("*.py"):
                if "migrations" in str(py) or "__pycache__" in str(py):
                    continue
                content = py.read_text(encoding="utf-8")
                for pat in forbidden:
                    assert pat not in content, f"{py.relative_to(ROOT)} 上层直触引擎：{pat}"
