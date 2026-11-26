from __future__ import annotations

import json

from engines.ae_harness.tools.scripted import scripted_tool
from engines.backend_bridge.agents.tool_selection import select_tools

__all__ = ["scripted_tools"]


def scripted_tools(
    selections: list[dict] | None, script: dict, calls: list[dict], *, kind: str = "ui_automation"
) -> list:
    fakes = []
    for real in select_tools(selections, kind=kind):
        fakes.append(_one(real.name, dict(real.input_schema or {}), script, calls))
    return fakes


def _one(name: str, schema: dict, script: dict, calls: list[dict]):
    async def respond(_tool_name: str = name, **kwargs) -> str:
        calls.append({"tool": _tool_name, "input": kwargs})
        body = script.get(_tool_name) or "假世界：动作已记录，没有触达真实设备。"
        return json.dumps({"status": True, "text": body}, ensure_ascii=False)

    return scripted_tool(name, schema, respond)
