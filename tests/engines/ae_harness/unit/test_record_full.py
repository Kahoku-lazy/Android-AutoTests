"""ae_harness 记录保真度：全量模式字段补齐、取消截断、仍按块折叠。

只测 `event/record.py` 的全量开关；替身事件带齐框架字段。
不测用量归属（`test_record_usage.py`）与观测中间件（`test_observer.py`）。
"""

from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from engines.ae_harness.event.record import AgentEventRecorder

pytestmark = [pytest.mark.unit]

STAMP = "2026-11-14T18:40:44.944345"
EVENT_ID = "ev-0001"
SESSION = "sess-0001"
LABEL = "GOVEE_API_KEY"


@dataclass
class ReplyEndEvent:
    """替身：回复结束，带框架公共字段。"""

    finished_reason: str = "completed"
    error: object = None
    session_id: str = SESSION
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class HintBlockEvent:
    """替身：提示块，带来源标签。"""

    hint: str = "同一条提示"
    source: str = '{"label": "System"}'
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ThinkingBlockEndEvent:
    """替身：思考块结束。"""

    block_id: str = "b1"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ThinkingBlockDeltaEvent:
    """替身：思考增量。"""

    block_id: str = "b1"
    delta: str = ""
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolResultEndEvent:
    """替身：工具结果结束。"""

    tool_call_id: str = "t1"
    state: str = "success"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCallStartEvent:
    """替身：工具调用开始。"""

    tool_call_id: str = "t1"
    tool_call_name: str = "adb_devices"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCallDeltaEvent:
    """替身：工具调用参数增量。"""

    tool_call_id: str = "t1"
    delta: str = "{}"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCallEndEvent:
    """替身：工具调用参数结束。"""

    tool_call_id: str = "t1"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolResultStartEvent:
    """替身：工具开始执行。"""

    tool_call_id: str = "t1"
    tool_call_name: str = "adb_devices"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolResultTextDeltaEvent:
    """替身：工具输出增量。"""

    tool_call_id: str = "t1"
    delta: str = "1 台设备"
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


@dataclass
class TextBlockEndEvent:
    """替身：文本块结束。"""

    block_id: str = "b2"
    text: object = None
    created_at: str = STAMP
    id: str = EVENT_ID
    metadata: dict = field(default_factory=dict)


def _tool_round(call_id: str = "t1") -> list:
    """造一轮完整工具往返：调用开始 → 参数增量 → 参数结束 → 执行 → 输出 → 结束。"""
    return [
        ToolCallStartEvent(tool_call_id=call_id),
        ToolCallDeltaEvent(tool_call_id=call_id),
        ToolCallEndEvent(tool_call_id=call_id),
        ToolResultStartEvent(tool_call_id=call_id),
        ToolResultTextDeltaEvent(tool_call_id=call_id),
        ToolResultEndEvent(tool_call_id=call_id),
    ]


def _recorder(tmp_path: Path, **kwargs) -> AgentEventRecorder:
    """建一个把产物落到临时目录的记录器，绝不写当前工作目录。"""
    return AgentEventRecorder(tmp_path, "probe", **kwargs)


def _rows(recorder: AgentEventRecorder, events: list) -> list[dict]:
    """把事件喂进记录器，返回落盘的 JSON 行。"""
    recorder.begin("probe")
    for event in events:
        recorder.on_event(event)
    record = recorder.finish(0.1)
    return [
        json.loads(line) for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
    ]


def test_full_mode_is_default(tmp_path: Path):
    """不传开关时按全量模式产出。"""
    recorder = _recorder(tmp_path)
    assert recorder._full is True  # noqa: SLF001 - 直接断言默认值


def test_full_mode_adds_public_fields(tmp_path: Path):
    """全量模式下事件行带绝对时刻与事件标识。"""
    rows = _rows(_recorder(tmp_path), [ReplyEndEvent()])
    row = next(r for r in rows if r["event"] == "ReplyEndEvent")
    assert row["created_at"] == STAMP
    assert row["event_id"] == EVENT_ID
    assert row["session_id"] == SESSION


def test_full_mode_writes_metadata_when_present(tmp_path: Path):
    """metadata 非空才写。"""
    empty = _rows(_recorder(tmp_path), [ReplyEndEvent()])
    assert "metadata" not in next(r for r in empty if r["event"] == "ReplyEndEvent")

    filled = _rows(_recorder(tmp_path), [ReplyEndEvent(metadata={"k": 1})])
    assert next(r for r in filled if r["event"] == "ReplyEndEvent")["metadata"] == {"k": 1}


def test_full_mode_adds_hint_source(tmp_path: Path):
    """提示块行同时有 hint 与 source。"""
    rows = _rows(_recorder(tmp_path), [HintBlockEvent()])
    row = next(r for r in rows if r["event"] == "HintBlockEvent")
    assert row["hint"] == "同一条提示"
    assert row["source"] == '{"label": "System"}'


