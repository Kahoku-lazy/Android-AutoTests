"""工具目录：只列名字，adb 含全部与只读。"""

from __future__ import annotations

import pytest

from engines.ae_harness.tools.catalog import list_tool_catalog

pytestmark = [pytest.mark.unit]


def test_adb_domain_has_all_and_readonly_presets():
    catalog = list_tool_catalog()
    adb = next(item for item in catalog if item["domain"] == "adb")
    assert {preset["id"] for preset in adb["presets"]} == {"all", "readonly"}
    names = {tool["name"] for tool in adb["tools"]}
    assert "adb_tap" in names
    assert "adb_screenshot" in names
    assert any(tool["read_only"] for tool in adb["tools"])
    assert all("def " not in tool["description"] for tool in adb["tools"])
