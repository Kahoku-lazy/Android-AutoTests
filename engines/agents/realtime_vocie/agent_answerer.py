"""
python -m 调试路径: engines.agents.realtime_vocie.agent_answerer

本模块的业务功能如下：
1. AgentAnswerer: 用 Agent + 中间件生成语音回答，文本流式吐出、音频整段攒取。
"""

from __future__ import annotations

import base64

from collections.abc import AsyncIterator
from typing import Any

from agentscope.message import UserMsg


class AgentAnswerer:
    """
    用 Agent 取代 pipeline 里「直连 DeepSeek + 单独合成 TTS」的两段。

    文本按增量吐出，音频块在内部解码攒成一段 PCM，结束时整段取走——
    与前端现有的「一段音频」帧格式保持一致。

    Attributes:
        last_usage: 最近一轮的 token 用量，键与 `DeepSeekAnswerer` 一致。
    """

    def __init__(self, agent: Any) -> None:
        """
        包装一个已经装配好中间件的智能体。

        Args:
            agent: 具备 `reply_stream(inputs, yield_final_msg=True)` 的智能体。
        """
        self._agent = agent
        self._audio_parts: list[bytes] = []
        self.last_usage: dict[str, int] = {}

    async def stream(self, text: str) -> AsyncIterator[str]:
        """
        流式生成一轮回答。

        Args:
            text: 用户源语转写。

        Yields:
            本次回答的文本增量；音频不在这里吐，结束后用 `take_audio` 取。
        """
        self._audio_parts = []
        self.last_usage = {}
        stream = self._agent.reply_stream(
            UserMsg(name="user", content=text),
            yield_final_msg=True,
        )
        async for event in stream:
            kind = type(event).__name__
            if kind == "TextBlockDeltaEvent":
                delta = str(getattr(event, "delta", "") or "")
                if delta:
                    yield delta
            elif kind == "DataBlockDeltaEvent":
                self._append_audio(getattr(event, "data", ""))
            elif kind == "ModelCallEndEvent":
                self.last_usage = {
                    "input_tokens": int(getattr(event, "input_tokens", 0) or 0),
                    "output_tokens": int(getattr(event, "output_tokens", 0) or 0),
                    "cache_input_tokens": int(getattr(event, "cache_input_tokens", 0) or 0),
                    "cache_creation_input_tokens": int(
                        getattr(event, "cache_creation_input_tokens", 0) or 0
                    ),
                }

    def _append_audio(self, data: object) -> None:
        """解码一段增量 base64 PCM 并攒起来；空块或坏块跳过。

        Args:
            data: `DataBlockDeltaEvent.data` 的 base64 片段。
        """
        raw = str(data or "").strip()
        if not raw:
            return
        try:
            self._audio_parts.append(base64.b64decode(raw))
        except ValueError:
            return

    def take_audio(self) -> bytes:
        """取走本轮攒下的 PCM16 音频，并清空缓冲。

        Returns:
            本轮整段音频；没有音频时为空字节。
        """
        pcm = b"".join(self._audio_parts)
        self._audio_parts = []
        return pcm
