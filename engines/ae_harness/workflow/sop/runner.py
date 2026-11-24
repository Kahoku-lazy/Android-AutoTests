"""
文件名: ➡️ runner.py 🏁
路径: ➡️ engines/ae_harness/workflow/sop/runner.py 🏁
模块功能：➡️ 把执行者、验收者与步骤跑成一次 SOP，并产出记录与报告 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.sop.runner 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_sop: 调用方只传执行者、验收者、步骤与模型身份，其余由本函数处理。
2. 内部负责建 SOP、跑引擎、记录事件、渲染报告、汇总每步结论。
3. 不认识具体工具，也不建角色；执行者与验收者由调用方准备好。
4. 把执行者 / 验收者的名字映射传给记录器，报告角色按名字归属，不依赖回复顺序。
🏁
关联模块：➡️
1. agentscope.sop: SOP / SOPStep / SOPEngine。
2. engines.ae_harness.event: AgentEventRecorder / HtmlReportRenderer。
3. engines.ae_harness.workflow.sop.spec: SopSpec / StepSpec。
🏁
测试：➡️
1. 暂无
🏁
"""

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

# 默认产物目录：ae_harness/logs，调用方不传 log_dir 时用这个。
DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


@dataclass
class StepOutcome:
    """
    一步的最终结论。

    Attributes:
        subject: 步骤名。
        passed: 是否通过。
        attempts: 实际尝试次数。
        message: 最后一次验收的说明；通过时是依据，不通过时是缺什么。
        expected: 这一步必须达成的结果；步骤定义没有时为空串。
    """

    subject: str
    passed: bool
    attempts: int
    message: str = ""
    expected: str = ""


@dataclass
class SopResult:
    """
    一次流程运行的结果。

    Attributes:
        phase: 流程最终阶段（字符串形式）。
        steps: 每步的结论。
        record: 整轮记录，可直接交给渲染器或二次处理。
    """

    phase: str
    steps: list[StepOutcome] = field(default_factory=list)
    record: RunRecord | None = None


def build_sop(executor: Any, verifier: Any, spec: SopSpec) -> SOP:
    """
    按步骤定义组装 SOP。

    Args:
        executor: 执行者，跨步骤复用同一实例，上下文连续。
        verifier: 验收者，每步都会调用。
        spec: 流程定义。

    Returns:
        可交给 SOPEngine 运行的流程。
    """
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
    """
    取出各 Agent 的工具 schema，供报告详情面板展示。

    Args:
        agents: 需要取 schema 的 Agent 列表。

    Returns:
        工具名到 schema 的映射。
    """
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
    """
    异步取工具 schema；取不到时退回同步扫描。

    Args:
        agents: 需要取 schema 的 Agent 列表。

    Returns:
        工具名到 schema 的映射。
    """
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
    """
    跑一遍 SOP：记录事件、渲染报告、汇总每步结论。

    调用方只需要传执行者、验收者与步骤；记录与报告由本函数负责。

    Args:
        executor: 执行者。
        verifier: 验收者。
        spec: 流程定义（步骤、任务描述）。
        log_dir: 产物根目录；不传则落在 ae_harness/logs。
        role: 角色名，写进产物文件名。
        renderer: 报告渲染器；不传则用默认配置。
        api_key_env: 兜底密钥标签；角色没登记绑定时用它。
        role_api_keys: 角色名到密钥环境变量名的绑定；密钥绑在角色上，两个角色各用一把时传它。
        role_models: 角色名到模型名的绑定；不传时逐次用量的模型名为空串。
        observations: 观测中间件的记录队列；记录器按到达顺序取出并落盘。

    Returns:
        流程结果，含每步结论与整轮记录。
    """
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
