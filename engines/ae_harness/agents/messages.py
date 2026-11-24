"""
文件名: ➡️ messages.py 🏁
路径: ➡️ engines/ae_harness/agents/messages.py 🏁
模块功能：➡️ 构造一轮发给智能体的用户消息 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.messages 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. user_message: 把一段正文包成名字固定为 user 的用户消息。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 agentscope 的消息类型。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from agentscope.message import UserMsg

__all__ = ["user_message"]


def user_message(content: str) -> UserMsg:
    """
    构造一条用户消息。

    Args:
        content: 发给智能体的正文。

    Returns:
        名字固定为 user 的用户消息。
    """
    return UserMsg(name="user", content=content)
