"""
文件名: ➡️ bound_team.py 🏁
路径: ➡️ engines/backend_bridge/workflow/bound_team.py 🏁
模块功能：➡️ 用名片绑定参数跑一次团队流水线 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.bound_team 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_bound_team: 用队长绑定与成员绑定装配团队，交给 run_team。
2. 不读库、不校验拆解正文；正文校验由调用方在拿到回复后做。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.team: 导入 TeamRole 与 run_team。
2. engines.backend_bridge.workflow.bound_roles: 导入 RoleBinding 与 build_bound_roles。
3. engines.backend_bridge.workflow.cancel: 导入 cancel_controls。
4. engines.backend_bridge.reports: 报告路径唯一来源。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from pathlib import Path

from engines.ae_harness.workflow.team import TeamResult, TeamRole, run_team
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.workflow.bound_roles import RoleBinding, build_bound_agent
from engines.backend_bridge.workflow.cancel import cancel_controls

__all__ = ["run_bound_team"]


async def run_bound_team(
    task: str,
    leader: RoleBinding,
    members: list[tuple[RoleBinding, str]],
    *,
    report_root: Path | None = None,
    task_id: int = 0,
) -> TeamResult:
    """
    用队长与成员绑定跑一次团队流水线。

    Args:
        task: 交给队长的任务正文。
        leader: 队长绑定。
        members: 成员绑定与各自擅长什么的说明。
        report_root: 报告根目录；不传则用平台报告根。
        task_id: 平台任务号，用于挂取消中间件；0 表示不挂。

    Returns:
        团队流水线的结果。

    Raises:
        ValueError: 连接参数不合法、提示词为空，或成员重名。
    """
    controls = cancel_controls(task_id)
    leader_bundle, observer = await build_bound_agent(
        leader, controls=controls, kind="requirement_breakdown"
    )
    roles: list[TeamRole] = []
    for binding, description in members:
        member, _ = await build_bound_agent(
            binding, observer=observer, controls=controls, kind="requirement_breakdown"
        )
        roles.append(TeamRole(agent=member.agent, description=description))
    return await run_team(
        leader_bundle.agent,
        roles,
        task,
        log_dir=report_root if report_root is not None else REPORT_ROOT,
        api_key_env=leader_bundle.api_key_env,
        observations=observer.records,
    )
