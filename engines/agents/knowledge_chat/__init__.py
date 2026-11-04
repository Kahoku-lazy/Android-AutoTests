"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/knowledge_chat/__init__.py 🏁
模块功能：➡️ 知识库文字问答会话的包入口 🏁
Python 调试：➡️ python -m engines.agents.knowledge_chat 🏁
时间：➡️ 2026-11-04 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-04 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 对外只导出会话、配置与状态三个入口，子模块不对外。
🏁
关联模块：➡️
1. engines.agents.knowledge_chat.config: 导入 ChatConfig / load_chat_config / build_status
2. engines.agents.knowledge_chat.session: 导入 KnowledgeChatSession / build_chat_toolkit
🏁
测试：➡️
1. tests/graybox/unit/test_knowledge_chat_session.py: 经包入口使用会话
🏁
"""

from __future__ import annotations

from .config import (
    DEFAULT_AGENT_NAME,
    DEFAULT_MAX_TEXT_CHARS,
    ChatConfig,
    build_status,
    load_chat_config,
)
from .session import KnowledgeChatSession, build_chat_toolkit

__all__ = [
    "DEFAULT_AGENT_NAME",
    "DEFAULT_MAX_TEXT_CHARS",
    "ChatConfig",
    "KnowledgeChatSession",
    "build_chat_toolkit",
    "build_status",
    "load_chat_config",
]
