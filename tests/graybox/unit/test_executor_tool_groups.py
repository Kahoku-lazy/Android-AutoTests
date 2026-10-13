"""执行角色工具组：常驻组、四个动作组、平台业务技能组与组开关。"""

from __future__ import annotations

import asyncio

from types import SimpleNamespace

import pytest

from agentscope.tool import ToolGroup

from engines.agents.agents import ExecutorRole as ScratchExecutorRole
from engines.agents.prompt_config import EXECUTOR_PROMPT
from engines.agents.role.base import BaseRole
from engines.agents.role.config import ModelConfig, RoleSpecConfig
from engines.agents.role.executor import ExecutorRole
from engines.agents.tools import PlatformFunctionTool, build_toolkit
from engines.agents.tools.tool_device import device_tool_specs
from engines.agents.tools_config import (
    EXECUTOR_SKILLS_NAMES,
    EXECUTOR_TOOL_GROUPS,
    ToolGroupSpec,
    build_executor_toolkit,
    register_skills,
)

_BASIC = {"screenshot_page", "press_key", "reset_tools"}
_GESTURE = {"click_ratio", "tap_screen", "swipe_screen", "drag_ratio"}
_ACTION = _GESTURE | {"xpath_action", "input_text", "app_control"}
_SKILL_DIR = "engines/agents/skills/executor"


def _names(toolkit, groups: list[str]) -> set[str]:
    available = asyncio.run(toolkit._get_available_tools(groups))
    return set(available)


def _skills(toolkit, groups: list[str] | None) -> set[str]:
    skills = asyncio.run(toolkit._get_available_skills(groups))
    return set(skills)


def _switch(toolkit, state, **flags: bool) -> str:
    chunk = asyncio.run(toolkit.builtin_meta_tool.tool.call(_agent_state=state, **flags))
    return chunk.content[0].text


def _state():
    return SimpleNamespace(tool_context=SimpleNamespace(activated_groups=[]))


def _role(toolkit) -> BaseRole:
    config = ModelConfig(
        provider="deepseek",
        model_name="deepseek-flash",
        api_key="test-key",
        base_url="https://example.invalid/v1",
    )
    return BaseRole(
        config, RoleSpecConfig(name="t", system_prompt="t", toolkit=toolkit, vision=False)
    )


def _group(toolkit, name: str):
    return next(group for group in toolkit.tool_groups if group.name == name)


def test_non_basic_group_registers_switch_outside_basic() -> None:
    by_name = {spec.name: spec for spec in device_tool_specs()}
    toolkit = build_toolkit(
        [by_name["screenshot_page"]],
        tool_groups=[
            ToolGroup(
                name="demo",
                description="示例组",
                tools=[PlatformFunctionTool(by_name["press_key"])],
            )
        ],
    )
    assert _names(toolkit, []) == {"screenshot_page", "reset_tools"}
    assert [tool.name for tool in _group(toolkit, "basic").tools] == ["screenshot_page"]


def test_unknown_tool_name_fails() -> None:
    with pytest.raises(ValueError, match="no_such_tool"):
        build_executor_toolkit(basic_tool_names=("no_such_tool",), groups=())


def test_tool_in_two_groups_fails() -> None:
    groups = (
        ToolGroupSpec("gesture", "点击滑动", "用手势。", tool_names=("click_ratio",)),
        ToolGroupSpec("xpath", "xpath", "用 xpath。", tool_names=("click_ratio",)),
    )
    with pytest.raises(ValueError, match="click_ratio"):
        build_executor_toolkit(basic_tool_names=(), groups=groups)


def test_default_visibility_is_basic_only() -> None:
    toolkit = build_executor_toolkit()
    assert _names(toolkit, []) == _BASIC
    schema = toolkit.builtin_meta_tool.tool.input_schema["properties"]
    assert "点击滑动" in schema["gesture"]["description"]
    assert "xpath" in schema["xpath"]["description"]
    assert "输入" in schema["text_input"]["description"]
    assert "启停应用" in schema["app"]["description"]
    assert "平台业务工具" in schema["platform_business"]["description"]
    assert "platform-tools-manual" not in _skills(toolkit, [])


def test_each_action_group_exposes_only_its_tools() -> None:
    toolkit = build_executor_toolkit()
    assert _names(toolkit, ["gesture"]) == _BASIC | _GESTURE
    assert _names(toolkit, ["xpath"]) == _BASIC | {"xpath_action"}
    assert _names(toolkit, ["text_input"]) == _BASIC | {"input_text"}
    assert _names(toolkit, ["app"]) == _BASIC | {"app_control"}


