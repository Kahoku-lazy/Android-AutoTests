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
