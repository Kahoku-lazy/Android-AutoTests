"""SOP 事件流的完整性：用例名刷新、步骤起点、超轮次提醒、运行预算。

守的是四件事：
1. 一个任务跑多条用例时，事件行能分清用例（`set_case_title`）；
2. SOP 步骤起点落库，步骤边界不再靠 `step_seq` 推断；
3. `ExceedMaxItersEvent` / `HintBlockEvent` 落库，「为什么突然收尾」可解释；
4. 模型调用次数超预算时整轮停下，而不是无限叠加。
"""

from __future__ import annotations

import pytest

from backend.apps.task_list.task_reports import _EVENT_LABEL, _detail, _EventRow
from engines.agents import event_sink
from engines.agents.event_sink import (
    bind_run_context,
    bind_sink,
    budget_exceeded,
    count_model_call,
    current_run,
    flush_sink,
    reset_run_context,
    reset_sink,
    set_case_title,
)
from engines.agents.messaging import messages
from engines.agents.messaging.fold import step

_IDLE = "2026-10-18T10:00:00+08:00"


class CustomEvent:
    """SOP 引擎的步骤边界事件。"""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class HintBlockEvent:
    """运行时注入提醒。"""

    def __init__(self, hint, source='{"label": "System"}'):
        self.hint = hint
        self.source = source


class ExceedMaxItersEvent:
    """推理轮次用尽。"""


class ModelCallEndEvent:
    """一次模型调用结束，带用量三元组。"""

    def __init__(self, incoming=10, outgoing=20, hit=5):
        self.input_tokens = incoming
        self.output_tokens = outgoing
        self.cache_input_tokens = hit
        self.created_at = _IDLE
        self.finished_reason = "completed"


def _event_types(result) -> list[str]:
    return [record.event_type for record in result.records]


# ── S1：用例名按用例刷新 ────────────────────────────────


@pytest.mark.unit
def test_set_case_title_refreshes_bound_context():
    """绑定运行上下文后，用例名可随每条用例刷新。"""
    token = bind_run_context(7, 3, "任务级标题")
    try:
        assert current_run().case_title == "任务级标题"
        set_case_title("用例 A")
        assert current_run().case_title == "用例 A"
        set_case_title("用例 B")
        assert current_run().case_title == "用例 B"
    finally:
        reset_run_context(token)


@pytest.mark.unit
def test_set_case_title_is_noop_without_run_context():
    """未绑定运行上下文时刷新用例名不抛异常。"""
    set_case_title("用例 A")
    assert current_run().case_title == ""


@pytest.mark.unit
def test_set_case_title_truncates_to_column_width():
    """用例名按列宽 255 截断，避免写库时被数据库拒掉。"""
    token = bind_run_context(7, 3, "")
    try:
        set_case_title("x" * 400)
        assert len(current_run().case_title) == 255
    finally:
        reset_run_context(token)


class _FlushSink:
    """记录 emit 与 flush 次数的假接收方。"""

    def __init__(self):
        self.emitted = []
        self.flushed = 0

    def emit(self, record, image_b64=""):
        self.emitted.append(record)

    def flush(self):
        self.flushed += 1


@pytest.mark.unit
def test_flush_sink_calls_receiver_flush():
    """flush_sink 只调用接收方的 flush，不关心它怎么落库。"""
    sink = _FlushSink()
    token = bind_sink(sink)
    try:
        flush_sink()
        assert sink.flushed == 1
    finally:
        reset_sink(token)


@pytest.mark.unit
def test_agent_events_show_flushes_when_requested():
    """用例编写流程逐条落库：show(flush=True) 交完就 flush。"""
    sink = _FlushSink()
    token = bind_sink(sink)
    try:
        messages.AgentEventsShow.show(
            CustomEvent("SOP_STEP_STARTED", {"step": "家电测试用例设计与自检", "attempt": 1}),
            {},
            None,
            flush=True,
        )
        assert len(sink.emitted) == 1
        assert sink.flushed == 1
    finally:
        reset_sink(token)


# ── S2：SOP 步骤起点落库 ────────────────────────────────


@pytest.mark.unit
def test_sop_step_started_becomes_record():
    """步骤起点交出记录，角色与模型留空（它不属于任何一轮发言）。"""
    result = step(
        CustomEvent("SOP_STEP_STARTED", {"step": "打开设置", "attempt": 2}),
        {},
        None,
    )
    assert _event_types(result) == ["SOP_STEP_STARTED"]
    record = result.records[0]
    assert record.phase == "开始"
    assert record.block_type == "sop_step"
    assert record.payload == {"step": "打开设置", "attempt": 2}
    assert (record.role_name, record.role_kind, record.model) == ("", "", "")


@pytest.mark.unit
def test_sop_step_ended_is_dropped():
    """步骤终点不落行：终点等于下一个起点或任务结束。"""
    result = step(
        CustomEvent("SOP_STEP_ENDED", {"step": "打开设置", "phase": "completed"}),
        {},
        None,
    )
    assert result.records == []


