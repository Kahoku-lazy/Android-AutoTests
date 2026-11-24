"""
文件名: ➡️ bound_goal.py 🏁
路径: ➡️ engines/backend_bridge/workflow/bound_goal.py 🏁
模块功能：➡️ 用名片绑定参数跑一次目标流水线 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.bound_goal 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_bound_goal: 用一对绑定装配执行者与验收者，交给 run_goal。
2. 不读库、不读步骤文件；目标正文由调用方传入。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.goal: 导入 run_goal。
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
    """
    用一对绑定跑一次目标流水线。

    Args:
        task: 目标正文。
        executor: 执行侧绑定。
        verifier: 验收侧绑定。
        max_iters: 最多允许被驳回几次。
        report_root: 报告根目录；不传则用平台报告根。
        task_id: 平台任务号，用于挂取消中间件；0 表示不挂。

    Returns:
        目标流水线的结果。

    Raises:
        ValueError: 连接参数不合法或提示词为空。
    """
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
