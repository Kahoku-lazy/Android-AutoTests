"""SOP 角色归属与尝试序号契约（ae-harness-event-full-record 新增需求）。

用替身事件驱动记录器：有名字映射按 agent 名归属（不依赖回复顺序），
无映射沿用奇偶推断；尝试序号取自官方 SOP_STEP_STARTED 事件。
零 I/O：只写临时目录，不连模型、不联网。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from engines.ae_harness.event.record import AgentEventRecorder

pytestmark = [pytest.mark.unit]


@dataclass
class ReplyStartEvent:
    """替身：一条回复开始，带 reply_id 与 agent 名。"""

    reply_id: str
    name: str


@dataclass
class CustomEvent:
    """替身：SOP 步骤起点事件。"""

    name: str
    value: dict


@dataclass
class ToolCallStartEvent:
    """替身：工具调用开始。"""

    tool_call_id: str
    tool_call_name: str = "adb_tap"


@dataclass
class ToolCallEndEvent:
    """替身：工具调用入参确定。"""

    tool_call_id: str


@dataclass
class ToolResultEndEvent:
    """替身：工具结果返回，带发起回复的 reply_id。"""

    tool_call_id: str
    state: str = "success"
    reply_id: str = "r1"


def _feed_tool(recorder: AgentEventRecorder, call_id: str, reply_id: str) -> None:
    """喂一次完整工具调用，产出一条 StepRecord。"""
    recorder.on_event(ToolCallStartEvent(call_id))
    recorder.on_event(ToolCallEndEvent(call_id))
    recorder.on_event(ToolResultEndEvent(call_id, reply_id=reply_id))


def test_mapping_wins_over_reply_order(tmp_path: Path):
    """有映射时验收者先回复也归属正确，不按奇偶错配。"""
    recorder = AgentEventRecorder(
        tmp_path,
        "probe",
        sop_roles={"exec_agent": "executor", "verify_agent": "verifier"},
    )
    recorder.begin("sop")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "打开设置", "attempt": 1}))
    # 故意乱序：验收者的回复先到
    recorder.on_event(ReplyStartEvent("r1", "verify_agent"))
    _feed_tool(recorder, "c1", "r1")
    recorder.on_event(ReplyStartEvent("r2", "exec_agent"))
    _feed_tool(recorder, "c2", "r2")
    record = recorder.finish(1.0)

    assert [step.agent_role for step in record.steps] == ["verifier", "executor"]


def test_no_mapping_keeps_odd_even_fallback(tmp_path: Path):
    """无映射时沿用既有奇偶推断：每步第一次回复为执行者，第二次为验收者。"""
    recorder = AgentEventRecorder(tmp_path, "probe")
    recorder.begin("sop")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "打开设置", "attempt": 1}))
    recorder.on_event(ReplyStartEvent("r1", "exec_agent"))
    _feed_tool(recorder, "c1", "r1")
    recorder.on_event(ReplyStartEvent("r2", "verify_agent"))
    _feed_tool(recorder, "c2", "r2")
    record = recorder.finish(1.0)

    assert [step.agent_role for step in record.steps] == ["executor", "verifier"]


def test_attempt_lands_on_step_records(tmp_path: Path):
    """第 2 次尝试内的工具记录带步骤名与尝试序号 2。"""
    recorder = AgentEventRecorder(tmp_path, "probe", sop_roles={"exec_agent": "executor"})
    recorder.begin("sop")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "打开设置", "attempt": 2}))
    recorder.on_event(ReplyStartEvent("r1", "exec_agent"))
    _feed_tool(recorder, "c1", "r1")
    record = recorder.finish(1.0)

    assert record.steps[0].sop_step == "打开设置"
    assert record.steps[0].sop_attempt == 2


def test_attempt_defaults_to_zero_without_field(tmp_path: Path):
    """步骤起点事件没带 attempt 时尝试序号为 0，不伪造。"""
    recorder = AgentEventRecorder(tmp_path, "probe")
    recorder.begin("sop")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "回到桌面"}))
    recorder.on_event(ReplyStartEvent("r1", "exec_agent"))
    _feed_tool(recorder, "c1", "r1")
    record = recorder.finish(1.0)

    assert record.steps[0].sop_attempt == 0
