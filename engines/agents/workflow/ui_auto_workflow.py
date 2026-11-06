"""
文件名: ➡️ ui_auto_workflow.py 🏁
路径: ➡️ engines/agents/workflow/ui_auto_workflow.py 🏁
模块功能：➡️ AgentSOPWorkflow 🏁
Python 调试：➡️ python -m engines.agents.workflow.ui_auto_workflow 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. AgentSOPWorkflow: 把一份 SOP 跑一次 UI 自动化, 事件与运行汇总都写入同一份事件日志
2. 每个步骤新建一对执行者与验收者实例，跨步不继承上下文；重试复用该步实例
3. 步骤提示由 step_brief 拼装：执行者拿动作与页面锚点，验收者拿结果与日志证据
🏁
关联模块：➡️
1. engines.agents.agent_builders: 导入 build_executor, build_verifier
2. engines.agents.config.log_keywords: 导入 load_log_keywords，按型号取关键词目录
3. engines.agents.event_log: 导入 write_line
4. engines.agents.event_sink: 导入 set_step_context
5. engines.agents.messaging.messages: 导入 AgentEventsShow
6. engines.agents.workflow.case_file: 导入 CaseStep，步骤的结构化输入
7. engines.agents.workflow.step_brief: 导入 executor_brief / verifier_brief
8. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/api/test_task_event_store.py: 任务事件落库：事件、缩略图、小时用量和任务费用
2. tests/engines/agents/test_agent_event_live.py: 真机跑一轮工作流，把模型事件写入 tests/reports/agent_events_live.csv
3. tests/engines/agents/test_agents_workflow.py: 调试代码，功能不完善 ~ 禁止修改此文件代码
🏁
"""

import asyncio

from collections.abc import Callable, Sequence
from datetime import datetime

import yaml

from agentscope.agent import Agent
from agentscope.message import TextBlock, UserMsg
from agentscope.sop import SOP, SOPEngine, SOPPhase, SOPStep

from engines.agents.agent_builders import build_executor, build_verifier
from engines.agents.config.log_keywords import load_log_keywords
from engines.agents.event_log import write_line
from engines.agents.event_sink import (
    bind_interrupts,
    current_interrupts,
    current_run,
    note_interrupt,
    reset_interrupts,
    set_step_context,
)
from engines.agents.messaging.messages import AgentEventsShow
from engines.agents.messaging.record import EventRecord
from engines.agents.workflow.case_file import CaseStep
from engines.agents.workflow.step_brief import executor_brief, verifier_brief, with_context
from utils.logs import agent_event_log


async def _emit_interrupt(
    reason: str,
    exc_type: str,
    *,
    kind: str = "exception",
    step_seq: int | None = None,
) -> None:
    """把「事件流被打断」写成一条事件，供任务详情与 BUG 台账识别。

    走 `show_event`（内部 `database_sync_to_async`），因此是在工作线程里写库：
    直接在事件循环里同步写库会被 Django 判为 SynchronousOnlyOperation 并整批丢事件。

    Args:
        reason: 打断原因的文本（设备日志为空 / 时间不满足 5 秒等）。
        exc_type: 异常类型名，便于排查。
        kind: 中断类别：`log` 证据不可用 / `exception` 执行层异常。
        step_seq: 被中断的步骤序号；None 表示取当前运行上下文里的步骤。
    """
    run = current_run()
    now = datetime.now()
    record = EventRecord(
        event_type="StepInterruptedEvent",
        phase="结束",
        block_type="interrupt",
        payload={
            "reason": reason,
            "exc_type": exc_type,
            "kind": kind,
            "step_seq": step_seq if step_seq is not None else run.step_seq,
            "attempt": run.attempt,
            "task_id": run.task_id,
        },
        started_at=now,
        ended_at=now,
        duration_ms=0,
    )
    try:
        await show_event(record, {}, {}, flush=True)
    except Exception as exc:  # noqa: BLE001 - 台账失败不影响任务终态
        agent_event_log.warning(f"记录中断事件失败：{exc}")


async def _emit_step_interrupt(interrupt) -> None:
    """把一步的中断写成事件：带上类别、原因与涉及的工具。

    Args:
        interrupt: `StepInterrupt` 记录（序号、标题、类别、原因、工具）。
    """
    set_step_context(interrupt.step_seq or None, 1)
    await _emit_interrupt(
        interrupt.reason,
        interrupt.kind,
        kind=interrupt.kind,
        step_seq=interrupt.step_seq,
    )
    if interrupt.tool:
        agent_event_log.warning(
            f"步骤中断：第 {interrupt.step_seq} 步 {interrupt.title}｜{interrupt.kind}｜"
            f"工具 {interrupt.tool}｜{interrupt.reason}"
        )


