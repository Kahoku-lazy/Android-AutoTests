"""单步中断：异常或证据不可用只让这一步失败，后续步骤照跑，原因带得回去。"""

from __future__ import annotations

import asyncio

from types import SimpleNamespace

import pytest

from agentscope.message import Msg, TextBlock
from agentscope.types import ReplyFinishedReason

from engines.agents.event_sink import bind_sink, note_interrupt, reset_sink
from engines.agents.tools.tool_serial import LOG_EMPTY
from engines.agents.workflow import ui_auto_workflow
from engines.agents.workflow.case_file import CaseStep
from engines.agents.workflow.ui_auto_workflow import AgentSOPWorkflow

pytestmark = [pytest.mark.unit]


def _reply(name: str, text: str, structured: dict) -> Msg:
    """造一条带结构化输出的终回复：SOPStep 只认这种结束方式。"""
    return Msg(
        name=name,
        role="assistant",
        content=[TextBlock(text=text)],
        finished_reason=ReplyFinishedReason.COMPLETED,
        structured_output=structured,
    )


class _FakeModel:
    """替身模型：工作流只读它的 model 名。"""

    model = "fake-model"


class _FakeExecutor:
    """替身执行者：按 behavior 产出交付、抛异常，或正常交卷。"""

    def __init__(self, name: str, behavior: str) -> None:
        self.name = name
        self.model = _FakeModel()
        self.behavior = behavior
        self.calls = 0

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        """产出事件；behavior=raise 时在产出后抛异常。"""
        self.calls += 1
        yield "thinking"
        if self.behavior == "raise":
            raise RuntimeError("tool exploded")
        if self.behavior == "pass":
            yield _reply(self.name, "交付", {"handover": "这一步做完了"})


class _FakeVerifier:
    """替身验收者：pass 给通过，reject 一律驳回，evidence 先记一条证据不可用。"""

    def __init__(self, name: str, behavior: str) -> None:
        self.name = name
        self.model = _FakeModel()
        self.behavior = behavior
        self.calls = 0

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        """产出事件；evidence 时先记证据不可用再产出，模拟 check_device_log 的返回。"""
        self.calls += 1
        if self.behavior == "evidence":
            note_interrupt("log", LOG_EMPTY, tool="check_device_log")
            yield "tool-result"
            return
        yield "looked at screenshot"
        if self.behavior == "reject":
            yield _reply(self.name, "驳回", {"passed": False, "message": "页面还停在上一页"})
            return
        if self.behavior == "pass":
            yield _reply(self.name, "判决", {"passed": True, "message": ""})


class _FakeSink:
    """替身接收方：只记录收到的结构化事件。"""

    def __init__(self) -> None:
        self.records: list = []

    def emit(self, record, image_b64: str = "") -> None:
        """收下一条记录。"""
        del image_b64
        self.records.append(record)

    def flush(self) -> None:
        """落库替身：什么都不做。"""


@pytest.fixture(autouse=True)
def _silence_show_event(monkeypatch):
    """把事件上屏替换成记录器；单测不写文本日志，也不走接收方。"""
    events: list = []

    async def _record(event, buf, models, *, flush=False):
        events.append(event)

    monkeypatch.setattr(ui_auto_workflow, "show_event", _record)
    return events


def _workflow(behaviors: list[tuple[str, str]], seen: dict) -> AgentSOPWorkflow:
    """按每一步的 (执行者行为, 验收者行为) 造一对替身；工厂按调用序号返回。"""

    def _executor_factory():
        index = seen["executors"]
        seen["executors"] += 1
        return _FakeExecutor(f"executor-{index}", behaviors[index][0])

    def _verifier_factory():
        index = seen["verifiers"]
        seen["verifiers"] += 1
        return _FakeVerifier(f"verifier-{index}", behaviors[index][1])

    return AgentSOPWorkflow(_executor_factory, _verifier_factory)


def _steps(count: int) -> list[CaseStep]:
    return [CaseStep(action=f"动作 {i}", expected=f"结果 {i}") for i in range(1, count + 1)]


async def test_step_exception_does_not_stop_later_steps(_silence_show_event):
    """第 2 步抛异常：第 3、4 步照跑，运行阶段为 interrupted。"""
    seen = {"executors": 0, "verifiers": 0}
    workflow = _workflow([("pass", "pass"), ("raise", "pass"), ("pass", "pass"), ("pass", "pass")], seen)

    phase = await workflow.run_workflow("用例", _steps(4), "开场")

    assert phase == AgentSOPWorkflow.INTERRUPTED_PHASE
    assert seen["executors"] == 4
    assert seen["verifiers"] == 4
    assert len(workflow.interrupts) == 1
    interrupt = workflow.interrupts[0]
    assert interrupt.step_seq == 2
    assert interrupt.kind == "exception"
    assert "RuntimeError" in interrupt.reason and "tool exploded" in interrupt.reason


