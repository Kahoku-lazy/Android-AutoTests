"""取消即断流：工作流在每个事件边界检查停止信号，命中即结束当前步骤。"""

from __future__ import annotations

import asyncio
import threading

from types import SimpleNamespace

import pytest

from engines.agents.agent_builders import _as_react_config
from engines.agents.config.role_types import ReActConfig
from engines.agents.workflow import platform_run as platform_run_module
from engines.agents.workflow import ui_auto_workflow
from engines.agents.workflow.case_file import CaseStep
from engines.agents.workflow.ui_auto_workflow import AgentSOPWorkflow

pytestmark = [pytest.mark.unit]


class _FakeModel:
    """替身模型：工作流只读它的 model 名。"""

    model = "fake-model"


class _Stopper:
    """停止信号开关：由替身执行者在产出第 N 条事件时置位。"""

    def __init__(self, after: int) -> None:
        self.after = after
        self.produced = 0
        self.stop = False

    def on_event(self) -> None:
        self.produced += 1
        if self.after and self.produced >= self.after:
            self.stop = True


class _FakeAgent:
    """替身角色：按预设事件列表流式产出，不做任何 I/O。

    Attributes:
        name: 角色名，工作流用它做事件归类。
        model: 模型替身，工作流只读 `.model`。
        calls: 被调用了几次，用来断言「没有触发重试」。
    """

    def __init__(self, name: str, events: list, stopper: _Stopper | None = None) -> None:
        self.name = name
        self.model = _FakeModel()
        self.events = list(events)
        self.stopper = stopper
        self.calls = 0

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        """按顺序产出事件；给了 stopper 时在每条事件后推进停止计数。"""
        self.calls += 1
        for event in self.events:
            if self.stopper is not None:
                self.stopper.on_event()
            yield event


async def _noop_show_event(event, buf, models, *, flush=False) -> None:
    """替身上屏：单测不写库、不打屏。"""
    return None


@pytest.fixture(autouse=True)
def _silence_show_event(monkeypatch):
    """把事件上屏替换成空实现，保持单测零 I/O。"""
    monkeypatch.setattr(ui_auto_workflow, "show_event", _noop_show_event)


def _workflow(executor: _FakeAgent, verifier: _FakeAgent) -> AgentSOPWorkflow:
    """装一个只有一对替身角色的工作流。"""
    return AgentSOPWorkflow(lambda: executor, lambda: verifier)


async def test_stop_signal_interrupts_before_retry():
    """停止信号在一个事件边界置位后立即结束，且不进入第二次尝试。"""
    stopper = _Stopper(after=3)
    executor = _FakeAgent("executor", ["e1", "e2", "e3", "e4", "e5"], stopper)
    verifier = _FakeAgent("verifier", [])
    steps = [CaseStep(action="点一下", expected="页面已打开")]

    with pytest.raises(asyncio.CancelledError):
        await _workflow(executor, verifier).run_workflow(
            "case",
            steps,
            "开场",
            should_stop=lambda: stopper.stop,
        )

    assert executor.calls == 1
    assert verifier.calls == 0


async def test_without_stop_signal_runs_to_budget_end():
    """不传停止信号时行为不变：照常跑满两次尝试并落到 failed。"""
    executor = _FakeAgent("executor", ["e1", "e2"])
    verifier = _FakeAgent("verifier", [])
    steps = [CaseStep(action="点一下", expected="页面已打开")]

    phase = await _workflow(executor, verifier).run_workflow("case", steps, "开场")

    assert phase == "failed"
    assert executor.calls == 2


async def test_stop_signal_never_set_runs_to_budget_end():
    """传入恒为 False 的探测函数时，行为与不传一致。"""
    executor = _FakeAgent("executor", ["e1"])
    verifier = _FakeAgent("verifier", [])
    steps = [CaseStep(action="点一下", expected="页面已打开")]

    phase = await _workflow(executor, verifier).run_workflow(
        "case",
        steps,
        "开场",
        should_stop=lambda: False,
    )

    assert phase == "failed"
    assert executor.calls == 2


async def test_drive_real_returns_cancelled_for_single_case(monkeypatch):
    """单用例任务取消后返回 cancelled，且不追加失败条目。"""
    seen: dict = {}

    class _CancellableWorkflow:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def run_workflow(self, name, steps, run_input, *, default_sku="", should_stop=None):
            seen["should_stop"] = should_stop
            seen["steps"] = steps
            while True:
                if should_stop is not None and should_stop():
                    raise asyncio.CancelledError()
                await asyncio.sleep(0.01)

    monkeypatch.setattr(platform_run_module, "AgentSOPWorkflow", _CancellableWorkflow)
    cancel_event = threading.Event()
    case = SimpleNamespace(title="H9999 单用例", steps=[])

    async def _scenario() -> dict:
        task = asyncio.create_task(
            platform_run_module._drive_real([case], "开场", 7, cancel_event, "", None)
        )
        await asyncio.sleep(0.05)
        cancel_event.set()
        return await asyncio.wait_for(task, timeout=5)

    result = await _scenario()

    assert result["status"] == "cancelled"
    assert result["completed"] == []
    assert result["failed"] == []
    assert callable(seen["should_stop"])


def test_react_config_keeps_cancelled_error():
    """角色侧 ReAct 配置默认继续抛出取消，并原样映射到 agentscope。"""
    assert ReActConfig().interruption_raise_cancelled_error is True
    assert _as_react_config(ReActConfig()).interruption_raise_cancelled_error is True
    assert (
        _as_react_config(ReActConfig(interruption_raise_cancelled_error=False))
        .interruption_raise_cancelled_error
        is False
    )
