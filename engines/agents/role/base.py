"""
python -m 调试路径: engines.agents.role.base

本模块的业务功能如下：
1. BaseRole: Agent 智能体基类, 主要有 智能体创建、运行、中断等功能。
2. AgentRoleConfig: 角色配置类，主要用于创建角色配置。
"""

from __future__ import annotations

import asyncio
import os

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.console import ConsoleRenderer
from agentscope.message import Msg, UserMsg
from agentscope.tool import Toolkit

from utils.logs import agent_event_log

from .config import ChatModelFactory, ModelConfig, RoleSpecConfig


class BaseRole:
    """
    角色基类：用模型配置和角色配置创建并运行一个智能体。
    """

    def __init__(self, config: ModelConfig, role_config: RoleSpecConfig) -> None:
        """
        创建角色基类：用模型配置与角色配置创建智能体。

        Args:
            config: 模型配置。
            role: 角色配置。

        Raises:
            ValueError: 不支持的模型提供商。

        """
        self.log = agent_event_log
        self.config = config
        self.role = role_config

        self.model = ChatModelFactory(
            config, stream=self.role.stream, vision=self.role.vision
        ).create()

        self.agent = Agent(
            name=self.role.name,
            system_prompt=self.role.system_prompt,
            model=self.model,
            react_config=self._react_config(),
            context_config=self._context_config(),
            toolkit=self.role.toolkit,
        )

        # self._reply_task: asyncio.Task[object] | None = None
        # self._loop: asyncio.AbstractEventLoop | None = None

    def _user_msg(self, content: str) -> Msg:

        return UserMsg(name="user", content=content)

    def user_reply(self, content: str) -> Msg:
        """等本轮结束，返回最终消息。不打印、不解析。

        Args:
            content: 本轮用户输入正文。

        Returns:
            本轮最终消息。

        Raises:
            RuntimeError: 在已经运行的事件循环内调用（`asyncio.run` 拒绝）。
        """
        return asyncio.run(self.agent.reply(self._user_msg(content)))

    def user_reply_stream(self, content: str) -> Msg:
        """同步上屏，结束后返回最终消息。

        Args:
            content: 本轮用户输入正文。

        Returns:
            本轮最终消息。

        Raises:
            RuntimeError: 在已经运行的事件循环内调用（`asyncio.run` 拒绝）。
            RuntimeError: 事件流没有给出最终消息。
        """
        return asyncio.run(self._print_reply(content))

    async def _print_reply(self, content: str) -> Msg:
        """逐事件打印到控制台。"""
        renderer = ConsoleRenderer()
        final: Msg | None = None
        stream = self.agent.reply_stream(self._user_msg(content), yield_final_msg=True)
        async for event in stream:
            if isinstance(event, Msg):
                final = event
                continue
            renderer.render(event)
        if final is None:
            raise RuntimeError("事件流没有给出最终消息")
        return final

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


class AgentRoleConfig:
    def __init__(
        self,
        provider: str,
        model_name: str,
        base_url: str,
        api_key: str,
        name: str,
        system_prompt: str,
        toolkit: Toolkit,
        vision: bool,
    ):

        self.log = agent_event_log
        self.provider = provider
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

        self.name = name
        self.system_prompt = system_prompt
        self.toolkit = toolkit
        self.vision = vision

    def load_config(self):

        return (
            ModelConfig(
                provider=self.provider,
                model_name=self.model_name,
                base_url=self.base_url,
                api_key=self.api_key,
            ),
            RoleSpecConfig(
                name=self.name,
                system_prompt=self.system_prompt,
                toolkit=self.toolkit,
                vision=self.vision,
            ),
        )

    def _load_api_key(self, provider: str):

        api_key = None

        if provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        elif provider == "dashscope":
            api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        else:
            raise ValueError(
                f" 当前不支持{provider}厂商模型配置；可选：deepseek、openai、dashscope"
            )

        if not api_key:
            raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY（不要把 key 写进源码）")

        return api_key
