"""知识库用量出口：代理透传、事件字段、零 token 不记与打标。

用替身模型承接调用，不联网、不调真实嵌入 API。
独立性（无兄弟包 import）由 test_knowledge_independence.py 守护。
"""

from __future__ import annotations

import pytest

from agentscope.embedding import EmbeddingResponse, EmbeddingUsage

from engines.ae_harness.knowledge.usage import UsageEvent, UsageRecordingEmbedding, tag_events

pytestmark = [pytest.mark.unit]


class _FakeEmbedding:
    """替身嵌入模型：返回预置响应并记录收到的输入。"""

    model = "text-embedding-v4"
    dimensions = 4
    supports_multimodal = False

    def __init__(self, response: EmbeddingResponse) -> None:
        """保存预置响应。

        Args:
            response: 每次调用返回的响应。
        """
        self.response = response
        self.seen: list = []

    async def __call__(self, inputs, **kwargs):
        """记录输入并返回预置响应。"""
        self.seen.append((inputs, kwargs))
        return self.response


def _response(tokens: int | None) -> EmbeddingResponse:
    """造一条带用量的响应。

    Args:
        tokens: token 数；None 表示不带 usage。

    Returns:
        嵌入响应。
    """
    usage = None if tokens is None else EmbeddingUsage(tokens=tokens, time=0.25)
    return EmbeddingResponse(embeddings=[[0.1, 0.2, 0.3, 0.4]], usage=usage)


async def test_proxy_passes_through_response_and_attributes():
    """代理原样透传响应与输入，并委托维度/多模态属性。"""
    response = _response(12)
    fake = _FakeEmbedding(response)
    proxy = UsageRecordingEmbedding(fake, "DASHSCOPE_API_KEY")

    assert proxy.dimensions == 4
    assert proxy.supports_multimodal is False
    assert proxy.model == "text-embedding-v4"

    got = await proxy(["问题"], text_type="query")
    assert got is response
    assert fake.seen == [(["问题"], {"text_type": "query"})]


async def test_event_fields_complete():
    """事件字段齐全：模型名、密钥环境变量名、token、耗时与时间戳。"""
    proxy = UsageRecordingEmbedding(_FakeEmbedding(_response(12)), "DASHSCOPE_API_KEY")
    await proxy(["问题"])

    events = proxy.drain_events()
    assert len(events) == 1
    event = events[0]
    assert event.model == "text-embedding-v4"
    assert event.api_key_env == "DASHSCOPE_API_KEY"
    assert event.tokens == 12
    assert event.time == 0.25
    assert event.occurred_at
    assert event.phase == ""
    assert event.base == ""
    assert set(event.as_dict()) == {
        "model",
        "api_key_env",
        "tokens",
        "time",
        "phase",
        "base",
        "occurred_at",
    }


async def test_zero_or_missing_tokens_produce_no_event():
    """usage 缺失或 token 为 0 时不产事件。"""
    for tokens in (None, 0):
        proxy = UsageRecordingEmbedding(_FakeEmbedding(_response(tokens)), "DASHSCOPE_API_KEY")
        await proxy(["问题"])
        assert proxy.drain_events() == []


async def test_drain_clears_events():
    """drain 取出后内部清空，再次 drain 为空。"""
    proxy = UsageRecordingEmbedding(_FakeEmbedding(_response(5)), "DASHSCOPE_API_KEY")
    await proxy(["一"])
    await proxy(["二"])
    assert len(proxy.drain_events()) == 2
    assert proxy.drain_events() == []


def test_tag_events_sets_phase_and_base():
    """打标返回新事件，原事件不变。"""
    event = UsageEvent(model="m", api_key_env="E", tokens=1, time=0.1)
    tagged = tag_events([event], phase="index", base="kb")
    assert tagged[0].phase == "index"
    assert tagged[0].base == "kb"
    assert event.phase == ""
    assert event.base == ""
