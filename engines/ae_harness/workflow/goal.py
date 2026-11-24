"""
文件名: ➡️ goal.py 🏁
路径: ➡️ engines/ae_harness/workflow/goal.py 🏁
模块功能：➡️ 把执行者与验收者跑成一次目标流水线，并产出记录与报告 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.goal 🏁
时间：➡️ 2026-11-19 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_goal: 执行者产出、验收者判定、不通过退回重做，直到通过或用尽次数。
2. 不建角色、不挂工具、不保存具体目标；目标正文由调用方随任务传入。
🏁
关联模块：➡️
1. agentscope.pipeline: GoalPipeline。
2. engines.ae_harness.agents.messages: 导入 user_message，把目标正文包成用户消息。
3. engines.ae_harness.event: 导入记录器与报告渲染器。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_goal_pipeline.py: 退回一次后通过与用尽次数
🏁
"""

from __future__ import annotations

import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.pipeline import GoalPipeline

from engines.ae_harness.agents.messages import user_message
from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer, RunRecord

__all__ = ["GoalResult", "run_goal"]

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


@dataclass
class GoalResult:
    """
    一次目标流水线的结果。

    Attributes:
        passed: 验收是否通过。
        verdict: 验收结论，pass / fail / impossible 之一；没有合法结论时为空串。
        message: 验收说明；未通过时是缺什么。
        record: 整轮记录。
    """

    passed: bool
    verdict: str
    message: str
    record: RunRecord | None = None


async def run_goal(
    executor: Any,
    verifier: Any,
    task: str,
    *,
    max_iters: int = 3,
    max_retries: int = 3,
    log_dir: Path | None = None,
    role: str = "goal",
    renderer: HtmlReportRenderer | None = None,
    api_key_env: str = "",
    observations: list | None = None,
) -> GoalResult:
    """
    跑一遍目标流水线：执行者产出，验收者不通过就退回重做。

    Args:
        executor: 执行者，负责达成目标。
        verifier: 验收者，负责判定。
        task: 目标正文，既是交给执行者的任务，也是验收者对照的目标。
        max_iters: 最多允许被驳回几次。
        max_retries: 任一方没有给出合法结构化输出时，最多重问几次。
        log_dir: 产物根目录；不传则落在 ae_harness/logs。
        role: 角色名，写进产物文件名。
        renderer: 报告渲染器；不传则用默认配置。
        api_key_env: 密钥环境变量名，写进记录。
        observations: 观测中间件的记录队列。

    Returns:
        目标结果，含是否通过、验收结论与整轮记录。
    """
    pipeline = GoalPipeline(
        executor=executor,
        verifier=verifier,
        max_iters=max_iters,
        max_retries=max_retries,
    )
    recorder = AgentEventRecorder(
        log_dir if log_dir is not None else DEFAULT_LOG_DIR,
        role,
        api_key_env=api_key_env,
        observations=observations,
    )
    recorder.begin(task)
    begin = time.perf_counter()
    verdict, message = "", ""
    async for event in pipeline.reply_stream(user_message(task)):
        recorder.on_event(event)
        output = getattr(event, "structured_output", None)
        if isinstance(output, dict) and output.get("result") in {"pass", "fail", "impossible"}:
            verdict = str(output["result"])
            message = str(output.get("message") or "")
    record = recorder.finish(round(time.perf_counter() - begin, 2))
    (renderer or HtmlReportRenderer()).save(record)
    return GoalResult(passed=verdict == "pass", verdict=verdict, message=message, record=record)
