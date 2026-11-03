"""
文件名: ➡️ tts.py 🏁
路径: ➡️ engines/agents/middleware/tts.py 🏁
模块功能：➡️ 按环境变量装配语音合成中间件 🏁
Python 调试：➡️ python -m engines.agents.middleware.tts 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. build_tts_middleware: 按开关装配「文本转语音」中间件；缺密钥或缺依赖只警告并跳过
2. 模型实例由 engines.agents.models 门面创建，本模块只管开关与降级
🏁
关联模块：➡️
1. engines.agents.models: 导入 get_tts_model，取语音合成模型实例
2. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/graybox/unit/test_agent_middleware_assembly.py: 语音中间件按开关装配
🏁
"""

from __future__ import annotations

import os

from agentscope.middleware import TTSMiddleware

from engines.agents.models import get_tts_model
from utils.logs import agent_event_log

from .envs import env_flag

TTS_ENABLED_ENV = "AGENT_TTS_MIDDLEWARE"
"""是否启用语音合成中间件；默认关闭。"""

API_KEY_ENV = "DASHSCOPE_API_KEY"


def build_tts_middleware() -> TTSMiddleware | None:
    """按环境变量装配语音合成中间件。

    只在显式开启且配置了 DashScope 密钥时装配；没有密钥或缺少 TTS 依赖时
    只记一条警告，文本回复不受影响。

    Returns:
        语音中间件；未开启、缺密钥或缺依赖时返回 None。

    Raises:
        ValueError: 语音模型参数非法（由框架构造时抛出）。
    """
    if not env_flag(TTS_ENABLED_ENV):
        return None
    if not os.environ.get(API_KEY_ENV, "").strip():
        agent_event_log.warning("AGENT_TTS_MIDDLEWARE 已开启，但缺少 DASHSCOPE_API_KEY，已跳过")
        return None
    try:
        model = get_tts_model()
    except RuntimeError as exc:
        agent_event_log.warning("缺少 TTS 依赖，语音中间件未启用：%s", exc)
        return None
    return TTSMiddleware(model)
