"""
文件名: ➡️ knowledge.py 🏁
路径: ➡️ engines/agents/realtime_vocie/knowledge.py 🏁
模块功能：➡️ 语音助手系统提示词：实现已迁至 engines.agents.role_sys_prompts.VoiceKnowled 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie.knowledge 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. （模块无公开类/函数，见源码）
🏁
关联模块：➡️
1. engines.agents.role_sys_prompts: 导入 SYSTEM_PROMPT, VoiceKnowledgePrompts, build_system_prompt
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from __future__ import annotations

from engines.agents.role_sys_prompts import (
    SYSTEM_PROMPT,
    VoiceKnowledgePrompts,
    build_system_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "VoiceKnowledgePrompts",
    "build_system_prompt",
]
