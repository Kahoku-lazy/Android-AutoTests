"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/realtime_vocie/__init__.py 🏁
模块功能：➡️ 实时语音助手引擎包：Omni 实时模型配置、知识库提示词、事件桥、 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. （模块无公开类/函数，见源码）
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_realtime_vocie_models.py: Omni realtime 模型工厂单测：不联网
🏁
"""

from .config import (
    RealtimeVoiceConfig,
    build_runtime_status,
    create_realtime_model,
    load_config,
)
from .events import TranscriptBridge, VoiceLogSink
from .transport import WebSocketAudioTransport

__all__ = [
    "RealtimeVoiceConfig",
    "RealtimeVoiceSession",
    "TranscriptBridge",
    "VoiceLogSink",
    "WebSocketAudioTransport",
    "build_runtime_status",
    "create_realtime_model",
    "load_config",
]


def __getattr__(name: str):
    if name == "RealtimeVoiceSession":
        from .session import RealtimeVoiceSession

        return RealtimeVoiceSession
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
