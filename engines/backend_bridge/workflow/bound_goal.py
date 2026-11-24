from __future__ import annotations

from pathlib import Path

from engines.ae_harness.workflow.goal import GoalResult, run_goal
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.workflow.bound_roles import RoleBinding, build_bound_roles
from engines.backend_bridge.workflow.cancel import cancel_controls

__all__ = ["run_bound_goal"]


async def run_bound_goal(
    task: str,
    executor: RoleBinding,
    verifier: RoleBinding,
    *,
    max_iters: int = 3,
    report_root: Path | None = None,
    task_id: int = 0,
) -> GoalResult:
    roles = await build_bound_roles(
        executor, verifier, controls=cancel_controls(task_id), kind="case_authoring"
    )
    return await run_goal(
        roles.executor.agent,
        roles.verifier.agent,
        task,
        max_iters=max_iters,
        log_dir=report_root if report_root is not None else REPORT_ROOT,
        api_key_env=roles.executor.api_key_env,
        observations=roles.observer.records,
    )
