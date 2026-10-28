"""知识库助手事件桥单测：AgentScope 事件 → 前端消息 + 落日志。"""

from __future__ import annotations

import json

import pytest

from agentscope.event import (
    ModelCallEndEvent,
    ModelCallStartEvent,
    ReplyEndEvent,
    ReplyStartEvent,
    TextBlockDeltaEvent,
    TextBlockEndEvent,
)
from agentscope.types import ReplyFinishedReason

from backend.apps.knowledge_assistant.transcript_log import DialogueLog
from engines.agents.realtime_vocie.events import TranscriptBridge

pytestmark = [pytest.mark.unit]


def _bridge(tmp_path):
    return TranscriptBridge(DialogueLog(tmp_path, "session-1", "user-1"))


def _records(tmp_path):
    path = next(tmp_path.glob("*.jsonl"))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _start(reply_id: str, role: str = "assistant", name: str = "知识库助手"):
    return ReplyStartEvent(
        session_id="session-1",
        reply_id=reply_id,
        name=name,
        role=role,
    )


def _end(reply_id: str, reason=ReplyFinishedReason.COMPLETED):
    return ReplyEndEvent(
        session_id="session-1",
        reply_id=reply_id,
        finished_reason=reason,
    )


def test_model_usage_is_logged_and_summed(tmp_path):
    """ModelCallEndEvent 写 model_usage 并累计 token。"""
    bridge = _bridge(tmp_path)

    payloads = bridge.handle(
        ModelCallEndEvent(
            reply_id="a1",
            input_tokens=120,
            output_tokens=30,
            cache_input_tokens=80,
            cache_creation_input_tokens=4,
        ),
    )

    assert payloads == []
    assert bridge.usage_input == 120
    assert bridge.usage_output == 30
    assert bridge.usage_cache_input == 80
    assert bridge.usage_cache_creation == 4
    records = [record for record in _records(tmp_path) if record["type"] == "event"]
    usage = [record for record in records if record["event"] == "model_usage"]
    assert usage[0]["provider"] == "dashscope"
    assert usage[0]["input_tokens"] == 120
    assert usage[0]["output_tokens"] == 30


def test_model_usage_ignores_all_zero(tmp_path):
    """全 0 usage 不写伪造事件。"""
    bridge = _bridge(tmp_path)

    bridge.handle(ModelCallEndEvent(reply_id="a1", input_tokens=0, output_tokens=0))

    assert bridge.usage_input == 0
    files = list(tmp_path.glob("*.jsonl"))
    assert not files or not [
        record for record in _records(tmp_path) if record.get("event") == "model_usage"
    ]


def test_user_turn_is_streamed_and_logged(tmp_path):
    """用户转写：先开消息，再增量，最后收敛并落日志。"""
    bridge = _bridge(tmp_path)

    opened = bridge.handle(_start("u1", role="user", name="user"))
    delta = bridge.handle(
        TextBlockDeltaEvent(reply_id="u1", block_id="b1", delta="设备怎么连"),
    )
    final = bridge.handle(TextBlockEndEvent(reply_id="u1", block_id="b1"))
    ended = bridge.handle(_end("u1"))

    assert opened == [
        {"type": "reply_start", "reply_id": "u1", "role": "user", "name": "user"},
        {"type": "state", "value": "listening"},
    ]
    assert delta == [
        {
            "type": "transcript_delta",
            "reply_id": "u1",
            "role": "user",
            "delta": "设备怎么连",
        },
    ]
    assert final == [
        {"type": "transcript_final", "reply_id": "u1", "role": "user", "text": "设备怎么连"},
    ]
    assert ended == [
        {"type": "reply_end", "reply_id": "u1", "role": "user", "reason": "completed"},
        {"type": "state", "value": "thinking"},
    ]

    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert [(m["role"], m["text"]) for m in messages] == [("user", "设备怎么连")]


def test_assistant_turn_streams_and_speaks(tmp_path):
    """助手回复：状态进入 speaking，收尾后回到 listening。"""
    bridge = _bridge(tmp_path)

    opened = bridge.handle(_start("a1"))
    bridge.handle(TextBlockDeltaEvent(reply_id="a1", block_id="b1", delta="先打开"))
    bridge.handle(TextBlockDeltaEvent(reply_id="a1", block_id="b1", delta="设备管理"))
    final = bridge.handle(TextBlockEndEvent(reply_id="a1", block_id="b1"))
    ended = bridge.handle(_end("a1"))

    assert opened == [
        {"type": "reply_start", "reply_id": "a1", "role": "assistant", "name": "知识库助手"},
        {"type": "state", "value": "speaking"},
    ]
    assert final == [
        {
            "type": "transcript_final",
            "reply_id": "a1",
            "role": "assistant",
            "text": "先打开设备管理",
        },
    ]
    assert ended == [
        {"type": "reply_end", "reply_id": "a1", "role": "assistant", "reason": "completed"},
        {"type": "state", "value": "listening"},
    ]

    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert [(m["role"], m["text"]) for m in messages] == [("assistant", "先打开设备管理")]


def test_interrupted_reply_logs_only_heard_prefix(tmp_path):
    """被打断时 TextBlockEnd 的最终文本覆盖增量全文，日志与屏幕都只保留听到的前缀。"""
    bridge = _bridge(tmp_path)
    bridge.handle(_start("a1"))
    bridge.handle(TextBlockDeltaEvent(reply_id="a1", block_id="b1", delta="先打开设备管理再连接"))
    final = bridge.handle(
        TextBlockEndEvent(reply_id="a1", block_id="b1", text="先打开设备管理"),
    )
    bridge.handle(_end("a1", ReplyFinishedReason.INTERRUPTED))

    assert final[0]["text"] == "先打开设备管理"
    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert messages[0]["text"] == "先打开设备管理"


def test_message_is_logged_once(tmp_path):
    """TextBlockEnd 与 ReplyEnd 都到达时只落一条记录。"""
    bridge = _bridge(tmp_path)
    bridge.handle(_start("a1"))
    bridge.handle(TextBlockDeltaEvent(reply_id="a1", block_id="b1", delta="你好"))
    bridge.handle(TextBlockEndEvent(reply_id="a1", block_id="b1"))
    bridge.handle(_end("a1"))

    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert len(messages) == 1


def test_state_is_deduplicated(tmp_path):
    """相同状态不重复下发。"""
    bridge = _bridge(tmp_path)

    first = bridge.handle(ModelCallStartEvent(reply_id="a1", model_name="qwen"))
    second = bridge.handle(ModelCallStartEvent(reply_id="a1", model_name="qwen"))

    assert first == [{"type": "state", "value": "thinking"}]
    assert second == []


def test_model_call_start_does_not_downgrade_speaking(tmp_path):
    """助手已开始说话后，ModelCallStart 不能把状态压回 thinking。"""
    bridge = _bridge(tmp_path)
    bridge.handle(_start("a1"))

    assert bridge.handle(ModelCallStartEvent(reply_id="a1", model_name="qwen")) == []


def test_flush_logs_partial_message_once(tmp_path):
    """用户中途结束、TextBlockEnd 未到达时，flush 补写屏幕上的部分文本且不重复。"""
    bridge = _bridge(tmp_path)
    bridge.handle(_start("a1"))
    bridge.handle(TextBlockDeltaEvent(reply_id="a1", block_id="b1", delta="去设备管理"))

    bridge.flush()
    bridge.flush()

    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert [(m["role"], m["text"]) for m in messages] == [("assistant", "去设备管理")]
