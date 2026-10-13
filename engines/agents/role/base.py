"""
python -m 调试路径: engines.agents.role.base

本模块的业务功能如下：
1. BaseRole: 角色基类, 主要功能有智能体创建、运行智能体与智能体中断功能。
"""

from __future__ import annotations

import asyncio

from contextlib import asynccontextmanager

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.event import UserInterruptEvent
from agentscope.message import Msg, UserMsg

from ..messaging.messages import render_reply_stream
from .config import ChatModelFactory, ModelConfig, RoleSpecConfig


class BaseRole:
    """用模型配置和角色配置创建并运行一个智能体。

    既定异常：构造时模型提供商不在支持集合内会抛 `ValueError`；
    `reply` / `reply_stream` / `interrupt` 在未 `start()` 或
    在运行中的事件循环内调用时会抛 `RuntimeError`。
    """

    def __init__(self, config: ModelConfig, role: RoleSpecConfig) -> None:
        """
        创建角色基类：用模型配置与角色配置创建智能体。

        Args:
            config: 模型配置。
            role: 角色配置。

        Raises:
            ValueError: 不支持的模型提供商。

        """
        self.config = config
        self.role = role
        self.model = ChatModelFactory(config, stream=role.stream, vision=role.vision).create()
        self.agent: Agent | None = None
        self._reply_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        """用角色配置里的名称、提示词、工具包、ReAct 与上下文创建智能体。

        Returns:
            None。
        """
        self.agent = Agent(
            name=self.role.name,
            system_prompt=self.role.system_prompt,
            model=self.model,
            react_config=self._react_config(),
            context_config=self._context_config(),
            toolkit=self.role.toolkit,
        )

    def reply(self, content: str):
        """等这一轮结束，返回消息，不做实时上屏。

        Args:
            content: 本轮用户输入正文。

        Returns:
            本轮的最终消息。

        Raises:
            RuntimeError: 未调用 `start()`（经 `_require_agent` 抛出）。
            RuntimeError: 在运行中的事件循环内调用（`asyncio.run` 拒绝）。
        """
        return asyncio.run(self._reply(content))

    def interrupt(self) -> None:
        """运行中取消当前回复；已暂停则结束等待中的工具确认。

        Raises:
            RuntimeError: 未调用 `start()`（经 `_interrupt_paused` → `_require_agent` 抛出）。
            RuntimeError: 没有运行中的回复时在事件循环内调用（`asyncio.run` 拒绝）。
        """
        task = self._reply_task
        loop = self._loop
        if task is not None and loop is not None and loop.is_running() and not task.done():
            loop.call_soon_threadsafe(task.cancel)
            return
        asyncio.run(self._interrupt_paused())

    def reply_stream(self, content: str):
        """实时打印思考、工具调用、工具结果和文本，并返回最后一条消息。

        Args:
            content: 本轮用户输入正文。

        Returns:
            事件流末端的最终消息。

        Raises:
            RuntimeError: 未调用 `start()`（经 `_require_agent` 抛出）。
            RuntimeError: 在运行中的事件循环内调用（`asyncio.run` 拒绝）。
        """
        return asyncio.run(self._reply_stream(content))

    @asynccontextmanager
    async def _running(self):
        """记下当前回复任务，供 interrupt 取消。"""
        self._loop = asyncio.get_running_loop()
        self._reply_task = asyncio.current_task()
        try:
            yield
        finally:
            self._reply_task = None
            self._loop = None

    async def _reply(self, content: str):
        async with self._running():
            return await self._require_agent().reply(self._user_msg(content))

    async def _interrupt_paused(self) -> None:
        """对暂停中的回复发送 UserInterruptEvent。未在等待时由框架空返回。"""
        agent = self._require_agent()
        event = UserInterruptEvent(reply_id=agent.state.reply_id)
        async for _event in agent.reply_stream(event):
            pass

    def _require_agent(self) -> Agent:
        """取出 `start()` 创建的智能体。

        Returns:
            已创建的智能体。

        Raises:
            RuntimeError: 尚未调用 `start()`。
        """
        if self.agent is None:
            raise RuntimeError("请先调用 start()")
        return self.agent

    def _react_config(self) -> ReActConfig:
        return ReActConfig(
            max_iters=self.role.max_iters,
            structured_output_grace_iters=self.role.structured_output_grace_iters,
            stop_on_reject=self.role.stop_on_reject,
        )

    def _context_config(self) -> ContextConfig:
        return ContextConfig(
            trigger_ratio=self.role.trigger_ratio,
            reserve_ratio=self.role.reserve_ratio,
            tool_result_limit=self.role.tool_result_limit,
            max_image_num=self.role.max_image_num,
        )

    def _user_msg(self, content: str) -> Msg:
        return UserMsg(name="user", content=content)

    async def _reply_stream(self, content: str):
        """驱动一次流式回复：上屏交给 messaging 层，本方法只管任务登记。"""
        async with self._running():
            return await render_reply_stream(self._require_agent(), self._user_msg(content))
