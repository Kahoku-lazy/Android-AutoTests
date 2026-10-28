"""
python -m 调试路径: engines.agents.realtime_vocie.tts_model

本模块的业务功能如下：
1. LocalTtsModel: 把 pipeline 现有的 Sambert / Qwen TTS 适配成 AgentScope 的 TTS 模型。
"""

from __future__ import annotations

import base64

from typing import Any

from agentscope.credential import DashScopeCredential
from agentscope.message import Base64Source, DataBlock
from agentscope.tts import TTSModelBase, TTSResponse

DEFAULT_SAMPLE_RATE = 24000


class LocalTtsModel(TTSModelBase):
    """
    整段式 TTS 适配器：保留现有音色与 provider，只换一层框架接口。

    非实时模式：`TTSMiddleware` 在每段文本结束时调一次 `synthesize`，
    拿到一块完整 PCM，再以 data block 事件吐回事件流。

    Attributes:
        sample_rate: 输出 PCM 采样率。
    """

    def __init__(
        self,
        engine: Any,
        *,
        model: str,
        api_key: str,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> None:
        """
        包装一个已有的 TTS 引擎。

        Args:
            engine: 具备 `synthesize(text) -> bytes` 的引擎（SambertTts / QwenTts）。
            model: 模型名，写进模型卡片与日志。
            api_key: DashScope 密钥，交给框架的凭证对象。
            sample_rate: 引擎没有 `sample_rate` 属性时使用的采样率。
        """
        super().__init__(
            credential=DashScopeCredential(api_key=api_key),
            model=model,
            stream=False,
        )
        self._engine = engine
        self.sample_rate = int(getattr(engine, "sample_rate", sample_rate))

    @property
    def media_type(self) -> str:
        """音频块的 media type；采样率随引擎实际输出。"""
        return f"audio/pcm;rate={self.sample_rate}"

    async def synthesize(
        self,
        text: str | None = None,
        **kwargs: Any,
    ) -> TTSResponse:
        """把一段文本合成成一块 PCM 音频。

        Args:
            text: 要合成的文本。
            **kwargs: 框架透传的额外参数，本适配器不用。

        Returns:
            含一块 PCM 音频的响应；没有音频时 `content` 为 None。

        Raises:
            RuntimeError: 底层引擎合成失败（由引擎自己抛出）。
        """
        pcm = await self._engine.synthesize(text or "")
        if not pcm:
            return TTSResponse(content=None)
        block = DataBlock(
            source=Base64Source(
                data=base64.b64encode(pcm).decode("ascii"),
                media_type=self.media_type,
            ),
        )
        return TTSResponse(content=block)
