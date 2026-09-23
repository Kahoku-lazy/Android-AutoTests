"""设备控制三角色系统提示词读写（spec: ai-device-prompts）。"""

from __future__ import annotations

import importlib

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.ai_assistant import api
from apps.ai_assistant.models import AIAgent
from engines.ai.agentscope.config import (
    PLANNER_PROMPT,
    VERIFIER_PROMPT,
    VISION_PROMPT,
    DeviceExecutionConfig,
    ModelConfig,
)
from engines.ai.agentscope.model import build_device_models
from models.constants import AgentStatus
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()


@pytest.fixture
def platform_agent(db):
    return AIAgent.objects.create(
        name="platform",
        status=AgentStatus.ACTIVE,
        prompt_planner="## planner",
        prompt_executor="## executor",
        prompt_verifier="## verifier",
    )


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


def test_get_device_prompts(platform_agent):
    data = api.get_device_prompts(platform_agent)
    assert data["planner"] == "## planner"
    assert data["executor"] == "## executor"
    assert data["verifier"] == "## verifier"
    assert data["agent_id"] == platform_agent.id


def test_update_device_prompts_success(platform_agent):
    data = api.update_device_prompts(
        platform_agent,
        {"planner": "# P", "executor": "# E", "verifier": "# V"},
    )
    platform_agent.refresh_from_db()
    assert platform_agent.prompt_planner == "# P"
    assert data["executor"] == "# E"


def test_update_device_prompts_rejects_blank(platform_agent):
    with pytest.raises(ValueError, match="executor"):
        api.update_device_prompts(
            platform_agent,
            {"planner": "# P", "executor": "  ", "verifier": "# V"},
        )
    platform_agent.refresh_from_db()
    assert platform_agent.prompt_planner == "## planner"


def test_api_get_ok(platform_agent, db):
    user = User.objects.create_user(username="reader", password="x")
    client = Client()
    resp = client.get("/api/ai/device-prompts/", **_auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["planner"] == "## planner"


def test_api_update_forbidden_for_normal_user(platform_agent, db):
    user = User.objects.create_user(username="normal", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/device-prompts/update/",
        data={"planner": "# P", "executor": "# E", "verifier": "# V"},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 403
    platform_agent.refresh_from_db()
    assert platform_agent.prompt_planner == "## planner"


def test_api_update_ok_for_superuser(platform_agent, db):
    user = User.objects.create_superuser(username="admin", email="a@t.com", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/device-prompts/update/",
        data={"planner": "# P2", "executor": "# E2", "verifier": "# V2"},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["planner"] == "# P2"
    platform_agent.refresh_from_db()
    assert platform_agent.prompt_verifier == "# V2"


def test_api_update_blank_returns_400(platform_agent, db):
    user = User.objects.create_superuser(username="admin2", email="b@t.com", password="x")
    client = Client()
    resp = client.post(
        "/api/ai/device-prompts/update/",
        data={"planner": "# P", "executor": "  ", "verifier": "# V"},
        content_type="application/json",
        **_auth_headers(user),
    )
    assert resp.status_code == 400


def test_api_404_without_platform_agent(db):
    user = User.objects.create_user(username="lonely", password="x")
    client = Client()
    resp = client.get("/api/ai/device-prompts/", **_auth_headers(user))
    assert resp.status_code == 404


def test_engine_prompt_constants_empty():
    assert PLANNER_PROMPT == ""
    assert VISION_PROMPT == ""
    assert VERIFIER_PROMPT == ""


def test_injected_system_prompt_on_role(monkeypatch):
    """注入正文出现在角色 system_prompt。"""

    class _FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.state = type("S", (), {"context": []})()

    monkeypatch.setattr("engines.ai.agentscope.model.Agent", _FakeAgent)
    monkeypatch.setattr(
        "engines.ai.agentscope.model.create_model",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "engines.ai.agentscope.model.build_toolkit",
        lambda *a, **k: object(),
    )

    cfg = DeviceExecutionConfig(
        planner=ModelConfig(provider="deepseek", model_name="m", api_key="sk"),
        executor=ModelConfig(provider="deepseek", model_name="m", api_key="sk"),
        verifier=ModelConfig(provider="deepseek", model_name="m", api_key="sk"),
    )
    planner, executor, verifier = build_device_models(
        cfg,
        tools=[],
        system_prompts={"planner": "FROM-DB-PLANNER", "executor": "FROM-E", "verifier": "FROM-V"},
    )
    assert planner.system_prompt == "FROM-DB-PLANNER"
    assert executor.system_prompt == "FROM-E"
    assert verifier.system_prompt == "FROM-V"


# ── planner 页面流指引：迁移逻辑（spec: ai-device-planner-tools）──


def _guidance_module():
    """迁移模块名以数字开头，只能经 importlib 取。"""
    return importlib.import_module(
        "apps.ai_assistant.migrations.0041_add_planner_page_flow_guidance"
    )


def test_planner_guidance_inserted_after_anchor():
    mod = _guidance_module()
    base = f"## 步骤要求\n{mod._ANCHOR}\n\n## 输出字段\n"

    updated = mod.with_guidance(base)

    assert mod._GUIDANCE in updated
    assert updated.index(mod._ANCHOR) < updated.index(mod._GUIDANCE)
    # 除追加行外其余内容逐字保留
    assert updated.replace(f"\n{mod._GUIDANCE}", "") == base


def test_planner_guidance_is_idempotent_and_leaves_user_edits():
    mod = _guidance_module()
    once = mod.with_guidance(f"{mod._ANCHOR}\n")

    assert mod.with_guidance(once) == once  # 已含指引 → 不重复插入

    user_written = "## 我自己重写的 planner，没有锚点"
    assert mod.with_guidance(user_written) == user_written


def test_planner_guidance_is_reversible():
    mod = _guidance_module()
    base = f"{mod._ANCHOR}\n"

    assert mod.without_guidance(mod.with_guidance(base)) == base


def test_seed_planner_prompt_carries_guidance():
    """新装库的种子必须已含指引（与存量库迁移两条下发路径一致）。"""
    mod = _guidance_module()
    seed = importlib.import_module("apps.ai_assistant.migrations.0038_aiagent_device_prompts")

    assert mod._GUIDANCE in seed._SNAPSHOT_PLANNER
    assert mod._ANCHOR in seed._SNAPSHOT_PLANNER
