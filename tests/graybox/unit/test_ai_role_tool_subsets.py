"""灰盒·单元测试 — 设备执行三角色的工具子集（spec: ai-device-planner-tools）。

零设备、零 I/O：只断言配置里的工具名与注册表、角色装配一致。
"""

from types import SimpleNamespace

import pytest

from apps.ai_assistant.tools import TOOLS
from engines.ai.agentscope.config import DEVICE_PLANNER_TOOLS, VERIFIER_TOOLS, VISION_TOOLS
from engines.ai.agentscope.model import PlannerRole
from engines.ai.base import ToolSpec

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]

_PAGE_FLOW_TOOLS = {"list_page_flows", "get_page_flow"}


def _all_tool_specs() -> list[ToolSpec]:
    return [
        ToolSpec(name=name, handler=lambda **_: "{}", read_only=read_only)
        for name, (_, read_only) in TOOLS.items()
    ]


def test_role_subsets_only_reference_registered_tools():
    """三角色子集只能引用已注册工具：装配对缺失名静默跳过，拼错不会报错。"""
    for subset in (DEVICE_PLANNER_TOOLS, VISION_TOOLS, VERIFIER_TOOLS):
        assert set(subset) <= set(TOOLS), set(subset) - set(TOOLS)


def test_planner_subset_is_the_page_flow_tools():
    """planner 拿到页面流工具（与手册所述一致）。"""
    assert PlannerRole.spec.tool_names == tuple(DEVICE_PLANNER_TOOLS)
    assert set(DEVICE_PLANNER_TOOLS) == _PAGE_FLOW_TOOLS


def test_planner_role_selects_both_page_flow_tools_from_registry():
    """经角色子集选取真的能拿到这两个，顺序与配置一致。"""
    selected = PlannerRole._select_tools(SimpleNamespace(spec=PlannerRole.spec), _all_tool_specs())

    assert [t.name for t in selected] == list(DEVICE_PLANNER_TOOLS)


def test_other_role_subsets_unchanged():
    """executor 不含页面流工具；verifier 仍只有 screenshot_page。"""
    assert not (set(VISION_TOOLS) & _PAGE_FLOW_TOOLS)
    assert VERIFIER_TOOLS == ["screenshot_page"]
