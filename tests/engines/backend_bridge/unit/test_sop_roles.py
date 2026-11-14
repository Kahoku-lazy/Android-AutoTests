"""平台 SOP 角色装配：验收者只读、两角色共用观察者。

只测 `workflow/roles.py` 的装配面；需要真实密钥构造模型时会跳过。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.config import load_secret
from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware
from engines.backend_bridge.workflow import SopRoles, build_sop_roles

pytestmark = [pytest.mark.unit]

# 只读工具集：任何写操作工具出现在验收者上都算违规。
WRITE_TOOL_HINTS = ("tap", "swipe", "input", "start", "stop", "install", "uninstall", "push")


def _needs_key() -> None:
    """没有密钥时跳过需要真实模型构造的用例。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")


async def test_roles_shape():
    """装配结果含两个角色与一个共用观察者。"""
    _needs_key()
    roles = await build_sop_roles()

    assert isinstance(roles, SopRoles)
    assert isinstance(roles.executor, AgentBundle)
    assert isinstance(roles.verifier, AgentBundle)
    assert isinstance(roles.observer, ObservationMiddleware)
    assert roles.executor.agent.name == "ui_executor"
    assert roles.verifier.agent.name == "ui_verifier"


async def test_verifier_has_no_write_tools():
    """验收者只带只读工具。"""
    _needs_key()
    roles = await build_sop_roles()
    schemas = await roles.verifier.agent.toolkit.get_tool_schemas()
    names = [item["function"]["name"] for item in schemas]

    assert names, "验收者必须带只读工具"
    offenders = [name for name in names if any(hint in name for hint in WRITE_TOOL_HINTS)]
    assert not offenders, f"验收者出现写操作工具：{offenders}"


async def test_executor_has_more_tools_than_verifier():
    """执行者的工具集严格大于验收者。"""
    _needs_key()
    roles = await build_sop_roles()
    executor_tools = await roles.executor.agent.toolkit.get_tool_schemas()
    verifier_tools = await roles.verifier.agent.toolkit.get_tool_schemas()

    assert len(executor_tools) > len(verifier_tools)


async def test_roles_share_one_observer():
    """两个角色共用同一个观测中间件，记录里靠 agent 名区分。"""
    _needs_key()
    watcher = ObservationMiddleware()
    roles = await build_sop_roles(observer=watcher)

    assert roles.observer is watcher
    assert roles.executor.api_key_env == "GOVEE_API_KEY"
    assert roles.verifier.api_key_env == "GOVEE_API_KEY"


async def test_controls_are_mounted_on_both_roles():
    """传入的控制中间件挂到两个角色的模型调用钩子上。"""
    _needs_key()
    from engines.ae_harness.middleware import BudgetMiddleware, RunBudget

    budget = BudgetMiddleware(RunBudget(max_model_calls=3))
    roles = await build_sop_roles(controls=[budget])

    for bundle in (roles.executor, roles.verifier):
        hooks = bundle.agent._model_call_middlewares  # noqa: SLF001 - 断言挂载位置
        assert budget in hooks


async def test_without_controls_only_observer_is_mounted():
    """不传控制中间件时，模型调用钩子上没有任何中间件。"""
    _needs_key()
    roles = await build_sop_roles()

    for bundle in (roles.executor, roles.verifier):
        assert bundle.agent._model_call_middlewares == []  # noqa: SLF001
