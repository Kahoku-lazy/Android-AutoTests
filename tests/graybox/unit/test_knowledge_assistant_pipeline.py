"""Pipeline 路线配置、模式切换与 TTS WAV 转换单测：不联网。"""

from __future__ import annotations

import array
import io
import wave

import pytest

from engines.agents.realtime_vocie.config import (
    PIPELINE_MODE,
    load_config,
    select_mode,
)
from engines.agents.realtime_vocie.pipeline_tts import _split_text, _wav_to_pcm

pytestmark = [pytest.mark.unit]


def test_load_pipeline_config_defaults():
    """pipeline 模式默认用 livetranslate 做 ASR、Cherry 做 TTS。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_REALTIME_MODE": "pipeline",
        },
    )

    assert config.mode == PIPELINE_MODE
    assert config.model == "qwen3.8-livetranslate-flash-realtime"
    assert config.voice == "知厨"
    assert config.pipeline_llm_model == "deepseek-flash"
    assert config.pipeline_tts_provider == "sambert"
    assert config.pipeline_tts_model == "sambert-zhichu-v1"
    assert config.pipeline_tts_voice == "知厨"


def test_pipeline_can_switch_tts_provider_to_qwen():
    """显式 qwen provider 时使用 qwen3-tts-flash/Cherry。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_REALTIME_MODE": "pipeline",
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER": "qwen",
        },
    )

    assert config.pipeline_tts_provider == "qwen"
    assert config.pipeline_tts_model == "qwen3-tts-flash"
    assert config.pipeline_tts_voice == "Cherry"


def test_select_mode_switches_models_and_voice():
    """同一基础配置可按连接切到 pipeline，再切回 omni。"""
    base = load_config({"DASHSCOPE_API_KEY": "sk-test"})
    pipeline = select_mode(base, "pipeline")
    omni = select_mode(pipeline, "omni")

    assert pipeline.mode == "pipeline"
    assert pipeline.model == "qwen3.8-livetranslate-flash-realtime"
    assert pipeline.voice == "知厨"
    assert omni.mode == "omni"
    assert omni.model == "qwen3.5-omni-plus-realtime"
    assert omni.voice == "Tina"


def test_select_mode_rejects_unknown_route():
    """未知路线返回 ValueError，由 consumer 转成可读错误。"""
    base = load_config({"DASHSCOPE_API_KEY": "sk-test"})

    with pytest.raises(ValueError, match="不支持的语音路线"):
        select_mode(base, "unknown")


def test_wav_to_pcm_downmixes_stereo_and_resamples():
    """48k 立体声 WAV 转成 24k 单声道 PCM16。"""
    rate = 48000
    frames = array.array("h")
    for _ in range(rate):
        frames.append(0)
        frames.append(16384)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(2)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(frames.tobytes())

    pcm = _wav_to_pcm(buffer.getvalue(), 24000)

    assert len(pcm) == 24000 * 2
    samples = array.array("h")
    samples.frombytes(pcm)
    assert 7000 <= samples[0] <= 9000


def test_split_text_keeps_chunks_under_limit():
    """长回答按标点切分，每段不超过 500 字符。"""
    text = "第一句。" * 200

    parts = _split_text(text)

    assert len(parts) > 1
    assert all(len(part) <= 500 for part in parts)
    assert "".join(parts) == text
