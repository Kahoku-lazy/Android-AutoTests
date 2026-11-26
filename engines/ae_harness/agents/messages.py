from __future__ import annotations

from agentscope.message import UserMsg

__all__ = ["user_message"]


def user_message(content: str) -> UserMsg:
    return UserMsg(name="user", content=content)
