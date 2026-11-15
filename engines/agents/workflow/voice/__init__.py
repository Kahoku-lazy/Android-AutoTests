"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/workflow/voice/__init__.py 🏁
模块功能：➡️ 语音助手对外出口：会话、传输、就绪状态与转写桥 🏁
Python 调试：➡️ python -m engines.agents.workflow.voice 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. open_voice_session: 打开一次语音会话，智能体由助手创建出口提供。
2. build_runtime_status / load_config: 就绪状态与会话配置。
3. WebSocketAudioTransport: 浏览器音频传输，生命周期仍由调用方持有。
4. TranscriptBridge / VoiceLogSink: 文字会话复用的转写桥与日志协议。
🏁
关联模块：➡️
1. engines.agents.realtime_vocie: 内部实现，包外不得直接引用
2. engines.agents.assistant: 由内部会话调用 create_voice_agent，本出口不构造智能体
🏁
测试：➡️
1. tests/engines/agents/unit/test_voice_workflow_exit.py: 出口再导出、不直接构造语音智能体
2. tests/knowledge/unit/test_knowledge_assistant_config.py: 就绪状态与配置经本出口
🏁
"""

from __future__ import annotations

from engines.agents.realtime_vocie.config import (
    OMNI_MODE,
    RealtimeVoiceConfig,
    build_runtime_status,
    load_config,
)
from engines.agents.realtime_vocie.events import TranscriptBridge, VoiceLogSink
from engines.agents.realtime_vocie.session import RealtimeVoiceSession
from engines.agents.realtime_vocie.transport import WebSocketAudioTransport

__all__ = [
    "OMNI_MODE",
    "RealtimeVoiceConfig",
    "RealtimeVoiceSession",
    "TranscriptBridge",
    "VoiceLogSink",
    "WebSocketAudioTransport",
    "build_runtime_status",
    "load_config",
    "open_voice_session",
]


def open_voice_session(
    config: RealtimeVoiceConfig,
    transport: WebSocketAudioTransport,
    send_json,
    log: VoiceLogSink,
) -> RealtimeVoiceSession:
    """
    打开一次语音会话。

    传输由调用方创建和关闭。本函数只把已有传输交给会话，不关闭浏览器通道。

    Args:
        config: 已校验的语音会话配置。
        transport: 调用方持有的浏览器音频传输。
        send_json: 向浏览器发送 JSON 事件的协程。
        log: 对话日志写入方。

    Returns:
        尚未启动的语音会话。调用方再调用 run()。
    """
    return RealtimeVoiceSession(config, transport, send_json, log)
