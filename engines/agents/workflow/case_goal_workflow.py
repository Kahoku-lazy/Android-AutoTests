"""
文件名: ➡️ case_goal_workflow.py 🏁
路径: ➡️ engines/agents/workflow/case_goal_workflow.py 🏁
模块功能：➡️ 一条目标流水线跑完用例编写与验收：编写角色增量写产物，验收角色核对事实 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_goal_workflow 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. CaseAuthoringResult: 一次用例编写运行的产物、事实预检、历次判决与渲染结果。
2. run_case_authoring_artifact: 两角色一条目标流水线跑到底，执行者只构建一次。
3. 有确定性问题时即使验收判通过也不放行，并把问题写成一条独立判决。
4. 产物由 ArtifactStore 增量累积，文档与状态图由渲染器派生。
5. 角色与工具由 case_roles 装配好后传入，本模块只编排。
🏁
关联模块：➡️
1. engines/agents/case_roles: 导入 build_case_authoring_roles，成对装配编写/验收角色
2. engines/agents/workflow/case_artifact: 导入 Artifact, ArtifactStore
3. engines/agents/workflow/case_artifact_facts: 导入 FactReport, check_artifact_facts
4. engines/agents/workflow/case_artifact_render: 导入 render
5. engines/agents/workflow/ui_auto_workflow: 导入 show_event
🏁
测试：➡️
1. tests/graybox/unit/test_case_goal_workflow.py: 单文件调试指令：python -m pytest tests/graybox/unit/test_case_goal_workflow.py -vv --tb=short
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from agentscope.message import Msg, UserMsg
from agentscope.pipeline import GoalPipeline

from engines.agents.case_roles import build_case_authoring_roles
from engines.agents.workflow.case_artifact import Artifact, ArtifactStore
from engines.agents.workflow.case_artifact_facts import FactReport, check_artifact_facts
from engines.agents.workflow.case_artifact_render import render
from engines.agents.workflow.ui_auto_workflow import show_event

__all__ = [
    "CASE_GOAL_MAX_ITERS",
    "CASE_GOAL_MAX_RETRIES",
    "CaseAuthoringResult",
    "build_case_run_input",
    "run_case_authoring_artifact",
]

# 最多 3 轮真实驳回；每轮内部只判一次，避免流水线自己提前结束
CASE_GOAL_MAX_ITERS = 3
# 结构化输出失败的重问次数（不消耗真实驳回预算）
CASE_GOAL_MAX_RETRIES = 3


@dataclass(frozen=True)
class CaseAuthoringResult:
    """
    一次用例编写运行的结果。

    Attributes:
        phase: `completed` 或 `failed`。
        artifact: 三段产物。
        facts: 事实预检结论。
        verdicts: 历次判决，元素为 (passed, message, verifier)。
        document: 渲染后的 Markdown 文档。
        reason: 失败原因；通过时为空。
        max_output_tokens: 各次模型调用里最大的输出 token 数。
    """

    phase: str
    artifact: Artifact
    facts: FactReport
    verdicts: tuple[tuple[bool, str, str], ...]
    document: str
    reason: str = ""
    max_output_tokens: int = 0

    @property
    def passed(self) -> bool:
        """最后一条判决通过、事实无确定性问题、且产物里有用例时才通过。"""
        if not self.artifact.cases:
            return False
        if not self.facts.passed:
            return False
        return bool(self.verdicts) and self.verdicts[-1][0]


def build_case_run_input(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
) -> str:
    """把需求正文与编写参数拼成交给编写角色的开场输入。

    Args:
        requirement_text: 需求正文。
        project_code: 项目代号，用于用例编号。
        version: 版本号，用于用例编号。

    Returns:
        带小标题的开场输入。

    Raises:
        ValueError: 需求正文为空白。
    """
    requirement = requirement_text.strip()
    if not requirement:
        raise ValueError("需求正文不能为空")
    return (
        "## 项目代号\n"
        f"{project_code.strip() or 'PROJ'}\n\n"
        "## 版本号\n"
        f"{version.strip() or 'V1'}\n\n"
        "## 需求正文\n"
        f"{requirement}\n"
    )


def _capture_output(agent, holder: list[dict], key: str) -> None:
    """包一层成员 reply_stream，在流水线消费最终消息前留下结构化输出。

    Args:
        agent: 被包装的角色。
        holder: 收集结构化输出的列表。
        key: 只收集含该键的结构化输出（`report` / `result`）。
    """

    original = agent.reply_stream

    async def stream(*args, **kwargs):
        async for event in original(*args, **kwargs):
            if isinstance(event, Msg) and event.structured_output:
                if event.structured_output.get(key):
                    holder.append(dict(event.structured_output))
            yield event

    agent.reply_stream = stream


async def run_case_authoring_artifact(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
) -> CaseAuthoringResult:
    """用一条目标流水线跑完整个需求的用例编写。

    执行者只构建一次：驳回意见由流水线作为系统消息回给同一个执行者，不再重建
    角色、也不再把上一版产物全文拼进输入。

    Args:
        requirement_text: 需求正文。
        project_code: 项目代号。
        version: 版本号。

    Returns:
        产物、事实预检、历次判决与渲染结果。

    Raises:
        ValueError: 需求正文为空白。
    """
    run_input = build_case_run_input(requirement_text, project_code, version)
    store = ArtifactStore()
    writer, verifier = await build_case_authoring_roles(store, requirement_text=requirement_text)

    reports: list[dict] = []
    verdicts_raw: list[dict] = []
    # 验证者的最终消息不会被流水线吐出来，只能在它自己的流里截一份
    _capture_output(verifier, verdicts_raw, "result")

    pipeline = GoalPipeline(
        executor=writer,
        verifier=verifier,
        verifier_reset_context=True,
        max_iters=CASE_GOAL_MAX_ITERS,
        max_retries=CASE_GOAL_MAX_RETRIES,
    )
    models = {
        writer.name: writer.model.model,
        verifier.name: verifier.model.model,
    }
    max_tokens = 0
    buf: dict = {}
    async for event in pipeline.reply_stream(UserMsg(name="user", content=run_input)):
        if type(event).__name__ == "ModelCallEndEvent":
            max_tokens = max(max_tokens, int(getattr(event, "output_tokens", 0) or 0))
        if isinstance(event, Msg):
            output = event.structured_output or {}
            if output.get("report"):
                reports.append(dict(output))
            if output.get("result"):
                verdicts_raw.append(dict(output))
            continue
        await show_event(event, buf, models, flush=True)

    if reports:
        store.report = str(reports[-1].get("report") or "")
    facts = check_artifact_facts(store.artifact(), requirement_text)
    document, diagram = render(store.artifact())
    artifact = replace(store.artifact(), diagram=diagram, report=store.report)

    verdicts: list[tuple[bool, str, str]] = []
    for item in verdicts_raw:
        verdicts.append(
            (
                str(item.get("result") or "") == "pass",
                str(item.get("message") or ""),
                verifier.name,
            )
        )
    if not facts.passed:
        blockers = "；".join(issue.render() for issue in facts.blocking[:20])
        verdicts.append((False, f"【确定性问题】{blockers}", "case_artifact_facts"))
    passed = bool(artifact.cases) and facts.passed and bool(verdicts) and verdicts[-1][0]
    reason = ""
    if not passed:
        if not artifact.cases:
            reason = "未产出合法结构化输出：产物里没有用例"
        elif verdicts:
            reason = verdicts[-1][1]

    return CaseAuthoringResult(
        phase="completed" if passed else "failed",
        artifact=artifact,
        facts=facts,
        verdicts=tuple(verdicts),
        document=document,
        reason=reason,
        max_output_tokens=max_tokens,
    )
