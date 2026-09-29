"""灰盒·单元测试 — 调试台的点击证据、5 秒日志检查与验收角色的日志证据（spec: ai-model-debug）。

断言六件事：
1. 本轮有点击 → 响应带 `log_check`（点击前时间点 + 点击后截图路径 + 同一份窗口证据）；
2. 开窗发生在把内容交给角色**之前**，读窗用同一个 window_id 与各点击时刻；
3. 本轮没有点击 → 不产出该键（不渲染空壳）；
4. 没有端口在监听（提供者为 None）→ 点击证据照旧、日志为空，且不打开任何端口；
5. **验收角色**的输入由平台附上「设备日志证据 · 调试回溯」（基准取消息里第一个毫秒时间戳；
   没有则退回最近窗并标明来源），响应带 `log_evidence` 与 `log_basis`；
6. 执行角色不受影响，且端口监听关着时验收对话如实说明没有日志、不打开端口。
"""

from __future__ import annotations

import json
import types

from pathlib import Path

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import model_debug
from apps.ai_assistant.api import encrypt_key
from apps.ai_assistant.log_history import NOTE_NO_LISTEN
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


class _PromptRole:
    """桩角色：记录收到的输入文本（验收角色要断言平台有没有喂日志证据）。"""

    def __init__(self, prompts: list[str], order: list[str]):
        self._prompts = prompts
        self._order = order

    async def ask(self, content: str) -> RoleResult:
        self._order.append("ask")
        self._prompts.append(str(content))
        return RoleResult(
            role="verifier", model_name="stub-model", output='{"result": "PASS"}', tool_usage=[]
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


def _patch_layer(
    monkeypatch, order: list[str], rows: list[dict], prompts: list[str] | None = None
) -> None:
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
    role_factory = (
        (lambda agent, role, model_cfg, user_id="": _PromptRole(prompts, order))
        if prompts is not None
        else (lambda agent, role, model_cfg, user_id="": _FakeRole(rows, order))
    )
    monkeypatch.setattr(model_debug, "build_debug_role", role_factory)
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


# ── 验收角色的「设备日志证据 · 调试回溯」──

BASIS = "2026-09-29 11:47:04.326"


@pytest.fixture
def log_env(tmp_path: Path, settings):
    """临时日志目录 + 关键词表 + 单个端口来源（H6810/7005）。"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "H6810_7005.log").write_text(
        "2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_on\n", encoding="utf-8"
    )
    keyword_file = tmp_path / "keywords.json"
    keyword_file.write_text(
        json.dumps(
            {
                "keywords": {
                    "switch_on": [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    settings.DEVICE_LOG_LOG_DIR = str(log_dir)
    settings.DEVICE_LOG_KEYWORD_FILE = str(keyword_file)
    settings.DEVICE_LOG_SOURCES = json.dumps({"7005": {"sku": "H6810"}})
    settings.DEVICE_LOG_WINDOW_SECONDS = 5.0
    settings.DEVICE_LOG_BASELINE_SECONDS = 30.0
    return log_dir


def test_verifier_chat_input_carries_log_evidence(agent, monkeypatch, log_env):
    """验收对话：平台按消息里的时刻取日志证据喂进模型输入，并回传证据与基准。"""
    order: list[str] = []
    prompts: list[str] = []
    _patch_layer(monkeypatch, order, [], prompts=prompts)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)

    payload = model_debug.run_role_chat(
        agent, "verifier", f"验证：设备已打开\n点击时刻 {BASIS}", serial="DEV-1"
    )

    prompt = prompts[0]
    assert "【设备日志证据 · 调试回溯】" in prompt
    assert BASIS in prompt
    assert "switch_on" in prompt
    assert "logAssertionTimer" in prompt  # 取值指引也在输入里
    assert payload["log_basis"]["from_message"] is True
    assert payload["log_basis"]["basis_time"] == BASIS
    assert payload["log_basis"]["files"][0].endswith("H6810_7005.log")
    assert payload["log_evidence"]["hits"][0]["keyword"] == "switch_on"
    # 该角色自己没有日志工具，因此不产生点击证据块
    assert "log_check" not in payload


def test_verifier_chat_without_time_falls_back_to_recent_window(agent, monkeypatch, log_env):
    """消息里没有时刻：退回最近一个取证窗，并标明基准不是来自消息。"""
    order: list[str] = []
    prompts: list[str] = []
    _patch_layer(monkeypatch, order, [], prompts=prompts)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)

    payload = model_debug.run_role_chat(agent, "verifier", "验证：设备已打开", serial="DEV-1")

    assert payload["log_basis"]["from_message"] is False
    assert payload["log_basis"]["basis_time"]
    assert "来源：最近一个取证窗" in prompts[0]


def test_verifier_chat_without_listening_port_says_so(agent, monkeypatch, log_env):
    """监听开关关着：不取证据、不打开端口，输入里如实说明没有日志。"""
    from apps.ai_assistant import api

    order: list[str] = []
    prompts: list[str] = []
    _patch_layer(monkeypatch, order, [], prompts=prompts)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)
    monkeypatch.setattr(api, "get_log_port_enabled_map", lambda: {7005: False})

    payload = model_debug.run_role_chat(agent, "verifier", f"验证 {BASIS}", serial="DEV-1")

    assert payload["log_basis"]["note"] == NOTE_NO_LISTEN
    assert "log_evidence" not in payload
    assert NOTE_NO_LISTEN in prompts[0]


def test_executor_chat_has_no_log_evidence_block(agent, monkeypatch, log_env):
    """执行角色不受影响：输入里没有该证据块，响应也没有这两个键。"""
    order: list[str] = []
    prompts: list[str] = []
    _patch_layer(monkeypatch, order, [], prompts=prompts)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)

    payload = model_debug.run_role_chat(agent, "executor", f"点一下开关 {BASIS}", serial="DEV-1")

    assert "【设备日志证据 · 调试回溯】" not in prompts[0]
    assert "log_evidence" not in payload
    assert "log_basis" not in payload


class _ToolRole:
    """桩角色：ask() 时返回带指定工具轨迹的结果（本轮检查过哪些关键词）。"""

    def __init__(self, rows: list[dict], order: list[str]):
        self._rows = rows
        self._order = order

    async def ask(self, content: str) -> RoleResult:
        self._order.append("ask")
        return RoleResult(
            role="verifier",
            model_name="stub-model",
            output='{"result": "PASS"}',
            tool_usage=self._rows,
        )


def test_verifier_chat_input_carries_keyword_catalog_and_rule(agent, monkeypatch, log_env):
    """验收对话的输入带当前关键词表与「两条件」口径（模型据此报关键词、判 PASS/FAIL）。"""
    order: list[str] = []
    prompts: list[str] = []
    _patch_layer(monkeypatch, order, [], prompts=prompts)
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)

    model_debug.run_role_chat(agent, "verifier", f"验证 {BASIS}", serial="DEV-1")

    prompt = prompts[0]
    assert "check_device_log" in prompt
    assert "switch_on" in prompt  # 关键词表里的词（取自运行时索引）
    assert "日志检测到 + 截图确认两个条件都满足才可判 PASS" in prompt


def test_verifier_chat_payload_carries_checked_keywords(agent, monkeypatch, log_env):
    """响应带本轮的 log_assertion_info（平台按模型对检查工具的调用自动填）。"""
    order: list[str] = []
    rows = [
        {"type": "call", "name": "check_device_log", "input": {"keyword": "switch_on"}},
        {"type": "result", "name": "check_device_log", "output": '{"detected": true}'},
    ]
    _patch_layer(monkeypatch, order, [], prompts=[])
    monkeypatch.setattr(model_debug, "ensure_log_evidence", lambda: None)
    monkeypatch.setattr(
        model_debug,
        "build_debug_role",
        lambda agent, role, model_cfg, user_id="": _ToolRole(rows, order),
    )

    payload = model_debug.run_role_chat(agent, "verifier", f"验证 {BASIS}", serial="DEV-1")

    assert payload["log_assertion_info"] == "switch_on"
