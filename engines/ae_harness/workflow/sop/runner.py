from __future__ import annotations

import time

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentscope.message import UserMsg
from agentscope.sop import SOP, SOPEngine, SOPStep

from engines.ae_harness.event import (
    AgentEventRecorder,
    HtmlReportRenderer,
    RunRecord,
)

from .spec import SopSpec

__all__ = ["SopResult", "StepOutcome", "build_sop", "run_sop"]

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


@dataclass
class StepOutcome:
    subject: str
    passed: bool
    attempts: int
    message: str = ""
    expected: str = ""


@dataclass
class SopResult:
    phase: str
    steps: list[StepOutcome] = field(default_factory=list)
    record: RunRecord | None = None


def build_sop(executor: Any, verifier: Any, spec: SopSpec) -> SOP:
    return SOP(
        name=spec.name,
        description=spec.description,
        steps=[
            SOPStep(
                subject=step.subject,
                description=step.description,
                executor=executor,
                verifier=verifier,
                max_attempts=step.max_attempts,
            )
            for step in spec.steps
        ],
    )


def _collect_schemas(agents: list[Any]) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for agent in agents:
        toolkit = getattr(agent, "toolkit", None)
        if toolkit is None:
            continue
        for item in getattr(toolkit, "_tools", {}).values():
            name = getattr(item, "name", "")
            schema = getattr(item, "input_schema", None)
            if name and isinstance(schema, dict):
                schemas[name] = {"name": name, "parameters": schema}
    return schemas


async def _gather_schemas(agents: list[Any]) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for agent in agents:
        toolkit = getattr(agent, "toolkit", None)
        if toolkit is None:
            continue
        getter = getattr(toolkit, "get_tool_schemas", None)
        if getter is None:
            continue
        try:
            items = await getter()
        except Exception:  # noqa: BLE001 - 取不到就不展示，不影响主流程
            continue
        for item in items:
            function = item.get("function") if isinstance(item, dict) else None
            if isinstance(function, dict) and function.get("name"):
                schemas[function["name"]] = function
    return schemas or _collect_schemas(agents)


async def run_sop(
    executor: Any,
    verifier: Any,
    spec: SopSpec,
    *,
    log_dir: Path | None = None,
    role: str = "sop",
    renderer: HtmlReportRenderer | None = None,
    api_key_env: str = "",
    role_api_keys: dict[str, str] | None = None,
    role_models: dict[str, str] | None = None,
    observations: list | None = None,
) -> SopResult:
    target_dir = log_dir if log_dir is not None else DEFAULT_LOG_DIR
    sop = build_sop(executor, verifier, spec)
    engine = SOPEngine(sop)

    recorder = AgentEventRecorder(
        target_dir,
        role,
        api_key_env=api_key_env,
        role_api_keys=role_api_keys,
        role_models=role_models,
        sop_roles={
            str(getattr(executor, "name", "") or ""): "executor",
            str(getattr(verifier, "name", "") or ""): "verifier",
        },
        observations=observations,
    )
    recorder.begin(
        spec.task or spec.name,
        schemas=await _gather_schemas([executor, verifier]),
        sop_steps=[
            {"subject": step.subject, "description": step.description} for step in spec.steps
        ],
    )

    begin = time.perf_counter()
    async for event in engine.reply_stream(UserMsg(name="user", content=spec.task or spec.name)):
        recorder.on_event(event)
    cost_s = round(time.perf_counter() - begin, 2)
    record = recorder.finish(cost_s)

    painter = renderer or HtmlReportRenderer()
    painter.save(record)

    outcomes: list[StepOutcome] = []
    for step, state in zip(spec.steps, engine.state.steps):
        verdicts = getattr(state, "verifications", []) or []
        last = verdicts[-1] if verdicts else None
        outcomes.append(
            StepOutcome(
                subject=step.subject,
                passed=bool(last and last.passed),
                attempts=len(verdicts),
                message=(last.message if last else ""),
                expected=step.description,
            )
        )

    return SopResult(phase=str(engine.phase), steps=outcomes, record=record)
