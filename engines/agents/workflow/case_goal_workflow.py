"""
文件名: ➡️ case_goal_workflow.py 🏁
路径: ➡️ engines/agents/workflow/case_goal_workflow.py 🏁
模块功能：➡️ 2. run_goal_module: 用 GoalPipeline 跑单模块，编写角色把全文存入 ModuleStor 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_goal_workflow 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. GoalModuleResult: 一个模块经 GoalPipeline 编写/验收后的结果。
2. run_goal_module: 用 GoalPipeline 跑单模块，编写角色把全文存入 ModuleStore，
🏁
关联模块：➡️
1. engines.agents.agent_builders: 导入 build_case_verifier_goal, build_case_writer_goal
2. engines.agents.tools.tool_case_module_store: 导入 ModuleStore
3. engines.agents.tools_config: 导入 build_case_module_store_tools
4. engines.agents.workflow.case_document_check: 导入 check_and_fix_document
5. engines.agents.workflow.ui_auto_workflow: 导入 show_event
🏁
测试：➡️
1. tests/graybox/unit/test_case_goal_workflow.py: GoalPipeline 模块池：模块存储、单模块判定与截断兜底
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.message import Msg, UserMsg
from agentscope.pipeline import GoalPipeline

from engines.agents.agent_builders import build_case_verifier_goal, build_case_writer_goal
from engines.agents.tools.tool_case_module_store import ModuleStore
from engines.agents.tools_config import build_case_module_store_tools
from engines.agents.workflow.case_document_check import check_and_fix_document
from engines.agents.workflow.ui_auto_workflow import show_event

# 最多 3 轮真实驳回；每轮内部 GoalPipeline 只判一次，避免它自己提前结束。
CASE_GOAL_MAX_ITERS = 3
# 结构化输出失败的重问次数（不消耗真实驳回预算）。
CASE_GOAL_MAX_RETRIES = 3
# 文档短于该长度视为没有交付（例如工具参数被截断）。
CASE_GOAL_MIN_DOCUMENT_CHARS = 200
# 单次输出达到该值视为顶到模型上限。
CASE_GOAL_OUTPUT_LIMIT = 60_000


@dataclass(frozen=True)
class GoalModuleResult:
    """
    一个模块的 GoalPipeline 运行结果。

    Attributes:
        document: 从 ModuleStore 读到的完整文档。
        passed: 最后一次验收是否为 pass。
        verdicts: 历次验收，元素为 (passed, message, verifier)。
        truncated: 文档缺失/过短，或输出顶到上限。
        max_output_tokens: 本模块各次模型调用的最大输出 token。
    """

    document: str
    passed: bool
    verdicts: tuple[tuple[bool, str, str], ...]
    truncated: bool
    max_output_tokens: int


def _capture_verdict(agent, holder: list[dict]) -> None:
    """包一层成员 reply_stream，在 GoalPipeline 消费最终消息前留下判决。"""

    original = agent.reply_stream

    async def stream(*args, **kwargs):
        async for event in original(*args, **kwargs):
            if isinstance(event, Msg) and event.structured_output:
                if event.structured_output.get("result"):
                    holder.append(dict(event.structured_output))
            yield event

    agent.reply_stream = stream


def _retry_input(run_input: str, document: str, verdict: dict) -> str:
    """把上一版文档与驳回意见拼成下一轮输入。"""
    previous = document.strip() or "（上一轮没有保存任何文档）"
    return (
        run_input
        + "\n\n## 上一轮交付文档（只修下面意见点名的问题；未点名的段落、表格行、ID 与数字逐字保留）\n"
        + previous
        + "\n\n## 上一轮验收意见（逐条修复；不要重写无关内容）\n"
        + str(verdict.get("message") or "")
    )


async def run_goal_module(
    run_input: str,
    module_key: str,
    store: ModuleStore,
) -> GoalModuleResult:
    """
    用 GoalPipeline 跑一个模块。

    Args:
        run_input: 交给编写角色的完整开场输入（含本模块片段与编号区段）。
        module_key: 模块 KEY，用于从 ModuleStore 取文档。
        store: 本次任务共享的模块存储。

    Returns:
        模块文档、最终判定、历次判决与截断标记。
    """
    verdicts: list[tuple[bool, str, str]] = []
    max_tokens = 0
    current_input = run_input
    last_document = ""

    for _round in range(CASE_GOAL_MAX_ITERS):
        writer = build_case_writer_goal()
        verifier = build_case_verifier_goal()
        await writer.toolkit.add_tool(build_case_module_store_tools(store, module_key))
        await verifier.toolkit.add_tool(
            build_case_module_store_tools(store, module_key, read_only=True)
        )

        captured: list[dict] = []
        _capture_verdict(verifier, captured)
        pipeline = GoalPipeline(
            executor=writer,
            verifier=verifier,
            verifier_reset_context=True,
            max_iters=1,
            max_retries=CASE_GOAL_MAX_RETRIES,
        )
        models = {
            writer.name: writer.model.model,
            verifier.name: verifier.model.model,
        }
        buf: dict = {}
        async for event in pipeline.reply_stream(UserMsg(name="user", content=current_input)):
            if type(event).__name__ == "ModelCallEndEvent":
                max_tokens = max(max_tokens, int(getattr(event, "output_tokens", 0) or 0))
            if isinstance(event, Msg):
                output = event.structured_output or {}
                if output.get("result"):
                    captured.append(dict(output))
                continue
            await show_event(event, buf, models, flush=True)

        last_document = store.get(module_key)
        fixed_document, issues = (
            check_and_fix_document(last_document) if last_document else (last_document, [])
        )
        if fixed_document != last_document:
            store.save(module_key, fixed_document)
            last_document = fixed_document
        if not captured and not issues:
            # 没有合法判决也没有确定性问题：按失败处理，交给上层拆分/报错
            break
        verdict = captured[-1] if captured else {"result": "fail", "message": ""}
        passed = verdict.get("result") == "pass" and not issues
        verdicts.append((passed, str(verdict.get("message") or ""), verifier.name))
        deterministic = ""
        if issues:
            deterministic = "【确定性问题】" + "；".join(issues[:20])
            verdicts.append((False, deterministic, "case_deterministic_check"))
        if passed or not last_document:
            break
        if _round + 1 < CASE_GOAL_MAX_ITERS:
            feedback = str(verdict.get("message") or "")
            if deterministic:
                feedback = deterministic + "\n" + feedback
            current_input = _retry_input(run_input, last_document, {"message": feedback})

    document = store.get(module_key)
    truncated = len(document.strip()) < CASE_GOAL_MIN_DOCUMENT_CHARS
    passed = bool(verdicts) and verdicts[-1][0] and not truncated
    return GoalModuleResult(
        document=document,
        passed=passed,
        verdicts=tuple(verdicts),
        truncated=truncated,
        max_output_tokens=max_tokens,
    )
