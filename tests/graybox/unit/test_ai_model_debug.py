"""单模型调试台：三角色只读配置 + 单角色调试对话（spec: ai-model-debug）。"""

from __future__ import annotations

import types

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import model_debug
from apps.ai_assistant.api import encrypt_key
from apps.ai_assistant.models import AIAgent, AIConversation, AIMessage
from engines.ai.agentscope.config import (
    DEVICE_PLANNER_TOOLS,
    VERIFIER_TOOLS,
    VISION_TOOLS,
    ModelConfig,
)
from engines.ai.agentscope.model import RoleResult
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="md_admin", password="x")


@pytest.fixture
def member():
    return User.objects.create_user(username="md_member", password="x")


def _route_cfg() -> dict:
    # 与 api.py 写入时一致：api_key 落库前经 Fernet 加密
    role = {
        "provider": "deepseek",
        "model_name": "deepseek-chat",
        "api_key": encrypt_key("stub-key"),
    }
    return {
        "device_control": {
            "planner": dict(role),
            "executor": dict(role),
            "verifier": dict(role),
        }
    }


@pytest.fixture
def agent(admin):
    return AIAgent.objects.create(
        owner=admin,
        name="调试智能体",
        prompt_planner="PLANNER-PROMPT-v1",
        prompt_executor="EXECUTOR-PROMPT-v1",
        prompt_verifier="VERIFIER-PROMPT-v1",
        route_configs=_route_cfg(),
    )


def _configs(agent) -> dict:
    return model_debug.build_role_debug_configs(agent)


def _role_cfg(agent, role) -> dict:
    return next(item for item in _configs(agent)["roles"] if item["role"] == role)


# ── 只读配置：与引擎装配同源 ──


def test_role_tool_subsets_match_engine_constants(agent):
    assert [t["name"] for t in _role_cfg(agent, "planner")["tools"]] == list(DEVICE_PLANNER_TOOLS)
    assert [t["name"] for t in _role_cfg(agent, "executor")["tools"]] == list(VISION_TOOLS)
    assert [t["name"] for t in _role_cfg(agent, "verifier")["tools"]] == list(VERIFIER_TOOLS)


def test_role_config_declares_needs_device(agent):
    assert _role_cfg(agent, "planner")["needs_device"] is False
    assert _role_cfg(agent, "executor")["needs_device"] is True
    assert _role_cfg(agent, "verifier")["needs_device"] is True


def test_role_prompt_and_vision(agent):
    assert _role_cfg(agent, "planner")["vision"] is False
    assert _role_cfg(agent, "executor")["vision"] is True
    assert _role_cfg(agent, "planner")["prompt"] == "PLANNER-PROMPT-v1"
    assert _role_cfg(agent, "executor")["prompt"] == "EXECUTOR-PROMPT-v1"


def test_config_leaks_no_plaintext_secret(agent):
    payload = _configs(agent)
    assert "stub-key" not in repr(payload)
    for role in payload["roles"]:
        assert set(role["model"]).isdisjoint({"api_key", "base_url"})
        assert role["model"]["has_api_key"] is True
        assert role["model"]["configured"] is True


def test_tools_carry_read_only_and_enabled_flags(agent):
    tools = {t["name"]: t for t in _role_cfg(agent, "executor")["tools"]}
    assert tools["tap_screen"]["read_only"] is False
    assert tools["screenshot_page"]["read_only"] is True
    assert tools["tap_screen"]["enabled"] is True
    assert tools["tap_screen"]["category"] == "设备控制"


def test_skills_and_knowledge_declare_ownership(agent):
    payload = _configs(agent)
    assert payload["skills"]["shared_by_roles"] is True
    assert payload["knowledge"]["wired_to_runtime"] is False
    assert "file_count" in payload["knowledge"]


# ── HTTP：权限与参数 ──


