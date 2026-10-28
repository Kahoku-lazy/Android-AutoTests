"""实时语音引擎配置与后端日志目录单测：不联网、不依赖数据库。"""

from __future__ import annotations

import pytest

from backend.apps.knowledge_assistant.runtime import build_status_payload, session_log_dir
from engines.agents.realtime_vocie.config import load_config
from engines.agents.realtime_vocie.knowledge import SYSTEM_PROMPT, build_system_prompt

pytestmark = [pytest.mark.unit]


def test_load_defaults_with_key():
    """只给 Key 时默认走 Omni 直接对话与 Tina 音色。"""
    config = load_config({"DASHSCOPE_API_KEY": "sk-test"})

    assert config.mode == "omni"
    assert config.model == "qwen3.5-omni-plus-realtime"
    assert config.translation_language == "zh"
    assert config.voice == "Tina"
    assert config.turn_detection == "server_vad"
    assert config.agent_name == "知识库助手"
    assert config.vad_threshold == 0.35
    assert config.vad_silence_ms == 700
    assert "DASHSCOPE" not in repr(config)


def test_load_reads_env_overrides():
    """显式配置覆盖默认值。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_REALTIME_MODE": "omni",
            "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.5-omni-flash-realtime",
            "KNOWLEDGE_ASSISTANT_VOICE": "Cherry",
            "KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE": "en",
            "KNOWLEDGE_ASSISTANT_TURN_DETECTION": "semantic_vad",
            "KNOWLEDGE_ASSISTANT_AGENT_NAME": "小知",
            "KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT": "只回答平台问题",
            "KNOWLEDGE_ASSISTANT_VAD_THRESHOLD": "0.2",
            "KNOWLEDGE_ASSISTANT_VAD_SILENCE_MS": "500",
        },
    )

    assert config.mode == "omni"
    assert config.model == "qwen3.5-omni-flash-realtime"
    assert config.translation_language == "en"
    assert config.voice == "Cherry"
    assert config.turn_detection == "semantic_vad"
    assert config.agent_name == "小知"
    assert config.system_prompt == "只回答平台问题"
    assert config.vad_threshold == 0.2
    assert config.vad_silence_ms == 500


def test_mode_infers_omni_from_model():
    """只配 omni 模型名时自动使用 omni 调用方式。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.5-omni-plus-realtime",
        },
    )

    assert config.mode == "omni"
    assert config.model == "qwen3.5-omni-plus-realtime"


def test_mode_infers_livetranslate_from_model():
    """只配实时翻译模型名时自动使用 livetranslate 调用方式。"""
    config = load_config(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.8-livetranslate-flash-realtime",
        },
    )

    assert config.mode == "livetranslate"
    assert config.model == "qwen3.8-livetranslate-flash-realtime"


def test_mode_rejects_model_mismatch():
    """显式 livetranslate 模式不能配 omni 模型。"""
    with pytest.raises(RuntimeError, match="livetranslate"):
        load_config(
            {
                "DASHSCOPE_API_KEY": "sk-test",
                "KNOWLEDGE_ASSISTANT_REALTIME_MODE": "livetranslate",
                "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.5-omni-plus-realtime",
            },
        )


def test_session_log_dir_defaults_and_override(tmp_path):
    """日志目录默认 logs/knowledge_assistant，可由环境变量覆盖。"""
    assert (
        session_log_dir({}, base_dir=tmp_path)
        == (tmp_path / "logs" / "knowledge_assistant").resolve()
    )
    assert (
        session_log_dir(
            {"KNOWLEDGE_ASSISTANT_LOG_DIR": "logs/custom_kb"},
            base_dir=tmp_path,
        )
        == (tmp_path / "logs" / "custom_kb").resolve()
    )


def test_load_rejects_missing_key():
    """缺少 DASHSCOPE_API_KEY 时给出可读配置错误。"""
    with pytest.raises(RuntimeError, match="DASHSCOPE_API_KEY"):
        load_config({})


def test_load_rejects_disabled():
    """功能关闭时拒绝建立会话。"""
    with pytest.raises(RuntimeError, match="已关闭"):
        load_config(
            {"KNOWLEDGE_ASSISTANT_ENABLED": "false", "DASHSCOPE_API_KEY": "sk-test"},
        )


def test_load_rejects_unknown_turn_detection():
    """不支持的回合检测方式被拒绝。"""
    with pytest.raises(RuntimeError, match="TURN_DETECTION"):
        load_config(
            {
                "DASHSCOPE_API_KEY": "sk-test",
                "KNOWLEDGE_ASSISTANT_TURN_DETECTION": "none",
            },
        )


def test_status_not_ready_without_key():
    """缺少 Key 时状态接口返回未就绪与中文原因。"""
    payload = build_status_payload({})

    assert payload["enabled"] is True
    assert payload["ready"] is False
    assert "DASHSCOPE_API_KEY" in payload["reason"]
    assert payload["log_dir"] == "logs/knowledge_assistant"
    assert "sk-test" not in payload.values()


def test_status_infers_omni_mode_from_model():
    """状态接口与 load_config 使用同一套 mode 推断，避免显示和实际不一致。"""
    payload = build_status_payload(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_MODEL": "qwen3.5-omni-plus-realtime",
        },
    )

    assert payload["ready"] is True
    assert payload["mode"] == "omni"
    assert payload["model"] == "qwen3.5-omni-plus-realtime"


def test_status_ready_with_key():
    """Key 与依赖齐全时状态接口返回就绪。"""
    payload = build_status_payload({"DASHSCOPE_API_KEY": "sk-test"})

    assert payload["ready"] is True
    assert payload["reason"] == ""
    assert payload["mode"] == "omni"
    assert payload["model"] == "qwen3.5-omni-plus-realtime"
    assert payload["pipeline_llm_model"] == "deepseek-flash"
    assert payload["pipeline_tts_model"] == "sambert-zhichu-v1"
    assert payload["pipeline_tts_voice"] == "知厨"


def test_system_prompt_is_direct_dialogue_without_presets():
    """提示词只保留直接对话约束，不注入平台知识速览或预设答案。"""
    prompt = build_system_prompt()

    assert prompt == SYSTEM_PROMPT
    assert "直接对话" in prompt
    assert "三句话" in prompt
    assert "设备管理" not in prompt
    assert "串口日志" not in prompt
    assert "不要声称拥有文档库" not in prompt
