from __future__ import annotations

import time

from pathlib import Path
from typing import Any, Callable

from engines.ae_harness.event import (
    AlignedReportRenderer,
    AlignedRun,
    RawEventDump,
    summarize,
)
from engines.ae_harness.middleware.control import BudgetExceeded, RunCancelled
from engines.ae_harness.workflow.sop import SopSpec, run_sop
from engines.backend_bridge.device_guard import require_online, serial_lock
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.workflow.bound_roles import RoleBinding, build_bound_roles
from engines.backend_bridge.workflow.cancel import cancel_controls
from engines.backend_bridge.workflow.sop_ui import SopRunResult, SopStepResult
from utils.logs import agent_event_log

__all__ = ["run_bound_sop"]

SOP_ROLE = "sop_bound"
_STEP_START = "SOP_STEP_STARTED"
_SERIAL_OPENING = "本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。"


def _with_serial(spec: SopSpec, serial: str) -> None:
    clean = serial.strip()
    if not clean:
        return
    opening = _SERIAL_OPENING.format(serial=clean)
    spec.task = f"{spec.task}\n\n{opening}".strip() if spec.task else opening


async def _tool_schemas(agent: Any) -> list[dict]:
    getter = getattr(getattr(agent, "toolkit", None), "get_tool_schemas", None)
    if getter is None:
        return []
    rows: list[dict] = []
    for item in await getter():
        function = item.get("function") if isinstance(item, dict) else None
        if isinstance(function, dict) and function.get("name"):
            rows.append(function)
    return rows


async def _role_inputs(roles: Any, executor: RoleBinding, verifier: RoleBinding) -> list[dict]:
    return [
        {
            "name": str(getattr(roles.executor.agent, "name", "") or ""),
            "role": "executor",
            "system_prompt": executor.system_prompt,
            "tool_schemas": await _tool_schemas(roles.executor.agent),
        },
        {
            "name": str(getattr(roles.verifier.agent, "name", "") or ""),
            "role": "verifier",
            "system_prompt": verifier.system_prompt,
            "tool_schemas": await _tool_schemas(roles.verifier.agent),
        },
    ]


def _run_meta(
    executor: RoleBinding,
    verifier: RoleBinding,
    inputs: list[dict],
    serial: str,
    spec: SopSpec,
) -> dict:
    roles = [
        {
            "name": item["name"],
            "role": item["role"],
            "model": executor.model_name if item["role"] == "executor" else verifier.model_name,
            "api_key_env": (
                executor.api_key_env if item["role"] == "executor" else verifier.api_key_env
            ),
        }
        for item in inputs
    ]
    return {
        "role": SOP_ROLE,
        "agent": str(roles[0]["name"]) if roles else "",
        "model": executor.model_name,
        "api_key_env": executor.api_key_env,
        "serial": serial,
        "sop_name": spec.name,
        "sop_description": spec.description,
        "roles": roles,
    }