def test_full_mode_keeps_thinking_whole(tmp_path: Path):
    """全量模式下思考正文不截断。"""
    long_text = "想" * 1200
    recorder = _recorder(tmp_path)
    rows = _rows(
        recorder,
        [
            ThinkingBlockDeltaEvent(delta=long_text),
            ThinkingBlockEndEvent(),
        ],
    )
    row = next(r for r in rows if r["event"] == "ThinkingBlockEndEvent")
    assert len(row["thinking"]) == 1200


def test_compact_mode_truncates_and_omits_fields(tmp_path: Path):
    """关闭全量后：思考被截断、公共字段不写。"""
    long_text = "想" * 1200
    recorder = _recorder(tmp_path, full=False)
    rows = _rows(
        recorder,
        [
            ThinkingBlockDeltaEvent(delta=long_text),
            ThinkingBlockEndEvent(),
            ReplyEndEvent(),
        ],
    )
    thinking = next(r for r in rows if r["event"] == "ThinkingBlockEndEvent")
    assert len(thinking["thinking"]) < 1200
    assert "created_at" not in thinking
    assert "event_id" not in thinking

    end = next(r for r in rows if r["event"] == "ReplyEndEvent")
    assert "session_id" not in end
    assert "created_at" not in end


def test_full_mode_keeps_tool_output_whole(tmp_path: Path):
    """全量模式下工具输出不截断。"""
    long_output = "o" * 5000
    recorder = _recorder(tmp_path)
    recorder.begin("probe")
    event = ToolResultEndEvent()
    recorder._buf[f"res:{event.tool_call_id}"] = long_output  # noqa: SLF001
    recorder.on_event(event)
    record = recorder.finish(0.1)
    rows = [
        json.loads(line) for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
    ]
    row = next(r for r in rows if r["event"] == "ToolResultEndEvent")
    assert len(row["output"]) == 5000


def test_delta_events_not_written_in_full_mode(tmp_path: Path):
    """全量模式仍按块折叠：增量不单独成行。"""
    events = [ThinkingBlockDeltaEvent(delta="片") for _ in range(100)]
    events.append(ThinkingBlockEndEvent())
    rows = _rows(_recorder(tmp_path), events)
    kinds = [r["event"] for r in rows]
    assert kinds.count("ThinkingBlockDeltaEvent") == 0
    assert kinds.count("ThinkingBlockEndEvent") == 1


def test_tool_rows_share_call_id(tmp_path: Path):
    """调用行与结果行带同一个工具调用标识，可据此配对。"""
    rows = _rows(_recorder(tmp_path), _tool_round("call-abc"))
    call = next(r for r in rows if r["event"] == "ToolCallEndEvent")
    result = next(r for r in rows if r["event"] == "ToolResultEndEvent")
    assert call["tool_call_id"] == "call-abc"
    assert result["tool_call_id"] == "call-abc"
    assert call["tool_call_id"] == result["tool_call_id"]
    assert call["input"] == "{}"
    assert result["output"] == "1 台设备"


def test_block_rows_carry_block_id(tmp_path: Path):
    """思考块与文本块各带自己的块标识。"""
    recorder = _recorder(tmp_path)
    rows = _rows(
        recorder,
        [
            ThinkingBlockDeltaEvent(block_id="think-1", delta="想"),
            ThinkingBlockEndEvent(block_id="think-1"),
            TextBlockEndEvent(block_id="text-1", text="答"),
        ],
    )
    think = next(r for r in rows if r["event"] == "ThinkingBlockEndEvent")
    text = next(r for r in rows if r["event"] == "TextBlockEndEvent")
    assert think["block_id"] == "think-1"
    assert text["block_id"] == "text-1"
    assert think["block_id"] != text["block_id"]


def test_association_keys_present_when_compact(tmp_path: Path):
    """关联键与开关无关：非全量模式下仍然写入。"""
    recorder = _recorder(tmp_path, full=False)
    rows = _rows(
        recorder,
        _tool_round("call-xyz") + [ThinkingBlockEndEvent(block_id="think-9")],
    )
    call = next(r for r in rows if r["event"] == "ToolCallEndEvent")
    result = next(r for r in rows if r["event"] == "ToolResultEndEvent")
    think = next(r for r in rows if r["event"] == "ThinkingBlockEndEvent")
    assert call["tool_call_id"] == "call-xyz"
    assert result["tool_call_id"] == "call-xyz"
    assert think["block_id"] == "think-9"


async def test_observation_rows_unaffected_by_full(tmp_path: Path):
    """观测行字段集合与开关无关。"""
    from engines.ae_harness.middleware import ObservationMiddleware

    shapes = {}
    for full in (True, False):
        observer = ObservationMiddleware()
        recorder = _recorder(tmp_path, observations=observer.records, full=full)
        recorder.begin("probe")
        await observer.on_system_prompt(None, "x")
        record = recorder.finish(0.1)
        rows = [
            json.loads(line)
            for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
        ]
        shapes[full] = sorted(next(r for r in rows if r["event"] == "observation"))
    assert shapes[True] == shapes[False]
