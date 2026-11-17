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