class _SopCapture:
    def __init__(self, run: dict, inputs: dict) -> None:
        self._run = run
        self._inputs = inputs
        self._raw: RawEventDump | None = None
        self._aligned: AlignedRun | None = None
        self._recorder: Any = None
        self._started = 0.0
        self._step = 0

    def start(self, recorder: Any) -> None:
        self._recorder = recorder
        self._started = time.perf_counter()
        stem = recorder.log_path.stem
        self._raw = RawEventDump(recorder.log_path.with_name(f"{stem}.raw.jsonl"))
        self._raw.begin({**self._run, "user_message": self._inputs.get("user_message", "")})
        self._aligned = AlignedRun(recorder.log_path.with_name(f"{stem}.aligned.json"))
        self._aligned.begin(self._run, self._inputs)

    def event(self, event: Any) -> None:
        if self._raw is not None:
            self._raw.feed(event)
        if self._aligned is None:
            return
        self._aligned.feed(event)
        if (
            type(event).__name__ == "CustomEvent"
            and str(getattr(event, "name", "") or "") == _STEP_START
        ):
            self._step += 1
        reply_id = str(getattr(event, "reply_id", "") or "")
        if reply_id and self._step:
            self._aligned.bind_step_reply(self._step, reply_id)

    def observation(self, record: Any) -> None:
        if self._aligned is not None:
            self._aligned.observe(record)

    def finish(self, record: Any, result: Any, tokens: dict) -> Path | None:
        if self._aligned is None or self._raw is None:
            return None
        steps = [
            {
                "index": index,
                "subject": item.subject,
                "description": item.expected,
                "passed": bool(item.passed),
                "attempts": int(item.attempts),
                "message": item.message,
                "expected": item.expected,
                "reply_ids": [],
            }
            for index, item in enumerate(result.steps, 1)
        ]
        self._aligned.set_steps(steps)
        paths = {
            "log_path": record.log_path.as_posix(),
            "html_path": record.html_path.as_posix(),
            "raw_path": self._raw.path.as_posix(),
            "aligned_path": self._aligned.path.as_posix(),
        }
        self._raw.end(
            {
                "cost_s": record.cost_s,
                "final_text": record.final_text,
                "phase": result.phase,
                **paths,
            }
        )
        self._raw.close()
        aligned_path = self._aligned.end(
            {
                "cost_s": record.cost_s,
                "final_text": record.final_text,
                "phase": result.phase,
                "tokens": tokens,
                "usages": [item.as_dict() for item in record.usages],
                "steps_total": len(steps),
                "steps_passed": sum(1 for item in steps if item["passed"]),
                **paths,
            }
        )
        AlignedReportRenderer().save(self._aligned.document, record.html_path)
        return aligned_path

    def abort(self, exc: Exception) -> Path | None:
        recorder = self._recorder
        if recorder is None or self._aligned is None or self._raw is None:
            return None
        reason = str(exc).strip() or type(exc).__name__
        cost_s = round(time.perf_counter() - self._started, 2)
        try:
            record = recorder.finish(cost_s)
            summary = summarize(record.usages).as_dict()
            tokens = {
                "input": summary.get("input", 0),
                "output": summary.get("output", 0),
                "cache_hit": summary.get("cache_hit", 0),
                "cache_creation": summary.get("cache_creation", 0),
            }
            self._aligned.set_steps([])
            paths = {
                "log_path": record.log_path.as_posix(),
                "html_path": record.html_path.as_posix(),
                "raw_path": self._raw.path.as_posix(),
                "aligned_path": self._aligned.path.as_posix(),
            }
            self._raw.end(
                {
                    "cost_s": record.cost_s,
                    "final_text": record.final_text,
                    "phase": "aborted",
                    "abort_reason": reason,
                    **paths,
                }
            )
            self._raw.close()
            self._aligned.end(
                {
                    "cost_s": record.cost_s,
                    "final_text": record.final_text,
                    "phase": "aborted",
                    "tokens": tokens,
                    "usages": [item.as_dict() for item in record.usages],
                    "steps_total": 0,
                    "steps_passed": 0,
                    "aborted": True,
                    "abort_reason": reason,
                    **paths,
                }
            )
            self._aligned.document["run"]["运行中断"] = reason
            AlignedReportRenderer().save(self._aligned.document, record.html_path)
        except Exception:
            agent_event_log.exception("SOP 中断报告生成失败")
            return None
        return record.html_path


async def run_bound_sop(
    spec: SopSpec,
    executor: RoleBinding,
    verifier: RoleBinding,
    *,
    serial: str = "",
    report_root: Path | None = None,
    controls: list | None = None,
    task_id: int = 0,
    on_abort: Callable[[Path | None, Exception], None] | None = None,
) -> SopRunResult:
    clean = require_online(serial)
    _with_serial(spec, clean)
    merged = [*(controls or []), *cancel_controls(task_id)]
    roles = await build_bound_roles(executor, verifier, controls=merged, capture_messages=True)
    root = report_root if report_root is not None else REPORT_ROOT
    role_models = {
        roles.executor.agent.name: executor.model_name,
        roles.verifier.agent.name: verifier.model_name,
    }
    inputs = await _role_inputs(roles, executor, verifier)
    run_meta = _run_meta(executor, verifier, inputs, clean, spec)
    capture = _SopCapture(
        run_meta,
        {
            "system_prompt": executor.system_prompt,
            "user_message": spec.task or spec.name,
            "tool_schemas": inputs[0]["tool_schemas"],
            "roles": inputs,
        },
    )
    try:
        with serial_lock(clean):
            result = await run_sop(
                roles.executor.agent,
                roles.verifier.agent,
                spec,
                log_dir=root,
                role=SOP_ROLE,
                render_report=False,
                on_begin=capture.start,
                on_event=capture.event,
                on_observation=capture.observation,
                api_key_env=roles.executor.api_key_env,
                role_api_keys={
                    roles.executor.agent.name: roles.executor.api_key_env,
                    roles.verifier.agent.name: roles.verifier.api_key_env,
                },
                role_models=role_models,
                observations=roles.observer.records,
            )
    except (RunCancelled, BudgetExceeded):
        raise
    except Exception as exc:
        report_path = capture.abort(exc)
        if on_abort is not None:
            try:
                on_abort(report_path, exc)
            except Exception:
                agent_event_log.exception("SOP 失败回调执行失败")
        raise
    record = result.record
    totals = summarize(record.usages) if record is not None else None
    summary = totals.as_dict() if totals is not None else {}
    tokens = {
        "input": summary.get("input", 0),
        "output": summary.get("output", 0),
        "cache_hit": summary.get("cache_hit", 0),
        "cache_creation": summary.get("cache_creation", 0),
    }
    if record is not None:
        capture.finish(record, result, tokens)
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
        tokens=tokens,
        by_api_key_env=dict(totals.by_api_key_env) if totals is not None else {},
        usages=[item.as_dict() for item in record.usages] if record is not None else [],
        cost_s=float(record.cost_s) if record is not None else 0.0,
    )
