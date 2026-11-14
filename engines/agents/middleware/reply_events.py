"""
文件名: ➡️ reply_events.py 🏁
路径: ➡️ engines/agents/middleware/reply_events.py 🏁
模块功能：➡️ 单智能体回复事件观察：折叠后交给接收方，并继续向外产出 🏁
Python 调试：➡️ python -m engines.agents.middleware.reply_events 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. ReplyEventsMiddleware: 观察一次 reply 的事件流，交给 AgentEventsShow 后原样向外产出。
2. 只由单智能体编排显式挂入，不进默认装配，避免 SOP 双写。
🏁
关联模块：➡️
1. engines.agents.messaging.messages: 导入 AgentEventsShow，折叠并交给接收方
🏁
测试：➡️
1. tests/engines/agents/unit/test_single_agent_workflow.py: 假事件经过后接收方收到记录，调用方仍能迭代到原事件
🏁
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from typing import Any

from agentscope.middleware import MiddlewareBase

from engines.agents.messaging.messages import AgentEventsShow


class ReplyEventsMiddleware(MiddlewareBase):
    """
    观察一个智能体的一次回复，并把事件交给现有接收方。

    Attributes:
        无。累积器按一次 reply 新建，不跨回复共享。
    """

    async def on_reply(
        self,
        agent: Any,
        input_kwargs: dict,
        next_handler: Callable[..., AsyncGenerator[Any, None]],
    ) -> AsyncGenerator[Any, None]:
        """
        转发一次回复的事件，并在转发前折叠给接收方。

        Args:
            agent: 正在回复的智能体，只取名字和模型名。
            input_kwargs: 框架传给下一层的回复参数。
            next_handler: 内层回复生成器。

        Returns:
            原样向外的事件流。

        Raises:
            RuntimeError: 运行预算超限时由 AgentEventsShow 抛出。
        """
        buf: dict = {}
        model_name = str(getattr(getattr(agent, "model", None), "model", "") or "")
        models = {str(getattr(agent, "name", "") or ""): model_name}
        async for event in next_handler(**input_kwargs):
            AgentEventsShow.show(event, buf, models)
            yield event
