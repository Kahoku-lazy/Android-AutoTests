from __future__ import annotations

from engines.ae_harness.tools import build_adb_readonly_tools
from engines.backend_bridge.agents.card_agent import build_card_agent
from engines.backend_bridge.workflow.fake_world import scripted_tools

__all__ = ["play_script", "probe_same_instance"]


async def probe_same_instance(reply, **binding) -> dict:
    bundle = await build_card_agent(**binding)
    seen: list[int] = []
    usages: list[dict] = []

    async def ask(text: str) -> str:
        seen.append(id(bundle.agent))
        answer, usage = await reply(bundle.agent, text)
        if usage:
            usages.append(usage)
        return answer

    first = await ask("你好")
    second = await ask("上一句我说了什么")
    return {
        "same_instance": len(set(seen)) == 1,
        "usages": usages,
        "steps": [
            {"role": "user", "text": "你好"},
            {"role": "assistant", "text": first},
            {"role": "user", "text": "上一句我说了什么"},
            {"role": "assistant", "text": second},
        ],
    }


async def play_script(
    selections: list[dict], script: list[dict], *, kind: str = "ui_automation"
) -> list[dict]:
    calls: list[dict] = []
    mounted = {tool.name: tool for tool in scripted_tools(selections, {}, calls, kind=kind)}
    readonly = {tool.name for tool in build_adb_readonly_tools()}
    steps: list[dict] = []
    for item in script:
        name = str(item.get("tool") or "")
        role = str(item.get("role") or "")
        payload = dict(item.get("input") or {})
        allowed = mounted.get(name)
        if role == "verifier" and name not in readonly:
            allowed = None
        if allowed is None:
            steps.append({"role": role, "tool": name, "input": payload, "text": "未挂载"})
            continue
        await allowed.call(**payload)
        steps.append({"role": role, "tool": name, "input": payload, "text": calls[-1]["tool"]})
    return steps