# ── S3：超轮次与运行时提醒落库 ──────────────────────────


@pytest.mark.unit
def test_exceed_max_iters_becomes_record():
    """推理轮次用尽要留下一条记录，才能解释「为什么突然收尾」。"""
    result = step(ExceedMaxItersEvent(), {"_model": "deepseek-flash"}, None)
    assert _event_types(result) == ["ExceedMaxItersEvent"]
    assert result.records[0].phase == "结束"
    assert result.records[0].payload == {}


@pytest.mark.unit
def test_hint_block_keeps_full_text():
    """运行时提醒落库时保留注入全文，不截断。"""
    hint = "你已连续 3 次调用同一个失败工具，请换一种做法。" + "补充" * 200
    result = step(HintBlockEvent(hint), {"_model": "deepseek-flash"}, None)
    assert _event_types(result) == ["HintBlockEvent"]
    assert result.records[0].payload["hint"] == hint
    assert result.records[0].block_type == "hint"


# ── S6：运行预算兜底 ───────────────────────────────────


@pytest.mark.unit
def test_model_call_budget_flips_flag(monkeypatch):
    """模型调用次数超过上限后置位预算标志。"""
    monkeypatch.setattr(event_sink, "MAX_MODEL_CALLS", 2)
    token = bind_run_context(7, 3, "")
    try:
        count_model_call()
        count_model_call()
        assert budget_exceeded() is False
        count_model_call()
        assert budget_exceeded() is True
        assert current_run().model_calls == 3
    finally:
        reset_run_context(token)


@pytest.mark.unit
def test_budget_is_off_without_run_context():
    """未绑定运行上下文时不参与预算判定（本地调试路径）。"""
    count_model_call()
    assert budget_exceeded() is False


@pytest.mark.unit
def test_show_raises_when_budget_exceeded(monkeypatch):
    """超预算时事件上屏抛 RuntimeError，由工作流收束整轮。"""
    monkeypatch.setattr(event_sink, "MAX_MODEL_CALLS", 1)
    monkeypatch.setattr(messages, "write_line", lambda *args, **kwargs: None)
    token = bind_run_context(7, 3, "")
    try:
        messages.AgentEventsShow.show(ModelCallEndEvent(), {})
        with pytest.raises(RuntimeError):
            messages.AgentEventsShow.show(ModelCallEndEvent(), {})
    finally:
        reset_run_context(token)


# ── S4：报告侧展示 ─────────────────────────────────────


@pytest.mark.unit
def test_report_detail_covers_new_event_types():
    """新事件行在报告里必须有非空 detail，否则等于白落。"""
    started = _EventRow(
        seq=1,
        event_type="SOP_STEP_STARTED",
        is_delta=False,
        step_seq=1,
        attempt=2,
        payload={"step": "打开设置", "attempt": 2},
    )
    assert _detail(started, started.payload) == "打开设置 · 第 2 次尝试"

    hint = _EventRow(
        seq=2,
        event_type="HintBlockEvent",
        is_delta=False,
        step_seq=1,
        attempt=1,
        payload={"hint": "换一种做法"},
    )
    assert _detail(hint, hint.payload) == "换一种做法"

    exceed = _EventRow(
        seq=3,
        event_type="ExceedMaxItersEvent",
        is_delta=False,
        step_seq=1,
        attempt=1,
        payload={},
    )
    assert _detail(exceed, exceed.payload) == "推理轮次用尽，模型被强制收尾"


@pytest.mark.unit
def test_report_detail_covers_model_retry_and_fallback():
    """重试与回退事件要有可读明细和中文标签，否则详情页等于白多一行。"""
    retry = _EventRow(
        seq=4,
        event_type="ModelRetryEvent",
        is_delta=False,
        step_seq=1,
        attempt=1,
        model="deepseek-flash",
        phase="推理",
        payload={
            "attempt": 1,
            "attempts": 2,
            "delay_ms": 800,
            "reason": "APIStatusError: 503",
        },
    )
    assert _detail(retry, retry.payload) == (
        "deepseek-flash · 第 1/2 次 · 800 ms 后重试 · APIStatusError: 503"
    )

    fallback = _EventRow(
        seq=5,
        event_type="ModelFallbackEvent",
        is_delta=False,
        step_seq=1,
        attempt=1,
        model="deepseek-flash",
        phase="推理",
        payload={"from_model": "deepseek-flash", "to_model": "deepseek-pro", "attempts": 2},
    )
    assert _detail(fallback, fallback.payload) == ("deepseek-flash → deepseek-pro · 主模型重试用尽")

    assert _EVENT_LABEL["ModelRetryEvent"] == "模型调用重试"
    assert _EVENT_LABEL["ModelFallbackEvent"] == "模型回退到备用模型"
