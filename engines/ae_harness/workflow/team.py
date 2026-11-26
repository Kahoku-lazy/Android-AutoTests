from __future__ import annotations

import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.pipeline import TeamMember, TeamPipeline

from engines.ae_harness.agents.messages import user_message
from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer, RunRecord

__all__ = ["TeamResult", "TeamRole", "run_team"]

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


@dataclass(frozen=True)
class TeamRole:
    agent: Any
    description: str


@dataclass
class TeamResult:
    reply: str
    record: RunRecord | None = None


async def run_team(
    leader: Any,
    members: list[TeamRole],
    task: str,
    *,
    reset_members: bool = True,
    log_dir: Path | None = None,
    role: str = "team",
    renderer: HtmlReportRenderer | None = None,
    api_key_env: str = "",
    observations: list | None = None,
) -> TeamResult:
    pipeline = TeamPipeline(
        leader=leader,
        members=[TeamMember(agent=item.agent, description=item.description) for item in members],
        reset_members=reset_members,
    )
    recorder = AgentEventRecorder(
        log_dir if log_dir is not None else DEFAULT_LOG_DIR,
        role,
        api_key_env=api_key_env,
        observations=observations,
    )
    recorder.begin(task)
    begin = time.perf_counter()
    reply = ""
    async for event in pipeline.reply_stream(user_message(task)):
        recorder.on_event(event)
        text = getattr(event, "get_text_content", None)
        if callable(text):
            content = text()
            if content:
                reply = str(content)
    record = recorder.finish(round(time.perf_counter() - begin, 2))
    (renderer or HtmlReportRenderer()).save(record)
    return TeamResult(reply=reply, record=record)
