"""
文件名: ➡️ team.py 🏁
路径: ➡️ engines/ae_harness/workflow/team.py 🏁
模块功能：➡️ 把队长与成员跑成一次团队流水线，并产出记录与报告 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.team 🏁
时间：➡️ 2026-11-19 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. TeamRole: 一个成员的智能体与它擅长什么。
2. run_team: 队长通过工具把任务分派给成员，成员的回复作为工具结果交回队长。
3. 不建角色、不决定成员名单；名单与任务正文由调用方传入。
🏁
关联模块：➡️
1. agentscope.pipeline: TeamPipeline 与 TeamMember。
2. engines.ae_harness.agents.messages: 导入 user_message，把任务正文包成用户消息。
3. engines.ae_harness.event: 导入记录器与报告渲染器。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_team_pipeline.py: 成员被分派与重名被拒绝
🏁
"""

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
    """
    团队里的一个成员。

    Attributes:
        agent: 成员智能体，它的 name 就是队长分派时引用的名字。
        description: 成员擅长什么、何时分派给它。
    """

    agent: Any
    description: str


@dataclass
class TeamResult:
    """
    一次团队流水线的结果。

    Attributes:
        reply: 队长的最终回复正文。
        record: 整轮记录。
    """

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
    """
    跑一遍团队流水线：队长分派，成员各自完成，结果交回队长。

    Args:
        leader: 队长，需要带工具箱。
        members: 成员清单。名字必须互不相同，且不能与队长同名。
        task: 交给队长的任务正文。
        reset_members: 队长每次回复结束后是否清空成员上下文。
        log_dir: 产物根目录；不传则落在 ae_harness/logs。
        role: 角色名，写进产物文件名。
        renderer: 报告渲染器；不传则用默认配置。
        api_key_env: 密钥环境变量名，写进记录。
        observations: 观测中间件的记录队列。

    Returns:
        团队结果，含队长的最终回复与整轮记录。

    Raises:
        ValueError: 成员重名或与队长同名，由框架在构造时抛出。
    """
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
