"""知识库助手 Omni 配置单测：不联网。"""

from __future__ import annotations

import pytest

from engines.agents.realtime_vocie.config import (
    OMNI_MODE,
    build_runtime_status,
    load_config,
)


def _env(**extra: str) -> dict[str, str]:
    base = {
        "DASHSCOPE_API_KEY": "sk-test",
        "KNOWLEDGE_ASSISTANT_ENABLED": "true",
    }
    base.update(extra)
    return base


def test_load_omni_config_defaults():
    """默认走 Omni 模型与 Tina 音色。"""
    config = load_config(_env())
    assert config.mode == OMNI_MODE
    assert "omni" in config.model.lower()
    assert config.voice == "Tina"
    assert config.agent_name == "知识库助手"
    assert config.system_prompt


def test_rejects_livetranslate_model_name():
    """livetranslate 模型名不再受支持。"""
    with pytest.raises(RuntimeError, match="Omni"):
        load_config(
            _env(KNOWLEDGE_ASSISTANT_MODEL="qwen3.8-livetranslate-flash-realtime"),
        )


def test_rejects_non_omni_mode_env():
    """显式非 omni 模式直接拒绝。"""
    with pytest.raises(RuntimeError, match="omni"):
        load_config(_env(KNOWLEDGE_ASSISTANT_REALTIME_MODE="pipeline"))


def test_disabled_flag():
    with pytest.raises(RuntimeError, match="关闭"):
        load_config(_env(KNOWLEDGE_ASSISTANT_ENABLED="false"))


def test_missing_api_key():
    with pytest.raises(RuntimeError, match="DASHSCOPE_API_KEY"):
        load_config({"KNOWLEDGE_ASSISTANT_ENABLED": "true"})


def test_status_ready_shape():
    payload = build_runtime_status(_env())
    assert payload["mode"] == OMNI_MODE
    assert payload["enabled"] is True
    assert "pipeline_llm_model" not in payload
    assert "translation_language" not in payload
    assert "model" in payload
    assert "voice" in payload