async def test_evidence_missing_interrupts_only_that_step(_silence_show_event):
    """日志证据不可用：该步按中断收口，不触发重试，后续步骤继续。"""
    seen = {"executors": 0, "verifiers": 0}
    workflow = _workflow([("pass", "pass"), ("pass", "evidence"), ("pass", "pass")], seen)

    phase = await workflow.run_workflow("用例", _steps(3), "开场")

    assert phase == AgentSOPWorkflow.INTERRUPTED_PHASE
    assert seen["executors"] == 3
    assert len(workflow.interrupts) == 1
    assert workflow.interrupts[0].kind == "log"
    assert workflow.interrupts[0].tool == "check_device_log"
    assert LOG_EMPTY in workflow.interrupts[0].reason


async def test_interrupt_event_reaches_sink(_silence_show_event):
    """中断要真正交给接收方（写进 task_events），不是只交给上屏函数。

    回归点：中断曾走 `show_event`，而折叠按 AgentScope 事件类型名分派，
    `EventRecord` 认不出会被静默丢成空结果——任务 201/204 因此一条中断事件都没有。
    """
    sink = _FakeSink()
    token = bind_sink(sink)
    try:
        seen = {"executors": 0, "verifiers": 0}
        workflow = _workflow([("pass", "pass"), ("raise", "pass"), ("pass", "pass")], seen)

        await workflow.run_workflow("用例", _steps(3), "开场")
    finally:
        reset_sink(token)

    records = [
        record for record in sink.records if getattr(record, "event_type", "") == "StepInterruptedEvent"
    ]
    assert len(records) == 1
    payload = records[0].payload
    assert payload["kind"] == "exception"
    assert payload["step_seq"] == 2
    assert "RuntimeError" in payload["reason"]


async def test_rejected_step_is_collected_as_failure(_silence_show_event):
    """验收驳回到上限的步骤要进 failed_steps，失败原因才点得到名。"""
    seen = {"executors": 0, "verifiers": 0}
    workflow = _workflow([("pass", "pass"), ("pass", "reject"), ("pass", "pass")], seen)

    await workflow.run_workflow("用例", _steps(3), "开场")

    assert [item.step_seq for item in workflow.failed_steps] == [2]
    assert workflow.failed_steps[0].attempts == 2
    assert "上一页" in workflow.failed_steps[0].reason
    assert workflow.failed_steps[0].title == "动作 2"


async def test_interrupted_step_is_not_reported_as_rejection(_silence_show_event):
    """被中断的步骤不要在 failed_steps 里再报一次。"""
    seen = {"executors": 0, "verifiers": 0}
    workflow = _workflow([("pass", "pass"), ("pass", "evidence")], seen)

    await workflow.run_workflow("用例", _steps(2), "开场")

    assert len(workflow.interrupts) == 1
    assert workflow.failed_steps == []


async def test_all_steps_pass_has_no_interrupt(_silence_show_event):
    """没有中断时行为不变：阶段仍是引擎给的 completed。"""
    seen = {"executors": 0, "verifiers": 0}
    workflow = _workflow([("pass", "pass"), ("pass", "pass")], seen)

    phase = await workflow.run_workflow("用例", _steps(2), "开场")

    assert phase == "completed"
    assert workflow.interrupts == []


def test_interrupt_reason_is_readable():
    """失败原因要写清第几步、哪一类中断与原文。"""
    from engines.agents.workflow.platform_run import _failure_detail

    detail = _failure_detail(
        [SimpleNamespace(step_seq=2, kind="log", reason=LOG_EMPTY, tool="check_device_log")]
    )

    assert "第 2 步" in detail
    assert "证据不可用" in detail
    assert "check_device_log" in detail
    assert LOG_EMPTY in detail
    assert _failure_detail([]) == ""


def test_failure_detail_covers_interrupt_and_rejection():
    """中断与验收驳回要同时出现在原因里（任务 204 只报了中断、漏了驳回）。"""
    from engines.agents.workflow.platform_run import _failure_detail
    from engines.agents.workflow.ui_auto_workflow import StepFailure

    detail = _failure_detail(
        [SimpleNamespace(step_seq=7, kind="log", reason=LOG_EMPTY, tool="check_device_log")],
        [StepFailure(step_seq=8, title="添加效果", attempts=2, reason="页面还停在上一页")],
    )

    assert "第 7 步" in detail and "证据不可用" in detail
    assert "第 8 步" in detail and "添加效果" in detail
    assert "验收驳回 2 次" in detail
    assert "页面还停在上一页" in detail


def test_failure_detail_counts_overflow():
    """超过三条要给出总数，避免原因看起来只有三处问题。"""
    from engines.agents.workflow.platform_run import _failure_detail

    interrupts = [
        SimpleNamespace(step_seq=index, kind="log", reason=LOG_EMPTY, tool="check_device_log")
        for index in range(1, 6)
    ]

    detail = _failure_detail(interrupts)

    assert "等 2 处未通过" in detail


def test_verifier_prompt_explains_evidence_missing():
    """验收提示词要讲清「证据不可用 ≠ 执行失败」，且不能写成未抓到关键字。"""
    from engines.agents.role_sys_prompts import UiControlPrompts

    text = UiControlPrompts.verifier()

    assert "evidence_missing" in text
    assert "证据不可用" in text
    assert "MUST NOT 写成设备或应用执行失败" in text


def test_asyncio_runner_available():
    """保证 asyncio 在测试文件里可用（避免未使用导入被误删）。"""
    assert asyncio.get_event_loop_policy() is not None
