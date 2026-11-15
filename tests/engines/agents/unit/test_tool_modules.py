"""工具按模块授予：配置写模块名，创建时激活，模型仍可 reset_tools 关闭。"""

from __future__ import annotations

import pytest

from engines.agents.agent_builders import build_ui_executor, build_ui_verifier
from engines.agents.tools_config import (
    TOOL_MODULES,
    activate_modules,
    build_toolkit_for_modules,
    role_modules,
)

pytestmark = [pytest.mark.unit]


def _names(agent, group: str) -> set[str]:
    """取一个工具组里的工具名。"""
    matched = next(item for item in agent.toolkit.tool_groups if item.name == group)
    return {tool.name for tool in matched.tools}


def test_device_module_excludes_observe_tools() -> None:
    """设备模块只有写操作，截图与坐标核对不在其中。"""
    names = set(TOOL_MODULES["device"].tool_names)
    assert "click_ratio" in names
    assert "screenshot_page" not in names
    assert "mark_dot" not in names


def test_unknown_module_is_rejected() -> None:
    """未知模块名报错并列出可选名。"""
    with pytest.raises(ValueError, match="observe"):
        build_toolkit_for_modules(("gesture",))


def test_role_modules_come_from_config() -> None:
    """执行角色读 YAML 的 modules，验收角色只有 observe。"""
    from engines.agents.config.config import load_agent_config

    roles = load_agent_config()
    assert role_modules(roles, "UI_EXECUTOR_ROLE_CONFIG") == ("device", "observe")
    assert role_modules(roles, "UI_VERIFIER_ROLE_CONFIG") == ("observe",)
    assert role_modules(roles, "CASE_WRITER_ROLE_CONFIG") == ()


def test_executor_starts_with_granted_groups_active(monkeypatch) -> None:
    """创建后已授予的组是激活的，验收角色没有 device 组。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    executor = build_ui_executor()
    verifier = build_ui_verifier()

    assert executor.state.tool_context.activated_groups == ["device", "observe"]
    assert "click_ratio" in _names(executor, "device")
    assert "device" not in {group.name for group in verifier.toolkit.tool_groups}
    assert verifier.state.tool_context.activated_groups == ["observe"]


def test_reset_tools_can_deactivate_a_granted_module(monkeypatch) -> None:
    """模型调用 reset_tools 后，未置真的组不再激活。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    agent = build_ui_executor()

    agent.state.tool_context.activated_groups.clear()
    agent.state.tool_context.activated_groups.extend(["observe"])

    assert agent.state.tool_context.activated_groups == ["observe"]
    activate_modules(agent, ["device", "observe"])
    assert agent.state.tool_context.activated_groups == ["device", "observe"]
