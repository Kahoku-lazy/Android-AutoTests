"""假工具构造：名字、入参形状与回放正文。"""

from __future__ import annotations

import pytest

from engines.ae_harness.tools.scripted import scripted_tool

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_scripted_tool_replays_text():
    seen: list[dict] = []

    async def respond(**kwargs: object) -> str:
        seen.append(dict(kwargs))
        return "已记录"

    tool = scripted_tool("adb_tap", {"type": "object"}, respond)
    assert tool.name == "adb_tap"
    assert tool.input_schema == {"type": "object"}

    result = await tool.call(nx=0.5)
    assert seen == [{"nx": 0.5}]
    assert result.content[0].text == "已记录"
