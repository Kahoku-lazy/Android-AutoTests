"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/workflow/single/__init__.py 🏁
模块功能：➡️ 单智能体编排包：清单与按连接复用的运行器 🏁
Python 调试：➡️ python -m engines.agents.workflow.single 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. list_single_agents / get_single_agent: 编排清单。
2. open_session: 打开 Android UI 控制。
3. session_for: 同一 session_id 复用同一个执行者。
🏁
关联模块：➡️
1. engines.agents.workflow.single.catalog: 导入清单
2. engines.agents.workflow.single.android_ui: 导入 open_session
🏁
测试：➡️
1. tests/engines/agents/unit/test_single_agent_workflow.py: 清单、复用与未知键
🏁
"""

from __future__ import annotations

from .android_ui import AndroidUiSession, open_session
from .catalog import SingleAgentCard, get_single_agent, list_single_agents
from .event_tail import SESSION_MARK, read_session_events

__all__ = [
    "AndroidUiSession",
    "SESSION_MARK",
    "SingleAgentCard",
    "get_single_agent",
    "list_single_agents",
    "open_session",
    "read_session_events",
    "session_for",
]

_SESSIONS: dict[str, AndroidUiSession] = {}


def session_for(session_id: str, serial: str, workflow_key: str = "") -> AndroidUiSession:
    """
    按连接取 Android UI 控制会话。没有则创建。

    Args:
        session_id: 前端本次对话的连接键。
        serial: 当前设备序列号。已有会话时只更新序列号。
        workflow_key: 编排键。未知键拒绝创建。

    Returns:
        该连接上的同一个会话。

    Raises:
        ValueError: 连接键或序列号为空。
        KeyError: 编排键不存在。
    """
    get_single_agent(workflow_key)
    key = session_id.strip()
    if not key:
        raise ValueError("session_id 不能为空")
    current = _SESSIONS.get(key)
    if current is None:
        current = open_session(serial, session_id=key)
        _SESSIONS[key] = current
        return current
    current.serial = serial.strip()
    return current
