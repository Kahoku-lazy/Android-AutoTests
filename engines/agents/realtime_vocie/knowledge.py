"""
python -m 调试路径: engines.agents.realtime_vocie.knowledge

本模块的业务功能如下：
1. SYSTEM_PROMPT: 参考 realtime_voice_demo 的简短中文语音助手提示词。
2. build_system_prompt(): 返回该提示词，供实时语音会话直接使用。

这里不注入平台知识速览、固定答案或关键词匹配话术；助手回复完全由
实时模型根据用户语音与通用对话提示生成。
"""

from __future__ import annotations

from typing import Final

SYSTEM_PROMPT: Final[str] = (
    "你是一个中文语音助手，正在通过语音和用户直接对话。回答尽量简短、口语化，通常不超过三句话。"
)


def build_system_prompt() -> str:
    """
    返回实时语音助手的直接对话系统提示词。

    Returns:
        简短中文语音助手提示词。
    """
    return SYSTEM_PROMPT
