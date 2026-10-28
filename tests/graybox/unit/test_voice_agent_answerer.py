"""语音 pipeline 的 Agent 回答链路：TTS 适配、事件映射、配置开关。"""

from __future__ import annotations

import base64

import pytest

from engines.agents.realtime_vocie.agent_answerer import AgentAnswerer
from engines.agents.realtime_vocie.config import load_config
from engines.agents.realtime_vocie.tts_model import LocalTtsModel

pytestmark = [pytest.mark.unit]


class TextBlockDeltaEvent:
    """替身：文本增量事件。"""

    def __init__(self, delta: str) -> None:
        self.delta = delta


class DataBlockDeltaEvent:
    """替身：音频增量事件。"""

    def __init__(self, data: str) -> None:
        self.data = data


class ModelCallEndEvent:
    """替身：模型调用结束事件。"""

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


class _FakeAgent:
    """按预设事件序列吐事件的假智能体。"""

    def __init__(self, events: list) -> None:
        self._events = events

    def reply_stream(self, inputs, yield_final_msg: bool = True):
        del inputs, yield_final_msg

        async def gen():
            for event in self._events:
                yield event

        return gen()


class _Engine:
    """假 TTS 引擎：按预设返回 PCM。"""

    def __init__(self, pcm: bytes) -> None:
        self._pcm = pcm
        self.texts: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.texts.append(text)
        return self._pcm


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# ── 事件映射 ──────────────────────────────────────────────


async def test_stream_maps_text_and_collects_audio() -> None:
    agent = _FakeAgent(
        [
            TextBlockDeltaEvent("你"),
            TextBlockDeltaEvent("好"),
            DataBlockDeltaEvent(_b64(b"\x01\x02")),
            DataBlockDeltaEvent(_b64(b"\x03")),
            ModelCallEndEvent(
                input_tokens=10,
                output_tokens=5,
                cache_input_tokens=2,
                cache_creation_input_tokens=1,
            ),
        ]
    )
    answerer = AgentAnswerer(agent)

    deltas = [delta async for delta in answerer.stream("你好")]

    assert deltas == ["你", "好"]
    assert answerer.take_audio() == b"\x01\x02\x03"
    assert answerer.last_usage == {
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_input_tokens": 2,
        "cache_creation_input_tokens": 1,
    }


async def test_take_audio_clears_buffer() -> None:
    answerer = AgentAnswerer(_FakeAgent([DataBlockDeltaEvent(_b64(b"\x09"))]))
    await anext(answerer.stream("x"), None)

    assert answerer.take_audio() == b"\x09"
    assert answerer.take_audio() == b""


async def test_bad_audio_chunk_is_skipped() -> None:
    answerer = AgentAnswerer(_FakeAgent([DataBlockDeltaEvent("不是 base64")]))

    await anext(answerer.stream("x"), None)

    assert answerer.take_audio() == b""


# ── TTS 适配 ──────────────────────────────────────────────


async def test_tts_model_returns_one_pcm_block() -> None:
    engine = _Engine(b"\x00\x01")
    model = LocalTtsModel(engine, model="sambert-zhichu-v1", api_key="test-key")

    response = await model.synthesize("你好")

    assert response.content is not None
    assert response.content.source.media_type == "audio/pcm;rate=24000"
    assert base64.b64decode(response.content.source.data) == b"\x00\x01"
    assert engine.texts == ["你好"]


async def test_tts_model_without_audio_returns_empty_content() -> None:
    model = LocalTtsModel(_Engine(b""), model="sambert-zhichu-v1", api_key="test-key")

    assert (await model.synthesize("你好")).content is None


async def test_tts_model_keeps_engine_sample_rate() -> None:
    """适配器不固定采样率：音色与采样率沿用引擎实际输出。"""

    class _RateEngine:
        sample_rate = 16000

        async def synthesize(self, text: str) -> bytes:
            del text
            return b"\x05"

    model = LocalTtsModel(_RateEngine(), model="sambert-zhichu-v1", api_key="test-key")

    response = await model.synthesize("你好")

    assert response.content is not None
    assert response.content.source.media_type == "audio/pcm;rate=16000"


# ── 配置开关 ──────────────────────────────────────────────


def _config(**overrides) -> dict:
    base = {"DASHSCOPE_API_KEY": "test-key"}
    base.update(overrides)
    return base


def test_default_voice_stays_zhichu() -> None:
    """改用 Agent 后默认音色与 provider 都不动：sambert + 知厨。"""
    config = load_config(_config())

    assert config.pipeline_tts_provider == "sambert"
    assert config.pipeline_tts_model == "sambert-zhichu-v1"
    assert config.pipeline_tts_voice == "知厨"
    assert config.pipeline_engine == "agent"


def test_pipeline_engine_defaults_to_agent() -> None:
    assert load_config(_config()).pipeline_engine == "agent"


def test_pipeline_engine_can_fall_back_to_legacy() -> None:
    config = load_config(_config(KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE="legacy"))

    assert config.pipeline_engine == "legacy"


def test_pipeline_engine_rejects_unknown_value() -> None:
    with pytest.raises(RuntimeError):
        load_config(_config(KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE="nonsense"))


def test_unknown_engine_keeps_message_readable() -> None:
    with pytest.raises(RuntimeError, match="KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE"):
        load_config(_config(KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE="nonsense"))
