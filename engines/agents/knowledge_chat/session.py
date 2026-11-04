"""
文件名: ➡️ session.py 🏁
路径: ➡️ engines/agents/knowledge_chat/session.py 🏁
模块功能：➡️ 文字问答会话：回显用户消息、流式下发助手回答并落日志 🏁
Python 调试：➡️ python -m engines.agents.knowledge_chat.session 🏁
时间：➡️ 2026-11-04 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-04 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. KnowledgeChatSession: 一条连接内的文字问答会话，多轮历史留在 Agent 实例里。
2. answer(): 先回显用户消息，再把 Agent 事件翻成既有线格式流式下发。
3. build_chat_toolkit(): 按 RAG 是否启用装配 search_knowledge 工具包。
🏁
关联模块：➡️
1. engines.agents.agent_builders: 导入 build_knowledge_chat，按角色键装配 Agent
2. engines.agents.rag.service: 导入 RagService，本地知识检索
3. engines.agents.rag.tool: 导入 build_rag_tool，Omni 与文字共用同一工具
4. engines.agents.realtime_vocie.events: 导入 TranscriptBridge，复用线格式与日志
🏁
测试：➡️
1. tests/graybox/unit/test_knowledge_chat_session.py: 回显、流式回答、用量记账：不联网
🏁
"""

from __future__ import annotations

import uuid

from collections.abc import Awaitable, Callable
from typing import Final

from agentscope.message import UserMsg
from agentscope.tool import Toolkit

from engines.agents.agent_builders import build_knowledge_chat
from engines.agents.rag.service import RagService
from engines.agents.rag.tool import build_rag_tool
from engines.agents.realtime_vocie.events import TranscriptBridge, VoiceLogSink

from .config import ChatConfig, load_chat_config

SendJson = Callable[[dict], Awaitable[None]]

PROVIDER: Final[str] = "deepseek"
CATEGORY: Final[str] = "LLM"


def build_chat_toolkit(rag: RagService) -> Toolkit | None:
    """
    按 RAG 是否启用装配文字会话的工具包。

    Args:
        rag: 已配置的 RAG 服务。

    Returns:
        含 `search_knowledge` 的工具包；RAG 未启用时返回 None。
    """
    if not rag.enabled:
        return None
    return Toolkit(tools=[build_rag_tool(rag)])


class KnowledgeChatSession:
    """
    一条连接内的文字问答会话。

    Attributes:
        send_json: 向浏览器下发事件的协程。
        log: 对话日志写入方。
        config: 模型名与文本长度上限。
    """

    def __init__(
        self,
        send_json: SendJson,
        log: VoiceLogSink,
        *,
        config: ChatConfig | None = None,
        agent: object | None = None,
    ) -> None:
        """
        初始化会话；Agent 惰性创建，首次回答前才需要模型密钥。

        Args:
            send_json: 向浏览器下发事件的协程。
            log: 对话日志写入方（message / event / display_path）。
            config: 已校验的配置；None 时按环境变量读取。
            agent: 测试注入的 Agent；None 时首次回答前创建。
        """
        self.send_json = send_json
        self.log = log
        self.config = config or load_chat_config()
        self._agent = agent
        # 本次连接累计的 token，供接入层写 session_end
        self.usage_input = 0
        self.usage_output = 0

    @property
    def model(self) -> str:
        """当前回答模型名。"""
        return self.config.model

    async def answer(self, text: str) -> None:
        """
        处理一条用户文字：回显、流式回答、落日志。

        Args:
            text: 用户输入；空白内容直接忽略。

        Raises:
            Exception: 模型调用或 Agent 装配失败时向上抛，由接入层转成可读提示。
        """
        content = text.strip()
        if not content:
            return
        reply_id = f"text-{uuid.uuid4().hex[:12]}"
        await self.send_json(
            {"type": "reply_start", "reply_id": reply_id, "role": "user", "name": "user"},
        )
        await self.send_json(
            {
                "type": "transcript_final",
                "reply_id": reply_id,
                "role": "user",
                "text": content,
            },
        )
        self.log.message("user", content, reply_id)

        bridge = TranscriptBridge(
            self.log,
            model=self.model,
            provider=PROVIDER,
            category=CATEGORY,
        )
        try:
            async for event in self._ensure_agent().reply_stream(
                inputs=UserMsg(name="user", content=content),
            ):
                for payload in bridge.handle(event):
                    await self.send_json(payload)
        finally:
            # 用户中途结束或通道断开时补落已显示的文本，避免「看到了但日志没有」
            bridge.flush()
            self.usage_input += bridge.usage_input
            self.usage_output += bridge.usage_output

    def _ensure_agent(self):
        """取得 Agent；首次调用时按 RAG 启用情况装配工具包。"""
        if self._agent is None:
            rag = RagService.from_env()
            self._agent = build_knowledge_chat(toolkit=build_chat_toolkit(rag))
        return self._agent


__all__ = ["KnowledgeChatSession", "build_chat_toolkit"]
