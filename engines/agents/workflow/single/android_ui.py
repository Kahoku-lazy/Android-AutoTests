"""
文件名: ➡️ android_ui.py 🏁
路径: ➡️ engines/agents/workflow/single/android_ui.py 🏁
模块功能：➡️ Android UI 控制：一个执行角色对当前设备做一轮回复 🏁
Python 调试：➡️ python -m engines.agents.workflow.single.android_ui 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. AndroidUiSession: 一次连接内复用一个执行者，后续消息不新建。
2. open_session: 创建会话并挂上单智能体事件中间件。
3. 不调用 SOP，不创建验收角色。
🏁
关联模块：➡️
1. engines.agents.agent_builders: 导入 build_ui_executor，复用现有执行角色
2. 事件流由聊天助手默认装配，本模块不再另挂
🏁
测试：➡️
1. tests/engines/agents/unit/test_single_agent_workflow.py: 只建一个 Agent，同 session 复用，事件中间件只挂在这里
🏁
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from agentscope.message import UserMsg

from engines.agents.agent_builders import build_ui_executor
from engines.agents.event_log import write_line

from .event_tail import SESSION_MARK

__all__ = ["AndroidUiSession", "open_session"]


class AndroidUiSession:
    """
    一次 Android UI 控制对话。

    Attributes:
        serial: 当前设备序列号。换设备只改这个字段，不新建智能体。
        agent: 本次连接的唯一执行者。
        session_id: 前端本次对话的连接键，事件日志按它分段。
    """

    def __init__(self, serial: str, agent: Any, *, session_id: str = "") -> None:
        """
        绑定一台设备和一个已经建好的执行者。

        Args:
            serial: 设备序列号。
            agent: `build_ui_executor()` 的产物，且已挂事件中间件。
            session_id: 前端本次对话的连接键；空串表示不写分段标记。
        """
        self.serial = serial
        self.agent = agent
        self.session_id = session_id

    def _mark(self, stage: str) -> None:
        """
        在事件日志里写下会话分段标记，并带上本次使用的模型名。

        Args:
            stage: `开始` 或 `结束`。
        """
        if not self.session_id:
            return
        model = str(getattr(getattr(self.agent, "model", None), "model", "") or "-")
        write_line("", f"{SESSION_MARK} | {self.session_id} | {stage} | {model}")

    async def reply(self, message: str) -> AsyncIterator[Any]:
        """
        把一条用户消息交给同一个执行者。

        序列号每次重放，避免换设备后智能体还拿着旧设备。

        Args:
            message: 用户本轮输入。

        Returns:
            该执行者本轮的事件流。

        Raises:
            ValueError: 消息为空。
        """
        text = message.strip()
        if not text:
            raise ValueError("消息不能为空")
        content = f"当前设备序列号：{self.serial}\n{text}"
        self._mark("开始")
        try:
            async for event in self.agent.reply_stream(UserMsg(name="user", content=content)):
                yield event
        finally:
            self._mark("结束")


def open_session(serial: str, *, session_id: str = "") -> AndroidUiSession:
    """
    打开一次 Android UI 控制对话。

    Args:
        serial: 已选定的设备序列号。
        session_id: 前端本次对话的连接键。

    Returns:
        绑定一个执行者的会话。该执行者挂有事件中间件。

    Raises:
        ValueError: 序列号为空。
    """
    if not serial.strip():
        raise ValueError("需要先选择设备")
    agent = build_ui_executor(with_events=True)
    return AndroidUiSession(serial.strip(), agent, session_id=session_id)
