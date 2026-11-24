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
