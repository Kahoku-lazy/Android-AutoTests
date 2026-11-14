"""平台 UI 执行角色：装配结果与设备工具。

只测 `agents/ui_executor.py` 的装配面。不跑任务、不联网（构造模型不联网）。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.config import load_secret
from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware
from engines.backend_bridge.agents import UI_EXECUTOR_ROLE, PlatformRole, build_ui_executor

pytestmark = [pytest.mark.unit]


def test_role_definition_is_frozen_and_named():
    """角色三要素固定：键、提示词、默认模型。"""
    assert isinstance(UI_EXECUTOR_ROLE, PlatformRole)
    assert UI_EXECUTOR_ROLE.role_key == "ui_executor"
    assert UI_EXECUTOR_ROLE.prompt_name == "UI_EXECUTOR_PROMPT"
    assert UI_EXECUTOR_ROLE.model_short


async def test_build_returns_bundle_and_observer():
    """装配返回 (bundle, 观测中间件)，且智能体已挂设备工具。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    bundle, observer = await build_ui_executor()

    assert isinstance(bundle, AgentBundle)
    assert isinstance(observer, ObservationMiddleware)
    assert bundle.agent.name == UI_EXECUTOR_ROLE.role_key
    assert bundle.api_key_env == "GOVEE_API_KEY"

    schemas = await bundle.agent.toolkit.get_tool_schemas()
    assert len(schemas) > 0, "执行角色必须带设备工具"


async def test_build_reuses_given_observer():
    """调用方传入观测中间件时复用同一实例，便于统一取记录。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    observer = ObservationMiddleware()
    _, returned = await build_ui_executor(observer=observer)
    assert returned is observer


async def test_build_accepts_model_override():
    """调用方可覆盖模型短名（平台按 AIAgent 配置传入）。"""
    if not load_secret("DEEPSEEK_API_KEY"):
        pytest.skip("未配置 DEEPSEEK_API_KEY，跳过需要真实模型构造的用例")
    bundle, _ = await build_ui_executor(model_short="deepseek_chat_flash")
    assert bundle.api_key_env == "DEEPSEEK_API_KEY"
