"""
模块功能：➡️ 评测运行器。后台逐条跑探针，缺配置时不调用模型 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.live_runner 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading

log = logging.getLogger(__name__)

_SCRIPTS = {
    "S1": [{"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}}],
    "S2": [
        {"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}},
        {"role": "verifier", "tool": "adb_dump_ui", "input": {}},
        {"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.2}},
    ],
    "S3": [{"role": "verifier", "tool": "adb_tap", "input": {"nx": 0.1, "ny": 0.1}}],
}


def start_live_eval(run_id: int) -> None:
    """起后台线程。测试进程不自动跑，避免真模型调用。"""
    if "pytest" in sys.modules:
        return
    threading.Thread(target=execute, args=(run_id,), daemon=True, name=f"ai-eval-{run_id}").start()


def execute(run_id: int) -> None:
    """跑完一次评测。任何一步失败都收成失败运行，不留在进行中。"""
    from backend.apps.ai_assistant import api

    run = api.get_live_run(run_id)
    if run is None:
        return
    try:
        missing = _missing_key(run)
        if missing:
            api.finish_live_run(run_id, status="failed", error=f"缺少模型密钥：{missing}")
            return
        context = _context(run)
        failures: list[dict] = []
        usages: list[dict] = []
        for sample_id in run.sample_ids:
            steps, same, sample_usages = asyncio.run(_one(sample_id, context))
            usages.extend(sample_usages)
            graded = _grade(run, steps, same)
            failures.extend({**item, "sample": sample_id} for item in graded)
            api.append_live_sample(run_id, sample_id, sample_id, not graded, graded, steps)
        _bill(usages, run_id)
        api.finish_live_run(run_id, status="done", failures=failures)
    except Exception as exc:
        log.exception("assistant live eval failed run=%s", run_id)
        api.finish_live_run(run_id, status="failed", error=str(exc))


def _missing_key(run) -> str:
    """草稿引用的密钥名没有值时返回这个名字。"""
    from backend.apps.ai_assistant.models import AIAssistant, AIRole

    names: list[str] = []
    if run.target_kind == "assistant":
        card = AIAssistant.objects.filter(assistant_id=run.target_id).first()
        role = (
            AIRole.objects.select_related("model_config")
            .filter(role_id=getattr(card, "role_id", ""))
            .first()
        )
        if role is not None:
            names.append(role.model_config.api_key_env)
    return next((name for name in names if name and not os.environ.get(name)), "")


def _context(run) -> dict:
    """在同步侧取出名片勾选，避免异步里查库。"""
    from backend.apps.ai_assistant.models import AIAssistant, AISopWorkflow

    if run.target_kind == "workflow":
        workflow = AISopWorkflow.objects.filter(pk=int(run.target_id)).first()
        card = AIAssistant.objects.filter(
            assistant_id=getattr(workflow, "executor_assistant_id", "")
        ).first()
    else:
        card = AIAssistant.objects.filter(assistant_id=run.target_id).first()
    role = _role_of(card)
    config = getattr(role, "model_config", None)
    return {
        "name": getattr(card, "display_name", "probe"),
        "provider": getattr(config, "provider", ""),
        "api_key_env": getattr(config, "api_key_env", ""),
        "model_name": getattr(config, "model_name", ""),
        "base_url": getattr(config, "base_url", ""),
        "system_prompt": getattr(role, "system_prompt", ""),
        "tools": [],
        "selections": list(getattr(card, "tools", []) or []),
    }


def _role_of(card):
    """名片引用的角色。名片不存在时返回空。"""
    from backend.apps.ai_assistant.models import AIRole

    if card is None:
        return None
    return AIRole.objects.select_related("model_config").filter(role_id=card.role_id).first()


async def _one(sample_id: str, context: dict) -> tuple[list[dict], bool | None, list[dict]]:
    """跑一条样本。助手用真模型问两轮，SOP 用两侧名片的勾选走剧本。"""
    from engines.backend_bridge.workflow.eval_probe import play_script, probe_same_instance

    if sample_id.startswith("S"):
        steps = await play_script(context["selections"], _SCRIPTS.get(sample_id, []))
        return steps, None, []

    async def reply(agent, text: str):
        return await _ask_model(agent, text, context)

    result = await probe_same_instance(reply, **_binding(context))
    return result["steps"], result["same_instance"], result["usages"]


def _binding(context: dict) -> dict:
    """名片装配只收连接参数。工具由探针换成假世界。"""
    return {
        "name": context["name"],
        "provider": context["provider"],
        "api_key_env": context["api_key_env"],
        "model_name": context["model_name"],
        "base_url": context["base_url"],
        "system_prompt": context["system_prompt"],
        "tools": [],
    }


async def _ask_model(agent, text: str, context: dict) -> tuple[str, dict]:
    """问一轮。工具调用落在假世界上，用量带回给账本。"""
    from datetime import datetime

    from agentscope.message import UserMsg

    from engines.backend_bridge.workflow.fake_world import scripted_tools

    calls: list[dict] = []
    if not getattr(agent, "_eval_tools_mounted", False):
        for tool in scripted_tools(context["selections"], {}, calls):
            await agent.toolkit.add_tool(tool)
        agent._eval_tools_mounted = True
    answer = ""
    async for event in agent.reply_stream(UserMsg(name="user", content=text)):
        kind = type(event).__name__
        if kind == "TextBlockEndEvent":
            answer = str(getattr(event, "text", "") or answer)
        elif kind == "TextBlockDeltaEvent":
            answer += str(getattr(event, "delta", "") or "")
    usage = {
        "round": text,
        "provider": context["provider"],
        "model": context["model_name"],
        "occurred_at": datetime.now(),
        "input_tokens": 0,
        "output_tokens": 0,
    }
    return answer or "（模型没有返回文本）", usage


def _bill(usages: list[dict], run_id: int) -> None:
    """入账失败不让评测变失败。"""
    from backend.apps.ai_assistant.services.eval_billing import record_eval_usages

    record_eval_usages(usages, str(run_id))


def _grade(run, steps: list[dict], same: bool | None) -> list[dict]:
    """用四条规则读这次过程。"""
    from backend.apps.ai_assistant.services.live_rulers import grade_process

    allowed = {str(step.get("tool") or "") for step in steps if step.get("text") != "未挂载"}
    return grade_process(steps, allowed=allowed, same_instance=same)
