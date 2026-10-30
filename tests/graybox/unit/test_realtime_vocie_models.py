"""Omni realtime 模型工厂单测：不联网。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from engines.agents.realtime_vocie.config import load_config, create_realtime_model


def _env(**extra: str) -> dict[str, str]:
    base = {
        "DASHSCOPE_API_KEY": "sk-test",
        "KNOWLEDGE_ASSISTANT_ENABLED": "true",
    }
    base.update(extra)
    return base


def test_omni_mode_builds_dashscope_realtime_model():
    """默认 omni 配置走 DashScopeRealtimeModel 工厂。"""
    config = load_config(_env())
    fake_model = MagicMock(name="DashScopeRealtimeModel")
    import engines.agents.realtime_vocie.config as cfg

    original = cfg._get_realtime
    cfg._get_realtime = None
    try:
        with patch("agentscope.credential.DashScopeCredential"):
            with patch(
                "agentscope.realtime.DashScopeRealtimeModel",
                return_value=fake_model,
            ) as ctor:
                model = create_realtime_model(config)
    finally:
        cfg._get_realtime = original
    assert model is fake_model
    ctor.assert_called_once()


def test_package_exports_omni_only():
    """包表面不再导出 livetranslate / pipeline。"""
    import engines.agents.realtime_vocie as pkg

    assert "RealtimeVoiceSession" in pkg.__all__
    assert "LiveTranslateRealtimeModel" not in pkg.__all__
    assert "PipelineVoiceSession" not in pkg.__all__
    # dir() 不触发 __getattr__ 懒加载 session（会牵涉缺 config.yaml 的 rag）
    assert "LiveTranslateRealtimeModel" not in dir(pkg)
    assert "PipelineVoiceSession" not in dir(pkg)
