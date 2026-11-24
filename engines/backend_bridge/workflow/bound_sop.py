"""
文件名: ➡️ bound_sop.py 🏁
路径: ➡️ engines/backend_bridge/workflow/bound_sop.py 🏁
模块功能：➡️ 用名片绑定参数跑一次执行加验收 SOP 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.bound_sop 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-17 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_bound_sop: 接收已解析的 SopSpec 与一对绑定，装配后交给 run_sop。
2. 有 serial 才追加开场模板；没有时不拒绝。
3. 不读步骤键，不查库，一次运行新建一对角色。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.sop: 导入 SopSpec 与 run_sop。
2. engines.backend_bridge.workflow.bound_roles: 导入 RoleBinding 与 build_bound_roles。
3. engines.backend_bridge.workflow.cancel: 导入 cancel_controls，按任务号挂取消中间件。
4. engines.backend_bridge.reports: 报告路径唯一来源。
5. engines.ae_harness.event: 导入 summarize，汇总四类 token。
6. engines.backend_bridge.workflow.sop_ui: 复用 SopRunResult 的结果形状。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from pathlib import Path

from engines.ae_harness.event import summarize
from engines.ae_harness.workflow.sop import SopSpec, run_sop
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.workflow.bound_roles import RoleBinding, build_bound_roles
from engines.backend_bridge.workflow.cancel import cancel_controls
from engines.backend_bridge.workflow.sop_ui import SopRunResult, SopStepResult

__all__ = ["run_bound_sop"]

SOP_ROLE = "sop_bound"
_SERIAL_OPENING = "本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。"


def _with_serial(spec: SopSpec, serial: str) -> None:
    """
    有设备序列号时把开场模板追加到任务描述。

    Args:
        spec: 已解析的流程；只改它的 task 字段。
        serial: 设备序列号；空串时不做任何事。
    """
    clean = serial.strip()
    if not clean:
        return
    opening = _SERIAL_OPENING.format(serial=clean)
    spec.task = f"{spec.task}\n\n{opening}".strip() if spec.task else opening


async def run_bound_sop(
    spec: SopSpec,
    executor: RoleBinding,
    verifier: RoleBinding,
    *,
    serial: str = "",
    report_root: Path | None = None,
    controls: list | None = None,
    task_id: int = 0,
) -> SopRunResult:
    """
    用一对绑定跑一次 SOP。

    不读步骤键，也不因设备序列号为空而拒绝。取消、观测和报告目录沿用平台入口。

    Args:
        spec: 已解析的流程定义。
        executor: 执行侧绑定。
        verifier: 验收侧绑定。
        serial: 设备序列号；有值才追加开场模板。
        report_root: 报告根目录；不传则用平台报告根。
        controls: 额外中间件；不传则只挂观测与取消。
        task_id: 平台任务 id；登记过取消令牌时自动挂上取消中间件。

    Returns:
        本次运行的每步结论、产物路径与用量汇总。

    Raises:
        ValueError: 连接参数不合法，或系统提示词为空。
        ToolSelectionError: 任一侧勾选含未知工具名。
    """
    _with_serial(spec, serial)
    merged = [*(controls or []), *cancel_controls(task_id)]
    roles = await build_bound_roles(executor, verifier, controls=merged)
    root = report_root if report_root is not None else REPORT_ROOT
    role_models = {
        roles.executor.agent.name: executor.model_name,
        roles.verifier.agent.name: verifier.model_name,
    }
    result = await run_sop(
        roles.executor.agent,
        roles.verifier.agent,
        spec,
        log_dir=root,
        role=SOP_ROLE,
        api_key_env=roles.executor.api_key_env,
        role_api_keys={
            roles.executor.agent.name: roles.executor.api_key_env,
            roles.verifier.agent.name: roles.verifier.api_key_env,
        },
        role_models=role_models,
        observations=roles.observer.records,
    )
    record = result.record
    totals = summarize(record.usages) if record is not None else None
    summary = totals.as_dict() if totals is not None else {}
    return SopRunResult(
        phase=result.phase,
        steps=[
            SopStepResult(
                subject=item.subject,
                passed=item.passed,
                attempts=item.attempts,
                message=item.message,
                expected=item.expected,
            )
            for item in result.steps
        ],
        report_path=record.html_path if record is not None else None,
        log_path=record.log_path if record is not None else None,
        model=executor.model_name,
        tokens={
            "input": summary.get("input", 0),
            "output": summary.get("output", 0),
            "cache_hit": summary.get("cache_hit", 0),
            "cache_creation": summary.get("cache_creation", 0),
        },
        by_api_key_env=dict(totals.by_api_key_env) if totals is not None else {},
        usages=[item.as_dict() for item in record.usages] if record is not None else [],
        cost_s=float(record.cost_s) if record is not None else 0.0,
    )
