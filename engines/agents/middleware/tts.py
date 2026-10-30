"""
文件名: ➡️ tts.py 🏁
路径: ➡️ engines/agents/middleware/tts.py 🏁
模块功能：➡️ 按环境变量装配语音合成中间件 🏁
Python 调试：➡️ python -m engines.agents.middleware.tts 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. build_tts_middleware: 按环境变量装配「文本转语音」中间件。
🏁
关联模块：➡️
1. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from __future__ import annotations

import os

from agentscope.middleware import TTSMiddleware

from utils.logs import agent_event_log

from .envs import env_flag

TTS_ENABLED_ENV = "AGENT_TTS_MIDDLEWARE"
"""是否启用语音合成中间件；默认关闭。"""

TTS_MODEL_ENV = "AGENT_TTS_MODEL"
TTS_VOICE_ENV = "AGENT_TTS_VOICE"
API_KEY_ENV = "DASHSCOPE_API_KEY"

DEFAULT_MODEL = "qwen3-tts-flash"
DEFAULT_VOICE = "Cherry"


def build_tts_middleware() -> TTSMiddleware | None:
    """按环境变量装配语音合成中间件。

    只在显式开启且配置了 DashScope 密钥时装配；没有密钥只记一条警告，
    文本回复不受影响。

    Returns:
        语音中间件；未开启或缺密钥时返回 None。

    Raises:
        ValueError: 语音模型参数非法（由框架构造时抛出）。
    """
    if not env_flag(TTS_ENABLED_ENV):
        return None
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        agent_event_log.warning("AGENT_TTS_MIDDLEWARE 已开启，但缺少 DASHSCOPE_API_KEY，已跳过")
        return None
    try:
        from agentscope.credential import DashScopeCredential
        from agentscope.tts import DashScopeTTSModel
    except ImportError as exc:
        agent_event_log.warning("缺少 TTS 依赖，语音中间件未启用：%s", exc)
        return None
    model = DashScopeTTSModel(
        credential=DashScopeCredential(api_key=api_key),
        model=os.environ.get(TTS_MODEL_ENV, "").strip() or DEFAULT_MODEL,
        parameters=DashScopeTTSModel.Parameters(
            voice=os.environ.get(TTS_VOICE_ENV, "").strip() or DEFAULT_VOICE
        ),
        stream=True,
    )
    return TTSMiddleware(model)
