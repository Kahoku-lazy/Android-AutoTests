"""工具勾选：只读预设可去掉一项，未知名字拒绝。"""

from __future__ import annotations

import pytest

from engines.backend_bridge.agents.tool_selection import ToolSelectionError, select_tools

pytestmark = [pytest.mark.unit]


def test_readonly_remove_drops_that_function_and_writes():
    tools = select_tools(
        [{"domain": "adb", "preset": "readonly", "add": [], "remove": ["adb_screenshot"]}]
    )
    names = {tool.name for tool in tools}
    assert "adb_screenshot" not in names
    assert "adb_tap" not in names
    assert "adb_devices" in names


def test_unknown_function_is_rejected():
    with pytest.raises(ToolSelectionError, match="未知工具"):
        select_tools([{"domain": "adb", "preset": "all", "add": ["not_a_tool"], "remove": []}])


def test_empty_selection_returns_no_tools():
    assert select_tools([]) == []


def test_case_authoring_drops_device_write_tools():
    tools = select_tools(
        [
            {"domain": "adb", "preset": "all", "add": [], "remove": []},
            {"domain": "case_library", "preset": "all", "add": [], "remove": []},
        ],
        kind="case_authoring",
    )
    names = {tool.name for tool in tools}
    assert names == {"save_authored_case"}


def test_requirement_breakdown_drops_device_tools():
    tools = select_tools(
        [
            {"domain": "adb", "preset": "readonly", "add": [], "remove": []},
            {"domain": "document", "preset": "readonly", "add": [], "remove": []},
        ],
        kind="requirement_breakdown",
    )
    names = {tool.name for tool in tools}
    assert names == {"read_requirement"}


def test_unknown_case_tool_rejects_before_start():
    with pytest.raises(ToolSelectionError, match="未知工具"):
        select_tools(
            [{"domain": "case_library", "preset": "all", "add": ["missing"], "remove": []}],
            kind="case_authoring",
        )
