"""
文件名: ➡️ tts_model.py 🏁
路径: ➡️ engines/agents/models/tts_model.py 🏁
模块功能：➡️ 语音合成模型：唯一的构造实现，按环境变量取模型名与音色 🏁
Python 调试：➡️ python -m engines.agents.models.tts_model 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. build_tts_model: 造 DashScope 语音合成模型（stream=True），模型名与音色可由环境变量覆盖
2. DEFAULT_MODEL / DEFAULT_VOICE: 未配置时的默认值
3. 开关与降级留在中间件：本模块只负责「能造出来就造」，不决定是否启用
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_agent_middleware_assembly.py: 语音中间件按开关装配
🏁
"""

from __future__ import annotations

import os

__all__ = ["DEFAULT_MODEL", "DEFAULT_VOICE", "build_tts_model"]

DEFAULT_MODEL = "qwen3-tts-flash"
DEFAULT_VOICE = "Cherry"

TTS_MODEL_ENV = "AGENT_TTS_MODEL"
TTS_VOICE_ENV = "AGENT_TTS_VOICE"
API_KEY_ENV = "DASHSCOPE_API_KEY"


def build_tts_model(
    *,
    api_key: str | None = None,
    model_name: str | None = None,
    voice: str | None = None,
):
    """造一个 DashScope 语音合成模型。

    Args:
        api_key: 密钥；None 时读 `DASHSCOPE_API_KEY`。
        model_name: 模型名；None 时读 `AGENT_TTS_MODEL`，仍为空用默认值。
        voice: 音色；None 时读 `AGENT_TTS_VOICE`，仍为空用默认值。

    Returns:
        `DashScopeTTSModel` 实例（stream=True）。

    Raises:
        RuntimeError: 缺少 TTS 依赖，或缺 `DASHSCOPE_API_KEY`。
    """
    try:
        from agentscope.credential import DashScopeCredential
        from agentscope.tts import DashScopeTTSModel
    except ImportError as exc:
        raise RuntimeError(f"缺少 TTS 依赖：{exc}") from exc
    key = (api_key or os.environ.get(API_KEY_ENV, "")).strip()
    if not key:
        raise RuntimeError(f"缺少 {API_KEY_ENV}，无法创建语音合成模型")
    resolved_model = model_name or os.environ.get(TTS_MODEL_ENV, "").strip() or DEFAULT_MODEL
    resolved_voice = voice or os.environ.get(TTS_VOICE_ENV, "").strip() or DEFAULT_VOICE
    return DashScopeTTSModel(
        credential=DashScopeCredential(api_key=key),
        model=resolved_model,
        parameters=DashScopeTTSModel.Parameters(voice=resolved_voice),
        stream=True,
    )