class _ResilientSOPStep(SOPStep):
    """单步中断只影响这一步：异常收敛到本步并把该步收口，引擎继续推进。

    收集器里的中断记录由 `run_workflow` 统一转成事件，本类只负责把步骤状态
    从「还在跑」改成「已收口」，避免引擎把异常当成整轮失败。
    """

    def __init__(self, *args, step_seq: int = 0, **kwargs) -> None:
        """
        Args:
            *args: 透传给 SOPStep 的位置参数（subject / description / executor / verifier）。
            step_seq: 步骤序号，从 1 起；写入中断记录用。
            **kwargs: 透传给 SOPStep 的关键字参数。
        """
        super().__init__(*args, **kwargs)
        self.step_seq = step_seq

    def _close_interrupted(
        self, state, kind: str, reason: str, tool: str = "", *, noted: bool = False
    ) -> None:
        """记一条中断并把该步标记为已收口，让引擎继续下一步。

        Args:
            state: 本步的运行记录。
            kind: 中断类别。
            reason: 原因原文。
            tool: 涉及的工具名。
            noted: True 表示原因已由工具记进收集器，这里不再重复记。
        """
        if not noted:
            note_interrupt(kind, reason, title=self.subject, tool=tool, step_seq=self.step_seq)
        self.record(state, False, reason, "workflow")
        state.submission = [TextBlock(text=f"（本步中断：{reason}）")]
        state.phase = SOPPhase.COMPLETED

    async def reply_stream(self, inputs, state):
        """跑一次尝试；异常或证据不可用时只中断本步。

        Args:
            inputs: 引擎交给这次尝试的输入。
            state: 本步的运行记录。

        Yields:
            本步产生的事件；中断后立即结束，不再继续本步。
        """
        seen = len(current_interrupts())
        try:
            async for event in super().reply_stream(inputs, state):
                yield event
                latest = current_interrupts()
                if len(latest) > seen:
                    seen = len(latest)
                    self._close_interrupted(
                        state, latest[-1].kind, latest[-1].reason, latest[-1].tool, noted=True
                    )
                    return
            # 流正常结束也要看一次：证据不可用可能发生在最后一个事件之后
            latest = current_interrupts()
            if len(latest) > seen:
                self._close_interrupted(
                    state, latest[-1].kind, latest[-1].reason, latest[-1].tool, noted=True
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - 单步异常不许打死整条用例
            self._close_interrupted(state, "exception", f"{type(exc).__name__}: {exc}")
            return


def _step_keywords(step: CaseStep, default_sku: str) -> str:
    """取这一步的关键词表：优先用步上的 log.sku，其次用例级型号。

    Args:
        step: 一步的结构化输入。
        default_sku: 用例级型号；步上没有 log 时用它。

    Returns:
        该型号的关键词目录正文；两者都没有或目录缺失时为空串。
    """
    sku = step.log.sku if step.log is not None else default_sku
    return load_log_keywords(sku)


class AgentSOPWorkflow:
    """UI 自动 SOP 工作流：执行角色操作设备，验收角色判定步骤。"""

    INTERRUPTED_PHASE = "interrupted"
    """本次运行里有步骤被中断时的收口阶段，调用方据此把用例记为失败。"""

    def __init__(
        self,
        executor_factory: Callable[[], Agent],
        verifier_factory: Callable[[], Agent],
    ):
        """
        Args:
            executor_factory: 每个步骤调用一次，返回新的执行者（看页面、点设备）。
            verifier_factory: 每个步骤调用一次，返回新的验收者（截图、查日志、判这一步）。
        """
        self.log = agent_event_log
        self._executor_factory = executor_factory
        self._verifier_factory = verifier_factory
        # 运行汇总用第一个执行者的模型名，取不到时用占位符；编号在 run_workflow 里刷新
        self.model_name = "-"
        # 本次运行里被中断的步骤（StepInterrupt 列表），调用方据此写失败原因
        self.interrupts: list = []

        # 每一步被驳回几次后判失败, 由引擎执行, 不是步骤自己管
        self.MAX_ATTEMPTS = 2

    def _build_agents(self) -> tuple[Agent, Agent]:
        """为一步新建一对执行者与验收者。

        Returns:
            (执行者, 验收者)，两者都是全新实例，不带任何历史上下文。
        """
        return self._executor_factory(), self._verifier_factory()

    def dump(self, engine, sop) -> None:
        """流结束后回读运行状态：判决与交付都不在事件流里, 只能从这里看。

        Args:
            engine: 跑完的 SOPEngine, 状态在 engine.state。
            sop: 同一份 SOP, 用来取每步的步骤短名。

        Returns:
            None。
        """
        for index, record in enumerate(engine.state.steps, start=1):
            # record.submission: 这一步交付的内容块列表, 同时也是下一步的输入
            # 标准 SOPStep 交付的是一条 TextBlock; 被驳回时这里会被清回 None
            delivery = record.submission[0].text if record.submission else "-"
            self._log(f"第 {index} 步：{sop.steps[index - 1].subject}")
            # record.phase: 这一步的阶段, pending / running / awaiting / completed / failed
            # len(record.verifications): 已记几条判决 = 已尝试几次
            # record.given: 引擎交给这一步的输入, 第一步是开场输入, 之后是上一步的交付
            self._log(
                f"阶段 {record.phase.value}｜尝试 {len(record.verifications)} 次"
                f"｜引擎给了 {len(record.given)} 条输入"
            )
            self._log(f"交付：{delivery[:120]}")
            for order, verdict in enumerate(record.verifications, start=1):
                # verdict.passed: 这一次尝试过没过
                # verdict.message: 驳回说明, 不通过时会原样回灌给执行者, 所以要看清它
                # verdict.verifier: 谁判的, 模型名 / sop 兜底 / 人工
                self._log(
                    f"第 {order} 次判决 passed={verdict.passed}"
                    f" by={verdict.verifier}｜{verdict.message}"
                )

    async def run_workflow(
        self,
        name: str,
        steps: Sequence[CaseStep],
        run_input: str,
        *,
        default_sku: str = "",
        should_stop: Callable[[], bool] | None = None,
    ) -> str:
        """装配一份 SOP 并跑完一次：事件实时打屏, 结束后回读状态。

        Args:
            name: 流程名, 只用于日志与汇总, 模型看不到。
            steps: 一步一条的结构化输入；每个步骤单独新建一对角色实例。
            run_input: 开场输入（含设备 serial 等）；每步都会重放到提示里，因为每步都是新实例。
            default_sku: 用例级型号；某步没写 `log.sku` 时用它取关键词表，旧用例因此不必盲试。
            should_stop: 停止信号探测函数；返回 True 时在当前事件边界结束本次运行。
                None 表示不监听，行为与不传时一致。

        Returns:
            运行阶段字符串。完成时为 completed。

        Raises:
            ValueError: 步骤列表为空，无法装配流程。
            asyncio.CancelledError: 停止信号置位时抛出，供调用方按取消收口。
        """
        if not steps:
            raise ValueError("步骤列表为空，无法装配 SOP")

        # 每个步骤各建一对角色: 跨步不继承上下文; 同一步的重试仍复用该步的实例
        pairs = [self._build_agents() for _ in steps]
        first_executor, first_verifier = pairs[0]
        self.model_name = str(getattr(getattr(first_executor, "model", None), "model", "") or "-")
        # 开场上下文（设备 serial 等）每步重放：新实例的历史里没有它，不给就只能靠猜
        context = str(run_input or "").strip()
        sku_fallback = str(default_sku or "").strip()

        # 一份 SOP = 一串 SOPStep; SOP 本身不含运行状态, 可以反复跑
        # 用 _ResilientSOPStep：单步异常只中断这一步，引擎继续推进后续步骤
        sop = SOP(
            name=name,
            steps=[
                _ResilientSOPStep(
                    subject=with_context(executor_brief(step), context),  # 执行者: 动作 + 页面锚点
                    description=with_context(  # 验收者: 结果 + 日志证据 + 关键词表
                        verifier_brief(step, _step_keywords(step, sku_fallback)),
                        context,
                    ),
                    executor=executor,  # 执行者: 本步新建
                    verifier=verifier,  # 验收者: 本步新建
                    max_attempts=self.MAX_ATTEMPTS,  # 最大重试次数: 驳回几次后整轮失败
                    step_seq=index,
                )
                for index, (step, (executor, verifier)) in enumerate(
                    zip(steps, pairs, strict=True), start=1
                )
            ],
        )

        engine = SOPEngine(sop)  # 引擎持有本次运行的状态, 即 engine.state
        interrupt_token = bind_interrupts()

        try:
            buf: dict = {}  # 增量累积器: 块碎片、工具入参、工具返回都攒在这里
            # 发言开始早于模型调用, 「开始」行用角色上的模型名
            models = {
                first_executor.name: first_executor.model.model,
                first_verifier.name: first_verifier.model.model,
            }
            # 开场输入交给第一步供引擎推进；上下文已在每步的步骤提示里重放
            async for event in engine.reply_stream(UserMsg(name="user", content=run_input)):
                # 停止信号每个事件边界检查一次：库默认吞掉取消，只靠 task.cancel()
                # 会把「关闭」误当成一次失败尝试并触发重试，所以这里主动中断
                if should_stop is not None and should_stop():
                    raise asyncio.CancelledError()
                _stamp_step(engine)
                await show_event(event, buf, models)

        except Exception as exc:
            # 兜底：步骤级已接住工具异常，走到这里说明事件流本身坏了
            # 注意 Exception 接不住 BaseExceptionGroup（带取消时 asyncio 抛的是它）
            self._log(f"事件流被异常打断：{type(exc).__name__}: {exc}")
            await _emit_interrupt(f"{type(exc).__name__}: {exc}", type(exc).__name__)

        try:
            # 一步中断只收口这一步：把收集到中断写成事件，用例结论由调用方按 FAIL 收
            self.interrupts = current_interrupts()
            for interrupt in self.interrupts:
                await _emit_step_interrupt(interrupt)
            # 结论不在事件流里: 跑完必须回 engine.state 读
            # 中断过就按 interrupted 收口，其余情况用引擎给的阶段
            self._log(f"运行阶段：{engine.phase}")
            self.dump(engine, sop)
            if self.interrupts:
                return self.INTERRUPTED_PHASE
            phase = getattr(engine.phase, "value", engine.phase)
            return str(phase or "")
        finally:
            reset_interrupts(interrupt_token)

    def _log(self, action: str) -> None:
        """运行汇总写入与事件时间线同一份日志。模型名用执行者的模型。"""
        write_line(self.model_name, action)


async def show_event(event, buf: dict, models: dict | None, *, flush: bool = False) -> None:
    """在工作线程里折叠并交给接收方。事件循环里不查库。

    Django 未启动时仍在当前线程调用，供引擎本地调试使用。

    Args:
        event: 事件流里的一条事件。
        buf: 增量累积器。
        models: 角色名到模型名。
        flush: 交完这条后让接收方立即落库；实时过程需要。
    """
    if _django_ready():
        from channels.db import database_sync_to_async

        await database_sync_to_async(AgentEventsShow.show, thread_sensitive=False)(
            event, buf, models, flush=flush
        )
        return
    AgentEventsShow.show(event, buf, models, flush=flush)


def _django_ready() -> bool:
    """当前进程是否已完成 Django 启动。"""
    try:
        from django.apps import apps
    except ImportError:
        return False
    return bool(apps.ready)


def _stamp_step(engine) -> None:
    """把当前正在跑的步骤序号和尝试次数交给事件接收方。

    匹配集合含 pending：SOP 的步骤起点事件在这一步还是 pending 时到达，
    只有把它也算进来，步骤起点行才挂得到正确的步骤上。
    """
    steps = list(getattr(getattr(engine, "state", None), "steps", []) or [])
    for index, record in enumerate(steps, start=1):
        phase = getattr(getattr(record, "phase", None), "value", "")
        if str(phase) in {"running", "awaiting", "pending"}:
            attempt = len(getattr(record, "verifications", []) or []) + 1
            set_step_context(index, attempt)
            return
    set_step_context(None, None)


def _case_sections(data) -> list[list]:
    """取出文件里所有「用例列表」。

    用例 YAML 有两种根节点写法，都要认：

    1. 列表：整个文件就是用例列表（旧写法）；
    2. 映射：按测试模块分节，节值是用例列表（如 `TestAgentsWorkflow`），
       其它节放的是参数而不是用例（如 `TestToolDevice: {serial: ...}`），跳过。

    Args:
        data: `yaml.safe_load` 的结果。

    Returns:
        用例列表的列表；认不出时返回空列表。
    """
    if isinstance(data, list):
        return [data]
    if isinstance(data, dict):
        return [value for value in data.values() if isinstance(value, list)]
    return []


def load_test_cases(yaml_path: str) -> dict[str, list[tuple[str, str]]]:
    """读用例 YAML, 返回 {用例名: [(步骤描述, 需要达成的结果), ...]}。"""
    # 显式 encoding="utf-8": Windows 默认编码是 GBK, 而用例 YAML 是 UTF-8
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        str(case.get("title") or "").strip(): [  # title: 用例名
            (
                str(step.get("action") or "").strip(),  # action: 步骤描述, 给执行者
                str(step.get("assert") or "").strip(),  # assert: 需要达成的结果, 给验收者
            )
            for step in case.get("steps") or []
        ]
        for section in _case_sections(data)
        for case in section
        if isinstance(case, dict)
    }


def run_workflow(yml_path: str, run_input: str, case_title: str | None = None) -> None:
    """装配一份 SOP 并跑完一次：事件实时打屏, 结束后回读状态。

    Args:
        yml_path: 用例 YAML 路径。
        run_input: 开场输入, 只交给第一步。参数内容例如：本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。
        case_title: 用例名称，指定执行某条用例；如果为空，则执行所有用例。
    """
    cases = load_test_cases(yml_path)
    for title, steps in cases.items():
        if case_title and title != case_title:
            continue

        workflow = AgentSOPWorkflow(build_executor, build_verifier)
        case_steps = [CaseStep(action=action, expected=expected) for action, expected in steps]
        asyncio.run(workflow.run_workflow(title, case_steps, run_input))
