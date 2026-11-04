"""知识库助手 consumer 单测：白名单、mode 分流与文字串行；不联网。"""

from __future__ import annotations

import asyncio
import json

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.apps.knowledge_assistant.consumer import (
    KnowledgeAssistantConsumer,
    mode_from_scope,
    token_from_scope,
)
from backend.apps.knowledge_assistant.runtime import build_status_payload


def _voice_consumer() -> KnowledgeAssistantConsumer:
    """构造一个已连接、走语音模式的 consumer 替身。"""
    consumer = KnowledgeAssistantConsumer()
    consumer._closed = False
    consumer._mode = "voice"
    consumer._transport = MagicMock()
    consumer._send_json = AsyncMock()
    return consumer


def _text_consumer(max_chars: int = 5) -> KnowledgeAssistantConsumer:
    """构造一个已连接、走文字模式的 consumer 替身。"""
    consumer = _voice_consumer()
    consumer._mode = "text"
    consumer._chat = MagicMock()
    consumer._chat.config = SimpleNamespace(max_text_chars=max_chars)
    consumer._reply_task = None
    return consumer


def test_token_from_scope():
    assert token_from_scope({"query_string": b"token=abc"}) == "abc"
    assert token_from_scope({"query_string": b""}) == ""


def test_mode_from_scope_defaults_to_voice():
    """缺省与空值都按语音处理，保持旧客户端行为。"""
    assert mode_from_scope({"query_string": b"token=abc"}) == "voice"
    assert mode_from_scope({"query_string": b"token=abc&mode="}) == "voice"
    assert mode_from_scope({"query_string": b"token=abc&mode=TEXT"}) == "text"


@pytest.mark.asyncio
async def test_receive_interrupt_and_played():
    """interrupt / played 走传输；语音模式下的 text 消息被忽略。"""
    consumer = _voice_consumer()

    await consumer.receive(text_data='{"type":"interrupt"}')
    consumer._transport.push_interrupt.assert_called_once()

    await consumer.receive(text_data='{"type":"played","item_id":"i1","played_ms":12}')
    consumer._transport.report_played.assert_called_once_with("i1", 12)

    await consumer.receive(text_data='{"type":"text","text":"hello"}')
    consumer._send_json.assert_not_called()


@pytest.mark.asyncio
async def test_receive_bytes_to_transport():
    consumer = _voice_consumer()
    await consumer.receive(bytes_data=b"\x00\x01")
    consumer._transport.push_audio.assert_called_once_with(b"\x00\x01")


@pytest.mark.asyncio
async def test_receive_bytes_ignored_in_text_mode():
    """文字模式不收音频帧。"""
    consumer = _text_consumer()
    await consumer.receive(bytes_data=b"\x00\x01")
    consumer._transport.push_audio.assert_not_called()


@pytest.mark.asyncio
async def test_text_too_long_is_rejected():
    """超过上限的文本只回提示，不建回答任务。"""
    consumer = _text_consumer(max_chars=5)

    await consumer._on_text({"type": "text", "text": "一二三四五六"})

    consumer._send_json.assert_awaited_once()
    payload = consumer._send_json.await_args.args[0]
    assert payload["type"] == "notice"
    assert "最多 5 字" in payload["message"]
    assert consumer._reply_task is None


@pytest.mark.asyncio
async def test_text_is_serialized_while_answering():
    """上一条未结束时再发只回提示，不并发调用模型。"""
    consumer = _text_consumer(max_chars=100)
    consumer._reply_task = asyncio.create_task(asyncio.sleep(1))

    try:
        await consumer._on_text({"type": "text", "text": "你好"})
        payload = consumer._send_json.await_args.args[0]
        assert payload["type"] == "notice"
        assert "上一条还在回答" in payload["message"]
        consumer._chat.answer.assert_not_called()
    finally:
        consumer._reply_task.cancel()
        await asyncio.gather(consumer._reply_task, return_exceptions=True)


@pytest.mark.asyncio
async def test_blank_text_is_ignored():
    """空白文本不建任务、不提示。"""
    consumer = _text_consumer()

    await consumer._on_text({"type": "text", "text": "   "})

    consumer._send_json.assert_not_awaited()
    assert consumer._reply_task is None


def test_status_payload_has_text_fields():
    """就绪状态同时给出语音与文字两个入口。"""
    payload = build_status_payload({})

    assert {"text_model", "text_ready", "text_reason"} <= set(payload)
    assert payload["text_model"] == "deepseek-flash"
    assert payload["text_ready"] is False


def test_session_start_records_mode(tmp_path):
    """日志的 session_start 带会话方式，文字会话才能与语音区分。"""
    from backend.apps.knowledge_assistant.transcript_log import DialogueLog

    log = DialogueLog(tmp_path, "session-1", "user-1")
    log.event("session_start", mode="text", model="deepseek-flash")

    record = json.loads((next(tmp_path.glob("*.jsonl"))).read_text(encoding="utf-8"))
    assert record["event"] == "session_start"
    assert record["mode"] == "text"


@pytest.mark.asyncio
async def test_enqueue_usage_marks_chat_source(monkeypatch):
    """文字会话入账来源是 chat，语音仍是 voice。"""
    from backend.apps.knowledge_assistant import consumer as consumer_module

    calls: list[dict] = []

    def _capture(*args, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(consumer_module, "record_voice_event", _capture)

    text_future = _text_consumer()._enqueue_usage({"event": "model_usage"}, "s1", "u1")
    assert text_future is not None
    await text_future
    voice_future = _voice_consumer()._enqueue_usage({"event": "model_usage"}, "s1", "u1")
    assert voice_future is not None
    await voice_future

    assert [call["source"] for call in calls] == ["chat", "voice"]
