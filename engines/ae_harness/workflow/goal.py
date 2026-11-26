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
