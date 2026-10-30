"""知识库助手 consumer 白名单单测：不联网。"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.apps.knowledge_assistant.consumer import (
    KnowledgeAssistantConsumer,
    token_from_scope,
)


def test_token_from_scope():
    assert token_from_scope({"query_string": b"token=abc"}) == "abc"
    assert token_from_scope({"query_string": b""}) == ""


@pytest.mark.asyncio
async def test_receive_interrupt_and_played():
    """interrupt / played 走传输；text 消息被忽略。"""
    consumer = KnowledgeAssistantConsumer()
    consumer._closed = False
    consumer._transport = MagicMock()
    consumer._send_json = AsyncMock()

    await consumer.receive(text_data='{"type":"interrupt"}')
    consumer._transport.push_interrupt.assert_called_once()

    await consumer.receive(text_data='{"type":"played","item_id":"i1","played_ms":12}')
    consumer._transport.report_played.assert_called_once_with("i1", 12)

    await consumer.receive(text_data='{"type":"text","text":"hello"}')
    consumer._send_json.assert_not_called()


@pytest.mark.asyncio
async def test_receive_bytes_to_transport():
    consumer = KnowledgeAssistantConsumer()
    consumer._closed = False
    consumer._transport = MagicMock()
    await consumer.receive(bytes_data=b"\x00\x01")
    consumer._transport.push_audio.assert_called_once_with(b"\x00\x01")
