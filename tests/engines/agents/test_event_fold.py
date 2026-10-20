"""事件折叠：增量合并、工具逐条、角色继承、8 位费用与图片。"""

from __future__ import annotations

from decimal import Decimal

from engines.agents.event_sink import bind_sink, current_sink, reset_sink
from engines.agents.messaging.fold import step
from engines.agents.messaging.messages import AgentEventsShow
from engines.agents.messaging.record import EventRecord

_IDLE = "2026-10-18T10:00:00+08:00"


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


class DataBlockDeltaEvent:
    def __init__(self, block_id, media_type, data):
        self.block_id = block_id
        self.media_type = media_type
        self.data = data


class DataBlockEndEvent:
    def __init__(self, block_id):
        self.block_id = block_id


class CustomEvent:
    pass


def test_text_deltas_collapse_into_one_record():
    state: dict = {}
    assert step(TextBlockDeltaEvent("b", "hel"), state, None).records == []
    assert step(TextBlockDeltaEvent("b", "lo"), state, None).records == []
    result = step(TextBlockEndEvent("b"), state, None)
    assert result.log_lines == []
    record = result.records[0]
    assert record.payload["text"] == "hello"
    assert record.payload["delta_count"] == 2
    assert record.phase == "推理"
    assert record.block_type == "text"


def test_tool_call_deltas_keep_indexes_and_end_joins_args():
    state: dict = {}
    step(ReplyStartEvent("executor_role"), state, {"executor_role": "deepseek-flash"})
    assert step(ToolCallStartEvent("c", "screenshot_page"), state, None).records == []
    first = step(ToolCallDeltaEvent("c", "{"), state, None)
    second = step(ToolCallDeltaEvent("c", "}"), state, None)
    end = step(ToolCallEndEvent("c"), state, None)
    assert first.log_lines == []
    assert first.records[0].is_delta is True
    assert first.records[0].payload == {"delta": "{", "idx": 0}
    assert second.records[0].payload["idx"] == 1
    assert end.records[0].payload["tool_name"] == "screenshot_page"
    assert end.records[0].payload["args"] == "{}"
    assert [action for _model, action in end.log_lines] == ["工具调用 | screenshot_page | {}"]
    assert end.records[0].role_name == "executor_role"
    assert end.records[0].role_kind == "executor"


def test_tool_result_text_delta_and_end_status():
    state: dict = {}
    step(ToolResultStartEvent("t", "click_ratio"), state, None)
    delta = step(ToolResultTextDeltaEvent("t", "ok"), state, None)
    end = step(ToolResultEndEvent("t", "success"), state, None)
    assert delta.records[0].payload == {"delta": "ok", "idx": 0}
    assert end.records[0].phase == "执行"
    assert end.records[0].block_type == "tool_result"
    assert end.records[0].payload["tool_name"] == "click_ratio"
    assert end.records[0].payload["status"] == "success"
    assert end.records[0].payload["result"] == "ok"


def test_role_switches_on_the_next_reply():
    state: dict = {}
    start = step(ReplyStartEvent("executor_role"), state, {})
    assert start.records[0].event_type == "ReplyStartEvent"
    assert start.records[0].phase == "开始"
    assert start.records[0].block_type == "reply"
    assert start.log_lines[0][1] == "开始 | executor_role"
    step(ReplyStartEvent("verifier_role"), state, {})
    end = step(ToolCallEndEvent("x"), state, None)
    assert end.records[0].role_name == "verifier_role"
    assert end.records[0].role_kind == "verifier"


def test_custom_event_is_ignored():
    result = step(CustomEvent(), {}, None)
    assert result.log_lines == []
    assert result.records == []


def test_screenshot_base64_stays_out_of_the_log():
    secret = "AAAA_SECRET_B64"
    state: dict = {}
    step(ToolResultStartEvent("t", "screenshot_page"), state, None)
    assert step(ToolResultDataDeltaEvent("t", "image/png", secret), state, None).records == []
    end = step(ToolResultEndEvent("t", "success"), state, None)
    logged = " ".join(action for _model, action in end.log_lines)
    assert secret not in logged
    assert "image/png" in logged
    assert "字符base64" in logged
    assert end.records[0].image_b64 == secret
    assert end.records[0].media_type == "image/png"


def test_data_block_base64_is_joined_on_end_without_a_log_line():
    state: dict = {}
    assert step(DataBlockDeltaEvent("d", "image/png", "QQQ"), state, None).records == []
    end = step(DataBlockEndEvent("d"), state, None)
    assert end.log_lines == []
    assert end.records[0].block_type == "data"
    assert end.records[0].image_b64 == "QQQ"


def test_model_name_is_carried_from_start_to_end():
    state: dict = {}
    assert step(ModelCallStartEvent("deepseek-v4-pro"), state, None).records == []
    end = step(ModelCallEndEvent(0, 0, 0), state, None)
    assert end.records[0].model == "deepseek-v4-pro"
    assert end.records[0].block_type == "model_call"


def test_cache_fee_is_the_same_on_the_log_and_the_record():
    state: dict = {}
    step(ModelCallStartEvent("deepseek-flash"), state, None)
    result = step(ModelCallEndEvent(1000, 0, 1000), state, None)
    record = result.records[0]
    fees = [action for _model, action in result.log_lines if action.startswith("模型费用")]
    assert fees == ["模型费用：0.00000000元，0.00000000元，0.00002000元"]
    assert record.cost_input == Decimal("0.00000000")
    assert record.cost_output == Decimal("0.00000000")
    assert record.cost_cache == Decimal("0.00002000")


def test_reply_fee_total_is_the_sum_of_eight_decimal_calls():
    state: dict = {}
    step(ReplyStartEvent("executor_role"), state, {"executor_role": "deepseek-flash"})
    step(ModelCallStartEvent("deepseek-flash"), state, None)
    first = step(ModelCallEndEvent(1000, 0, 1000), state, None)
    step(ModelCallStartEvent("deepseek-flash"), state, None)
    second = step(ModelCallEndEvent(1000, 0, 1000), state, None)
    end = step(ReplyEndEvent(), state, None)
    cache = first.records[0].cost_cache + second.records[0].cost_cache
    fees = [action for _model, action in end.log_lines if "模型费用" in action]
    assert fees == [f"本轮执行总计量 | 模型费用：0.00000000元，0.00000000元，{cache:.8f}元"]
    assert cache == Decimal("0.00004000")


def test_unbound_sink_accepts_record_and_image():
    current_sink().emit(EventRecord("ReplyStartEvent", "开始", "reply"), "abc")


def test_sink_error_still_writes_the_log(monkeypatch):
    lines: list[str] = []
    warnings: list[str] = []
    monkeypatch.setattr(
        "engines.agents.messaging.messages.write_line",
        lambda model, action: lines.append(action),
    )
    monkeypatch.setattr(
        "engines.agents.messaging.messages.agent_event_log.warning",
        lambda text: warnings.append(text),
    )

    class Boom:
        def emit(self, record, image_b64=""):
            raise RuntimeError("down")

    token = bind_sink(Boom())
    try:
        AgentEventsShow.show(
            ReplyStartEvent("executor_role"),
            {},
            {"executor_role": "deepseek-flash"},
        )
    finally:
        reset_sink(token)
    assert lines == ["开始 | executor_role"]
    assert warnings
    assert "RuntimeError" in warnings[0]
