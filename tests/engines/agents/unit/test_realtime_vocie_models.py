"""Omni 会话取模型单测：不联网，不保留第二套构造。"""

from __future__ import annotations

from engines.agents.realtime_vocie.config import load_config


def _env(**extra: str) -> dict[str, str]:
    base = {
        "DASHSCOPE_API_KEY": "sk-test",
        "KNOWLEDGE_ASSISTANT_ENABLED": "true",
    }
    base.update(extra)
    return base


def test_omni_config_uses_catalog_model_name():
    """默认 omni 配置的模型名来自只读视图，不在本模块构造模型。"""
    config = load_config(_env())

    assert config.model == "qwen3.5-omni-plus-realtime"
    assert not hasattr(load_config, "create_realtime_model")


def test_package_exports_omni_only():
    """包表面不再导出模型工厂、livetranslate 或 pipeline。"""
    import engines.agents.realtime_vocie as pkg
    import engines.agents.realtime_vocie.config as config

    assert "RealtimeVoiceSession" in pkg.__all__
    assert "create_realtime_model" not in pkg.__all__
    assert not hasattr(config, "create_realtime_model")
    assert "LiveTranslateRealtimeModel" not in pkg.__all__
    assert "PipelineVoiceSession" not in pkg.__all__
    assert "LiveTranslateRealtimeModel" not in dir(pkg)
    assert "PipelineVoiceSession" not in dir(pkg)
