"""
文件名: ➡️ eval_probe.py 🏁
路径: ➡️ engines/backend_bridge/workflow/eval_probe.py 🏁
模块功能：➡️ 评测探针：同一实例两轮，或按剧本驱动假世界 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.eval_probe 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. probe_same_instance: 两轮对话是否仍是同一个智能体实例。
2. play_script: 按剧本调用假工具并留下有序过程，不跑真模型。
🏁
关联模块：➡️
1. engines.backend_bridge.workflow.fake_world: 导入 scripted_tools。
2. engines.backend_bridge.agents.card_agent: 导入 build_card_agent，装配被测名片。
3. engines.ae_harness.tools: 导入只读工具集，用来拦住验收者的写操作。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from engines.ae_harness.tools import build_adb_readonly_tools
from engines.backend_bridge.agents.card_agent import build_card_agent
from engines.backend_bridge.workflow.fake_world import scripted_tools

__all__ = ["play_script", "probe_same_instance"]


async def probe_same_instance(reply, **binding) -> dict:
    """
    用同一张名片连续问两句。

    Args:
        reply: 一轮回复。入参是当前智能体和这一句，返回原文与本轮用量。
        binding: 传给名片装配的运行参数。工具由调用方先换成假世界。

    Returns:
        含 same_instance、两轮过程与用量的字典。两轮拿到的不是同一个对象时记为换了实例。
    """
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
    """
    按剧本顺序调用假工具。

    Args:
        selections: 名片工具勾选。
        script: 每项含 role、tool 与 input。验收者的写操作即使勾选了也不挂上。
        kind: 工作流种类。

    Returns:
        有序过程。剧本点名了未挂上的工具时，记一条未见调用。
    """
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