def test_endpoints_require_superuser(client, member, agent):
    assert client.get("/api/ai/model-debug/planner/", **_headers(member)).status_code == 403
    chat = client.post(
        "/api/ai/model-debug/planner/chat/",
        data={"text": "你好"},
        content_type="application/json",
        **_headers(member),
    )
    assert chat.status_code == 403


def test_config_endpoint_returns_role_and_shared_blocks(client, admin, agent):
    resp = client.get("/api/ai/model-debug/executor/", **_headers(admin))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"]["role"] == "executor"
    assert data["role"]["label"] == "执行模型 Executor"
    assert data["skills"]["shared_by_roles"] is True
    assert data["knowledge"]["wired_to_runtime"] is False


def test_unknown_role_returns_400(client, admin, agent):
    assert client.get("/api/ai/model-debug/robot/", **_headers(admin)).status_code == 400
    resp = client.post(
        "/api/ai/model-debug/robot/chat/",
        data={"text": "你好"},
        content_type="application/json",
        **_headers(admin),
    )
    assert resp.status_code == 400
    assert "未知角色" in resp.json()["message"]


def test_missing_model_config_returns_readable_400(client, admin):
    AIAgent.objects.create(owner=admin, name="空配置智能体", route_configs={})

    resp = client.post(
        "/api/ai/model-debug/planner/chat/",
        data={"text": "你好"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert "model_name" in resp.json()["message"]


def test_empty_text_rejected(client, admin, agent):
    resp = client.post(
        "/api/ai/model-debug/planner/chat/",
        data={"text": "   "},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert "不能为空" in resp.json()["message"]


# ── 对话：模型层打桩 ──


class _FakeRole:
    """替代真实 AgentScope 角色：把"收到的系统提示词"回显出来，证明提示词确实被注入。"""

    def __init__(self, system_prompt: str, reply: str):
        self.system_prompt = system_prompt
        self._reply = reply
        self.seen_input = ""

    async def ask(self, content: str) -> RoleResult:
        self.seen_input = content
        return RoleResult(
            role="planner",
            model_name="stub-model",
            output=f"{self._reply}|{self.system_prompt}|{content}",
            tool_usage=[
                {"type": "call", "name": "current_app", "input": {"serial": "DEV-1"}},
                {"type": "result", "name": "current_app", "state": "success", "output": "pkg"},
            ],
        )


def _patch_model_layer(monkeypatch, reply: str = "REPLY") -> dict:
    cfg = ModelConfig(
        provider="deepseek", model_name="stub-model", api_key="stub-key", base_url="http://stub"
    )
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
    captured: dict = {}

    def _build(agent, role, model_cfg, user_id=""):
        prompt = model_debug.role_prompt(agent, role)
        captured["prompt"] = prompt
        role_obj = _FakeRole(system_prompt=prompt, reply=reply)
        captured["role_obj"] = role_obj
        return role_obj

    monkeypatch.setattr(model_debug, "build_debug_role", _build)
    return captured


def _patch_devices(monkeypatch, serials=("DEV-1",)) -> None:
    """把候选设备固定住，单测不依赖 device_pool 的真实数据。"""
    monkeypatch.setattr(
        model_debug,
        "available_device_options",
        lambda user_id: [{"value": s, "label": f"{s} (stub)"} for s in serials],
    )


def test_chat_uses_role_prompt_and_writes_no_records(client, admin, agent, monkeypatch):
    captured = _patch_model_layer(monkeypatch, reply="REPLY")
    _patch_devices(monkeypatch)
    before_conv = AIConversation.objects.count()
    before_msg = AIMessage.objects.count()

    resp = client.post(
        "/api/ai/model-debug/executor/chat/",
        data={"text": "你好", "serial": "DEV-1"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"] == "executor"
    assert data["model_name"] == "stub-model"
    assert data["reply"] == "REPLY|EXECUTOR-PROMPT-v1|当前设备 serial：DEV-1\n你好"
    assert captured["prompt"] == "EXECUTOR-PROMPT-v1"
    # 工具调用轨迹透出（前端据此展示"调了什么工具"）
    assert data["tool_usage"][0]["name"] == "current_app"
    assert data["tool_usage"][0]["type"] == "call"
    # 调试对话 MUST NOT 落库
    assert AIConversation.objects.count() == before_conv
    assert AIMessage.objects.count() == before_msg


def test_chat_reflects_updated_prompt(agent, admin, monkeypatch):
    captured = _patch_model_layer(monkeypatch, reply="v2")
    agent.prompt_planner = "PLANNER-PROMPT-v2"
    agent.save(update_fields=["prompt_planner"])

    result = model_debug.run_role_chat(agent, "planner", "问一句", user_id=str(admin.id))

    assert captured["prompt"] == "PLANNER-PROMPT-v2"
    assert "PLANNER-PROMPT-v2" in result["reply"]


def _stub_cfg() -> ModelConfig:
    return ModelConfig(
        provider="deepseek", model_name="stub-model", api_key="stub-key", base_url="http://stub"
    )


def test_debug_role_mounts_role_tool_subset(agent):
    cfg = _stub_cfg()
    role = model_debug.build_debug_role(agent, "executor", cfg, user_id="1")

    # 与生产装配同源：工具名取自角色规格，不再以空工具集运行
    assert role.spec.tool_names == tuple(VISION_TOOLS)
    assert role.spec.vision is True
    assert role.system_prompt == "EXECUTOR-PROMPT-v1"
    assert model_debug.build_debug_role(agent, "planner", cfg).spec.tool_names == tuple(
        DEVICE_PLANNER_TOOLS
    )
    assert model_debug.build_debug_role(agent, "verifier", cfg).spec.tool_names == tuple(
        VERIFIER_TOOLS
    )


def test_debug_role_mounts_real_tools_but_no_skill(agent, monkeypatch):
    from engines.ai.agentscope import model as engine_model

    seen: dict = {}
    real_build_toolkit = engine_model.build_toolkit

    def _spy(specs, user_id="", skill_dirs=None):
        seen["names"] = [s.name for s in specs]
        seen["skill_dirs"] = list(skill_dirs or [])
        return real_build_toolkit(specs, user_id=user_id, skill_dirs=skill_dirs)

    monkeypatch.setattr(engine_model, "build_toolkit", _spy)
    model_debug.build_debug_role(agent, "executor", _stub_cfg(), user_id="1")

    assert seen["names"] == list(VISION_TOOLS)
    assert seen["skill_dirs"] == []


def test_role_needs_device_follows_tool_signature():
    assert model_debug.role_needs_device("planner") is False
    assert model_debug.role_needs_device("executor") is True
    assert model_debug.role_needs_device("verifier") is True


def test_executor_chat_requires_device(client, admin, agent, monkeypatch):
    captured = _patch_model_layer(monkeypatch)
    _patch_devices(monkeypatch)

    resp = client.post(
        "/api/ai/model-debug/executor/chat/",
        data={"text": "你好"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert "需要先选定一台设备" in resp.json()["message"]
    # 未通过校验 MUST NOT 触发模型调用
    assert "role_obj" not in captured


def test_executor_chat_rejects_unavailable_device(client, admin, agent, monkeypatch):
    captured = _patch_model_layer(monkeypatch)
    _patch_devices(monkeypatch)

    resp = client.post(
        "/api/ai/model-debug/executor/chat/",
        data={"text": "你好", "serial": "NOT-AVAILABLE"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert "当前不可用" in resp.json()["message"]
    assert "role_obj" not in captured


def test_planner_chat_needs_no_device(client, admin, agent, monkeypatch):
    _patch_model_layer(monkeypatch, reply="PLAN")

    resp = client.post(
        "/api/ai/model-debug/planner/chat/",
        data={"text": "拆一下"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["reply"].endswith("拆一下")
