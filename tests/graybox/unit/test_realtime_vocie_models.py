"""实时语音模型选择与实时翻译协议映射单测：不联网。"""

from __future__ import annotations

import base64

import pytest

from agentscope.credential import DashScopeCredential
from agentscope.realtime import DashScopeRealtimeModel
from agentscope.realtime import _events as me

from engines.agents.realtime_vocie.config import create_realtime_model, load_config
from engines.agents.realtime_vocie.livetranslate import (
    LIVETRANSLATE_MODEL,
    LiveTranslateRealtimeModel,
)

pytestmark = [pytest.mark.unit]


def test_default_mode_builds_omni_realtime_model():
    """默认配置构造 Omni 直接对话适配器。"""
    model = create_realtime_model(load_config({"DASHSCOPE_API_KEY": "sk-test"}))

    assert isinstance(model, DashScopeRealtimeModel)
    assert not isinstance(model, LiveTranslateRealtimeModel)
    assert model.card.name == "qwen3.5-omni-plus-realtime"


def test_livetranslate_mode_builds_translate_adapter():
    """显式 livetranslate 模式构造实时翻译适配器。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_REALTIME_MODE": "livetranslate",
            "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.8-livetranslate-flash-realtime",
        },
    )
    model = create_realtime_model(config)

    assert isinstance(model, LiveTranslateRealtimeModel)
    assert model.card.name == LIVETRANSLATE_MODEL
    assert model.parameters.translation_language == "zh"
    assert model.parameters.voice == "Tina"


def _live_model() -> LiveTranslateRealtimeModel:
    return LiveTranslateRealtimeModel(
        model=LIVETRANSLATE_MODEL,
        credential=DashScopeCredential(api_key="sk-test"),
    )


def test_livetranslate_session_update_uses_translation_fields():
    """session.update 使用 output_modalities / translation / speaker_detection。"""
    model = _live_model()

    update = model._session_update("ignored", None)

    assert update["type"] == "session.update"
    session = update["session"]
    assert session["voice"] == "Tina"
    assert session["translation"] == {"language": "zh"}
    assert session["output_modalities"] == ["text", "audio"]
    assert session["audio"]["input"]["turn_detection"]["type"] == "speaker_detection"


def test_livetranslate_parse_translated_text_and_audio():
    """译文增量与音频增量映射到 AgentScope 事件。"""
    model = _live_model()
    created = model._parse(
        {"type": "response.created", "response": {"id": "resp_1"}},
    )
    text = model._parse(
        {
            "type": "response.audio_transcript.delta",
            "delta": "How do you connect?",
        },
    )
    audio = model._parse(
        {
            "type": "response.audio.delta",
            "delta": base64.b64encode(b"\x00\x01").decode(),
        },
    )
    done = model._parse(
        {"type": "response.done", "response": {"id": "resp_1"}},
    )

    assert isinstance(created, me.ResponseCreatedEvent)
    assert created.item_id == "resp_1"
    assert isinstance(text, me.TranscriptDeltaEvent)
    assert text.delta == "How do you connect?"
    assert isinstance(audio, me.AudioDeltaEvent)
    assert audio.pcm == b"\x00\x01"
    assert audio.sample_rate == 24000
    assert isinstance(done, me.ResponseDoneEvent)


def test_livetranslate_parse_speech_and_source_transcript():
    """speaker_detection 与源语种转写映射到用户回合事件。"""
    model = _live_model()

    started = model._parse(
        {"type": "input_audio_buffer.speech_started", "item_id": "item_1"},
    )
    stopped = model._parse(
        {"type": "input_audio_buffer.speech_stopped", "item_id": "item_1"},
    )
    transcript = model._parse(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "item_1",
            "transcript": "设备管理里怎么连接设备",
        },
    )

    assert isinstance(started, me.SpeechStartedEvent)
    assert isinstance(stopped, me.SpeechEndedEvent)
    assert isinstance(transcript, me.InputTranscriptionEvent)
    assert transcript.text == "设备管理里怎么连接设备"
