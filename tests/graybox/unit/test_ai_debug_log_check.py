"""灰盒·单元测试 — 调试台的点击证据与 5 秒日志检查（spec: ai-model-debug）。

断言四件事：
1. 本轮有点击 → 响应带 `log_check`（点击前时间点 + 点击后截图路径 + 同一份窗口证据）；
2. 开窗发生在把内容交给角色**之前**，读窗用同一个 window_id 与各点击时刻；
3. 本轮没有点击 → 不产出该键（不渲染空壳）；
4. 没有端口在监听（提供者为 None）→ 点击证据照旧、日志为空，且不打开任何端口。
"""

from __future__ import annotations

import types

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import model_debug
from apps.ai_assistant.api import encrypt_key
from apps.ai_assistant.models import AIAgent
from engines.ai.agentscope.config import ModelConfig
from engines.ai.agentscope.model import RoleResult
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()

CLICK_TIME = "2026-09-28 10:51:03.219"
SHOT = "ai_tasks/debug/s1.jpg"

EVIDENCE = {
    "conclusion": "hit",
    "channel": "H6810",
    "threshold_seconds": 5.0,
    "window_line_count": 3,
    "hits": [{"keyword": "switch_off", "grade": "strong", "count": 1}],
}


class _Recorder:
    """桩提供者：记录调用顺序与入参，返回固定证据。"""

    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.opened: list[tuple] = []
        self.reads: list[tuple] = []

    def open_window(self, device: str, label: str = "") -> str:
        self.order.append("open")
        self.opened.append((device, label))
        return "w-debug"

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict:
        self.order.append("read")
        self.reads.append((device, window_id, list(action_times or [])))
        return dict(EVIDENCE)


def _click_row(action_time: str = CLICK_TIME) -> dict:
    return {
        "type": "result",
        "name": "xpath_action",
        "state": "success",
        "output": f'{{"clicked": true, "action_time": "{action_time}"}}',
    }


def _shot_row(path: str = SHOT) -> dict:
    return {"type": "result", "name": "screenshot_page", "output": "{}", "screenshot_path": path}


class _FakeRole:
    """桩角色：ask() 时记一笔顺序，返回构造好的工具轨迹。"""

    def __init__(self, rows: list[dict], order: list[str]):
        self._rows = rows
        self._order = order

    async def ask(self, content: str) -> RoleResult:
        self._order.append("ask")
        return RoleResult(
            role="executor",
            model_name="stub-model",
            output="已点击开关",
            tool_usage=self._rows,
        )


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="dlc_admin", password="x")


def _route_cfg() -> dict:
    role = {"provider": "deepseek", "model_name": "deepseek-chat", "api_key": encrypt_key("k")}
    return {
        "device_control": {"planner": dict(role), "executor": dict(role), "verifier": dict(role)}
    }


@pytest.fixture
def agent(admin):
    return AIAgent.objects.create(
        owner=admin,
        name="调试智能体",
        prompt_planner="P",
        prompt_executor="E",
        prompt_verifier="V",
        route_configs=_route_cfg(),
    )


def _patch_layer(monkeypatch, order: list[str], rows: list[dict]) -> None:
    cfg = ModelConfig(provider="deepseek", model_name="stub", api_key="k", base_url="http://stub")
    monkeypatch.setattr(
        model_debug,
        "build_device_models_for_agent",
        lambda agent: (
            types.SimpleNamespace(planner=cfg, executor=cfg, verifier=cfg),
            None,
            None,
            None,
        ),
    )
    monkeypatch.setattr(
        model_debug,
        "build_debug_role",
        lambda agent, role, model_cfg, user_id="": _FakeRole(rows, order),
    )
    monkeypatch.setattr(
        model_debug,
        "available_device_options",
        lambda user_id: [{"value": "DEV-1", "label": "DEV-1 (stub)"}],
    )


def test_chat_carries_clicks_and_same_window_evidence(agent, monkeypatch):
    order: list[str] = []
    _patch_layer(monkeypatch, order, [_click_row(), _shot_row()])
    provider = _Recorder(order)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: provider)

    payload = model_debug.run_role_chat(agent, "executor", "点一下开关", serial="DEV-1")

    block = payload["log_check"]
    assert block["clicks"] == [{"action_time": CLICK_TIME, "screenshot_path": SHOT}]
    assert block["log"]["hits"][0]["keyword"] == "switch_off"
    # 开窗必须在交给角色之前，读窗用同一个窗口与各点击时刻
    assert order == ["open", "ask", "read"]
    assert provider.opened == [("DEV-1", "model-debug")]
    assert provider.reads == [("DEV-1", "w-debug", [CLICK_TIME])]


def test_chat_without_click_has_no_log_check(agent, monkeypatch):
    order: list[str] = []
    read_only = {"type": "result", "name": "current_app", "output": '{"package": "com.demo"}'}
    _patch_layer(monkeypatch, order, [read_only])
    provider = _Recorder(order)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: provider)

    payload = model_debug.run_role_chat(agent, "executor", "看一眼前台应用", serial="DEV-1")

    assert "log_check" not in payload
    assert provider.reads == []


def test_chat_without_listening_port_keeps_clicks_without_log(agent, monkeypatch):
    order: list[str] = []
    _patch_layer(monkeypatch, order, [_click_row(), _shot_row()])
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)

    payload = model_debug.run_role_chat(agent, "executor", "点一下开关", serial="DEV-1")

    block = payload["log_check"]
    assert block["clicks"][0]["action_time"] == CLICK_TIME
    assert block["log"] is None


def test_window_is_opened_before_any_device_action(agent, monkeypatch):
    """开窗早于 ask：即便这一轮没有点击，顺序也必须是开窗在前（与生产同口径）。"""
    order: list[str] = []
    _patch_layer(monkeypatch, order, [_click_row()])
    provider = _Recorder(order)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: provider)

    model_debug.run_role_chat(agent, "executor", "点一下开关", serial="DEV-1")

    assert order.index("open") < order.index("ask")


def test_chat_endpoint_passes_log_check_through(client, admin, agent, monkeypatch):
    """端点不透支契约：响应信封里能看到该块。"""
    order: list[str] = []
    _patch_layer(monkeypatch, order, [_click_row(), _shot_row()])
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: _Recorder(order))

    resp = client.post(
        "/api/ai/model-debug/executor/chat/",
        data={"text": "点开关", "serial": "DEV-1"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["log_check"]["clicks"][0]["action_time"] == CLICK_TIME
    assert data["log_check"]["log"]["conclusion"] == "hit"
