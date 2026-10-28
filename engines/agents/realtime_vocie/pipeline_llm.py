"""
python -m 调试路径: engines.agents.realtime_vocie.pipeline_llm

本模块的业务功能如下：
1. DeepSeekAnswerer: 用 DeepSeek Flash 流式回答语音转写文本，并维护最近多轮上下文。

Pipeline 路线只把 ASR 的源语文本送到这里；不注入平台知识、不做关键词匹配。
启用 RAG 时，本轮检索资料会作为上下文注入，但不会写进长期历史。
"""

from __future__ import annotations

import inspect
import os

from collections.abc import AsyncIterator

from agentscope.credential import DeepSeekCredential
from agentscope.message import Msg, TextBlock
from agentscope.model import DeepSeekChatModel

from engines.agents.config.models import DeepSeekModelConfig
from engines.agents.rag.service import RagService


class DeepSeekAnswerer:
    """
    DeepSeek Flash 流式回答器。

    Attributes:
        model_name: DeepSeek 模型名，默认 deepseek-flash。
        history: 最近多轮消息，固定在 max_history_turns 轮以内。
    """

    def __init__(
        self,
        system_prompt: str,
        model_name: str = DeepSeekModelConfig.FLASH,
        base_url: str = DeepSeekModelConfig.base_url,
        max_history_turns: int = 6,
        rag: RagService | None = None,
    ) -> None:
        """
        初始化 DeepSeek 回答器。

        Args:
            system_prompt: 直接对话系统提示词。
            model_name: DeepSeek 模型名。
            base_url: DeepSeek OpenAI 兼容地址。
            max_history_turns: 保留的最大历史轮数。
            rag: 可选的 RAG 服务；有命中时注入检索资料。

        Raises:
            RuntimeError: 缺少 DEEPSEEK_API_KEY。
        """
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY，无法使用 DeepSeek 回答")
        self.model_name = model_name
        self.max_history_turns = max(1, max_history_turns)
        self.rag = rag
        self.last_usage: dict[str, int] = {}
        if rag is not None and rag.enabled:
            system_prompt = (
                f"{system_prompt}\n"
                "如果本轮提供了【检索资料】，请优先依据资料回答；"
                "资料没有覆盖的内容不要编造。"
            )
        self._model = DeepSeekChatModel(
            credential=DeepSeekCredential(api_key=api_key, base_url=base_url),
            model=model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=False),
            stream=True,
        )
        self.history: list[Msg] = [
            Msg(
                name="system",
                content=[TextBlock(text=system_prompt)],
                role="system",
            ),
        ]

    async def stream(self, text: str) -> AsyncIterator[str]:
        """
        流式生成一轮回答。

        Args:
            text: 用户源语转写。

        Yields:
            本次回答的文本增量。

        Raises:
            RuntimeError: DeepSeek 调用失败。
        """
        self.last_usage = {}
        context = ""
        if self.rag is not None and self.rag.enabled:
            context = await self.rag.build_context(text)
        user_text = f"{context}\n\n用户问题：{text}" if context else text
        user = Msg(name="user", content=[TextBlock(text=user_text)], role="user")
        messages = [*self.history, user]
        try:
            response = await self._model(messages)
            full = ""
            if inspect.isasyncgen(response):
                async for chunk in response:
                    self._capture_usage(chunk.usage)
                    piece = "".join(
                        block.text for block in chunk.content if isinstance(block, TextBlock)
                    )
                    delta = self._delta(full, piece)
                    full = self._merge(full, piece)
                    if delta:
                        yield delta
            else:
                self._capture_usage(response.usage)
                full = "".join(
                    block.text for block in response.content if isinstance(block, TextBlock)
                )
                if full:
                    yield full
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"DeepSeek 回答失败：{exc}") from exc

        if not full:
            return
        self.history.extend(
            [
                user,
                Msg(
                    name="assistant",
                    content=[TextBlock(text=full)],
                    role="assistant",
                ),
            ],
        )
        self._trim_history()

    def _capture_usage(self, usage: object) -> None:
        """保存 DeepSeek 返回的 token 用量；没有 usage 时保持空。"""
        if usage is None:
            return
        self.last_usage = {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            "cache_input_tokens": int(
                getattr(usage, "cache_input_tokens", 0) or 0,
            ),
            "cache_creation_input_tokens": int(
                getattr(usage, "cache_creation_input_tokens", 0) or 0,
            ),
        }

    @staticmethod
    def _merge(accumulated: str, piece: str) -> str:
        """兼容“累计文本”与“增量文本”两种流式返回。"""
        if not accumulated:
            return piece
        if piece.startswith(accumulated):
            return piece
        if accumulated.endswith(piece):
            return accumulated
        return accumulated + piece

    @staticmethod
    def _delta(accumulated: str, piece: str) -> str:
        """算出本帧新增文本。"""
        if not accumulated:
            return piece
        if piece.startswith(accumulated):
            return piece[len(accumulated) :]
        if accumulated.endswith(piece):
            return ""
        return piece

    def _trim_history(self) -> None:
        """只保留 system 与最近 max_history_turns 轮。"""
        keep = 1 + self.max_history_turns * 2
        if len(self.history) > keep:
            self.history = [self.history[0], *self.history[-(keep - 1) :]]
