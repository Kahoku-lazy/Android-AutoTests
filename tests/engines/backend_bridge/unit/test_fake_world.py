"""假世界：同名假工具只记账，不调用真实现。"""

from __future__ import annotations

import pytest

from engines.backend_bridge.workflow.fake_world import scripted_tools

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_fake_world_records_call_and_skips_real_tool(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("真工具不该被调用")

    monkeypatch.setattr("engines.ae_harness.tools.adb.tools.run_adb", explode)
    calls: list[dict] = []
    tools = scripted_tools(
        [{"domain": "adb", "preset": "all", "add": [], "remove": []}],
        {"adb_tap": "仍停在设置"},
        calls,
    )
    named = {tool.name: tool for tool in tools}
    assert "adb_tap" in named, sorted(named)

    result = await named["adb_tap"].call(nx=0.5, ny=0.9)
    assert calls == [{"tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}}]
    assert "仍停在设置" in result.content[0].text
    assert "adb_devices" in named
