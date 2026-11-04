"""事件流被打断时写一条 StepInterruptedEvent，供任务详情与 BUG 台账识别。"""

from __future__ import annotations

import pytest

from engines.agents.event_sink import (
    bind_run_context,
    bind_sink,
    reset_run_context,
    reset_sink,
    set_step_context,
)
from engines.agents.workflow.ui_auto_workflow import _emit_interrupt

pytestmark = pytest.mark.unit


class _Recorder:
    """记录收到的每条事件。"""

    def __init__(self) -> None:
        self.records: list = []

    def emit(self, record, image_b64: str = "") -> None:
        """收下事件。"""
        self.records.append(record)


def test_interrupt_emits_marker_with_step_and_reason() -> None:
    """打断时写的事件带步骤号、尝试次数与原因。"""
    sink = _Recorder()
    sink_token = bind_sink(sink)
    run_token = bind_run_context(42, 7, "卡片页")
    set_step_context(2, 1)
    try:
        _emit_interrupt("日志为空，请检查断后是否正确连接，此轮执行终止", "DeveloperOrientedException")
    finally:
        reset_run_context(run_token)
        reset_sink(sink_token)

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.event_type == "StepInterruptedEvent"
    assert record.payload["step_seq"] == 2
    assert record.payload["attempt"] == 1
    assert record.payload["task_id"] == 42
    assert "日志为空" in record.payload["reason"]