def test_switch_overwrites_previous_groups() -> None:
    toolkit = build_executor_toolkit()
    state = _state()
    _switch(toolkit, state, gesture=True)
    assert _names(toolkit, list(state.tool_context.activated_groups)) == _BASIC | _GESTURE
    text = _switch(toolkit, state, text_input=True)
    visible = _names(toolkit, list(state.tool_context.activated_groups))
    assert "click_ratio" not in visible
    assert visible == _BASIC | {"input_text"}
    assert "text_input" in text
    assert "向当前输入框输入" in text


def test_switch_can_close_every_optional_group() -> None:
    toolkit = build_executor_toolkit()
    state = _state()
    _switch(
        toolkit,
        state,
        gesture=False,
        xpath=False,
        text_input=False,
        app=False,
        platform_business=False,
    )
    assert _names(toolkit, list(state.tool_context.activated_groups)) == _BASIC


def test_platform_business_skills_follow_the_group() -> None:
    toolkit = build_executor_toolkit()
    assert "platform-tools-manual" not in _skills(toolkit, [])
    opened = _skills(toolkit, ["platform_business"])
    assert "platform-tools-manual" in opened
    visible = _names(toolkit, ["platform_business", "gesture"])
    assert _GESTURE <= visible
    assert "xpath_action" not in visible
    assert "input_text" not in visible
    assert "app_control" not in visible


def test_empty_skill_list_stays_empty_when_group_opens() -> None:
    groups = tuple(
        ToolGroupSpec(
            group.name,
            group.description,
            group.instructions,
            tool_names=group.tool_names,
            skill_dirs=(),
        )
        if group.name == "platform_business"
        else group
        for group in EXECUTOR_TOOL_GROUPS
    )
    toolkit = build_executor_toolkit(groups=groups)
    assert _skills(toolkit, ["platform_business"]) == set()


def test_register_skills_defaults_to_basic_and_rejects_unknown_group() -> None:
    toolkit = build_toolkit([])
    register_skills(toolkit, [_SKILL_DIR])
    assert _skills(toolkit, None) == {"platform-tools-manual"}
    with pytest.raises(ValueError, match="missing-group"):
        register_skills(toolkit, [_SKILL_DIR], group_name="missing-group")


def test_register_skills_skips_directory_already_on_any_group() -> None:
    toolkit = build_executor_toolkit()
    before = len(_group(toolkit, "platform_business").skills_or_loaders)
    register_skills(toolkit, EXECUTOR_SKILLS_NAMES, group_name="platform_business")
    register_skills(toolkit, EXECUTOR_SKILLS_NAMES)
    assert len(_group(toolkit, "platform_business").skills_or_loaders) == before
    assert _group(toolkit, "basic").skills_or_loaders == []


def test_executor_role_registers_skills_before_start() -> None:
    config = ModelConfig(
        provider="deepseek",
        model_name="deepseek-flash",
        api_key="test-key",
        base_url="https://example.invalid/v1",
    )
    first = ExecutorRole(config)
    second = ExecutorRole(config)
    assert first.agent is None
    assert first.role.toolkit is not second.role.toolkit
    for role in (first, second):
        assert _group(role.role.toolkit, "basic").skills_or_loaders == []
        loaders = _group(role.role.toolkit, "platform_business").skills_or_loaders
        assert len(loaders) == 1


def test_scratch_executor_basic_has_no_skills() -> None:
    role = ScratchExecutorRole(
        ModelConfig(
            provider="deepseek",
            model_name="deepseek-flash",
            api_key="test-key",
            base_url="https://example.invalid/v1",
        )
    )
    role.start()
    basic = _group(role.role.toolkit, "basic")
    assert basic.skills_or_loaders == []
    assert {tool.name for tool in basic.tools} == {"screenshot_page", "press_key"}


def test_executor_prompt_states_group_switch_rules() -> None:
    assert "用某组前先打开该组" in EXECUTOR_PROMPT
    assert "一次组开关是全部可开关组的最终状态" in EXECUTOR_PROMPT
    assert "截图和返回键不用打开" in EXECUTOR_PROMPT


def test_optional_tools_are_not_all_visible_together_by_default() -> None:
    toolkit = build_executor_toolkit()
    assert _ACTION.isdisjoint(_names(toolkit, []))
