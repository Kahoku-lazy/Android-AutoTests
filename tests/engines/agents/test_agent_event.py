"""把一轮折叠结果按表字段写入 CSV，再读回断言字段与类型。

CSV 在 tests/reports/agent_events.csv，模拟尚未落地的事件表读写。不连接数据库。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from engines.agents.event_sink import bind_sink, reset_sink
from engines.agents.messaging.messages import AgentEventsShow
from tests.engines.agents.event_csv import CsvEventStore, assert_event_row, load_event_csv

_ROOT = Path(__file__).resolve().parents[3]
_CSV_PATH = _ROOT / "tests" / "reports" / "agent_events.csv"
_IDLE = "2026-10-18T10:00:00+08:00"
_ZERO = Decimal("0.00000000")
_CACHE = Decimal("0.00002000")


class ReplyStartEvent:
    def __init__(self, name):
        self.name = name


class ReplyEndEvent:
    def __init__(self, finished_reason="completed"):
        self.finished_reason = finished_reason


class ModelCallStartEvent:
    def __init__(self, model_name):
        self.model_name = model_name


class ModelCallEndEvent:
    def __init__(self, incoming, outgoing, hit):
        self.input_tokens = incoming
        self.output_tokens = outgoing
        self.cache_input_tokens = hit
        self.created_at = _IDLE
        self.finished_reason = "completed"


class TextBlockDeltaEvent:
    def __init__(self, block_id, delta):
        self.block_id = block_id
        self.delta = delta


class TextBlockEndEvent:
    def __init__(self, block_id):
        self.block_id = block_id
        self.text = None


class ToolCallStartEvent:
    def __init__(self, tool_call_id, tool_call_name):
        self.tool_call_id = tool_call_id
        self.tool_call_name = tool_call_name


class ToolCallDeltaEvent:
    def __init__(self, tool_call_id, delta):
        self.tool_call_id = tool_call_id
        self.delta = delta


class ToolCallEndEvent:
    def __init__(self, tool_call_id):
        self.tool_call_id = tool_call_id


class ToolResultStartEvent:
    def __init__(self, tool_call_id, tool_call_name):
        self.tool_call_id = tool_call_id
        self.tool_call_name = tool_call_name


class ToolResultTextDeltaEvent:
    def __init__(self, tool_call_id, delta):
        self.tool_call_id = tool_call_id
        self.delta = delta


class ToolResultDataDeltaEvent:
    def __init__(self, tool_call_id, media_type, data):
        self.tool_call_id = tool_call_id
        self.media_type = media_type
        self.data = data


class ToolResultEndEvent:
    def __init__(self, tool_call_id, state):
        self.tool_call_id = tool_call_id
        self.state = state


def _play(monkeypatch) -> list[dict]:
    """跑一轮假回复，写入 CSV 后再读出。"""
    monkeypatch.setattr("engines.agents.messaging.messages.write_line", lambda model, action: None)
    store = CsvEventStore(_CSV_PATH)
    models = {"executor_role": "deepseek-flash"}
    events = [
        ReplyStartEvent("executor_role"),
        ModelCallStartEvent("deepseek-flash"),
        TextBlockDeltaEvent("b", "hel"),
        TextBlockDeltaEvent("b", "lo"),
        TextBlockEndEvent("b"),
        ToolCallStartEvent("c", "screenshot_page"),
        ToolCallDeltaEvent("c", "{"),
        ToolCallDeltaEvent("c", "}"),
        ToolCallEndEvent("c"),
        ToolResultStartEvent("t", "screenshot_page"),
        ToolResultTextDeltaEvent("t", "ok"),
        ToolResultDataDeltaEvent("t", "image/png", "AAAA"),
        ToolResultEndEvent("t", "success"),
        ModelCallEndEvent(1000, 0, 1000),
        ReplyEndEvent(),
    ]
    token = bind_sink(store)
    try:
        buf: dict = {}
        for event in events:
            AgentEventsShow.show(event, buf, models)
    finally:
        reset_sink(token)
    store.flush()
    return load_event_csv(_CSV_PATH)


def test_csv_round_trip_keeps_columns_and_types(monkeypatch):
    rows = _play(monkeypatch)
    assert [row["event_type"] for row in rows] == [
        "ReplyStartEvent",
        "TextBlockEndEvent",
        "ToolCallDeltaEvent",
        "ToolCallDeltaEvent",
        "ToolCallEndEvent",
        "ToolResultTextDeltaEvent",
        "ToolResultEndEvent",
        "ModelCallEndEvent",
        "ReplyEndEvent",
    ]
    for index, row in enumerate(rows, start=1):
        assert_event_row(row)
        assert row["seq"] == index
        assert row["task_id"] == 1
        assert row["case_title"] == "测试 Agents 工作流"
        assert row["step_seq"] == 1
        assert row["attempt"] == 1
        assert row["role_name"] == "executor_role"
        assert row["role_kind"] == "executor"
        assert row["model"] == "deepseek-flash"
        assert row["duration_ms"] >= 0

    start, text, delta0, delta1, call_end, result_delta, result_end, model_end, reply_end = rows

    assert start["phase"] == "开始"
    assert start["block_type"] == "reply"
    assert start["is_delta"] is False
    assert start["is_peak"] is None
    assert type(start["started_at"]) is datetime
    assert start["payload"] == {"role": "executor_role", "model": "deepseek-flash"}
    assert start["cost_total"] == _ZERO

    assert text["phase"] == "推理"
    assert text["block_type"] == "text"
    assert text["payload"]["text"] == "hello"
    assert text["payload"]["delta_count"] == 2
    assert type(text["payload"]["chars"]) is int

    assert delta0["is_delta"] is True
    assert delta0["payload"] == {"delta": "{", "idx": 0}
    assert delta1["payload"]["idx"] == 1
    assert type(delta0["payload"]["idx"]) is int
    assert call_end["payload"] == {"tool_name": "screenshot_page", "args": "{}"}

    assert result_delta["phase"] == "执行"
    assert result_delta["block_type"] == "tool_result"
    assert result_delta["payload"]["delta"] == "ok"
    assert result_end["status"] == "success"
    assert result_end["payload"]["result"] == "ok"
    assert result_end["media_type"] == "image/png"
    assert result_end["image_b64"] == "AAAA"

    assert model_end["block_type"] == "model_call"
    assert model_end["input_tokens"] == 1000
    assert model_end["output_tokens"] == 0
    assert model_end["cache_input_tokens"] == 1000
    assert model_end["cost_input"] == _ZERO
    assert model_end["cost_output"] == _ZERO
    assert model_end["cost_cache"] == _CACHE
    assert model_end["cost_total"] == _CACHE
    assert model_end["is_peak"] is False
    assert model_end["image_b64"] == ""

    assert reply_end["phase"] == "结束"
    assert reply_end["block_type"] == "reply"
    assert reply_end["payload"]["finished_reason"] == "completed"
    assert reply_end["cost_input"] == _ZERO
    assert reply_end["cost_output"] == _ZERO
    assert reply_end["cost_cache"] == _CACHE
    assert reply_end["cost_total"] == _CACHE
    assert type(reply_end["ended_at"]) is datetime
