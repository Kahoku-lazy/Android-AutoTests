"""
python -m 调试路径: engines.agents.realtime_vocie.livetranslate

本模块的业务功能如下：
1. LiveTranslateRealtimeModel.Parameters: 实时翻译模型的音色、目标语种与输出模态。
2. LiveTranslateRealtimeModel: DashScope 实时翻译模型的 RealtimeModelBase 适配器。
3. _parse(): 把 qwen3.8-livetranslate 的服务端事件翻译成 AgentScope 模型事件。

实时翻译协议与 Omni 实时对话不同：使用 session.output_modalities、
session.translation.language 与 speaker_detection；译文走
response.audio_transcript.delta / response.text.delta，音频走
response.audio.delta；结束前需发送 session.finish。
"""

from __future__ import annotations

import asyncio
import base64

from typing import Any

from agentscope.credential import DashScopeCredential
from agentscope.realtime import _events as me
from agentscope.realtime._base import RealtimeModelBase
from agentscope.realtime._dashscope._model import DashScopeRealtimeModel
from agentscope.realtime._model_card import RealtimeModelCard
from pydantic import Field

LIVETRANSLATE_MODEL = "qwen3.8-livetranslate-flash-realtime"
# 实时翻译模型走百炼标准 Realtime WebSocket 地址（当前 API Key 可直接访问）。
LIVETRANSLATE_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
LIVETRANSLATE_CARD = RealtimeModelCard(
    name=LIVETRANSLATE_MODEL,
    label="Qwen3.8-LiveTranslate-Flash Realtime",
    input_sample_rate=16000,
    output_sample_rate=24000,
    supports_tools=False,
    input_types=["audio/pcm"],
    output_types=["audio/pcm", "text/plain"],
)


class LiveTranslateRealtimeModel(DashScopeRealtimeModel):
    """DashScope 实时翻译模型适配器。"""

    class Parameters(RealtimeModelBase.Parameters):
        """实时翻译模型的会话参数。"""

        voice: str = Field(default="Tina", title="Voice")
        translation_language: str = Field(
            default="zh",
            title="Target Language",
            description="目标语种代码，例如 zh / en / ja。",
        )
        output_modalities: list[str] = Field(
            default_factory=lambda: ["text", "audio"],
            title="Output Modalities",
        )

    type = "dashscope_livetranslate_realtime"
    supports_text_input = False

    def __init__(
        self,
        model: str,
        credential: DashScopeCredential,
        parameters: "LiveTranslateRealtimeModel.Parameters | None" = None,
    ) -> None:
        """
        初始化实时翻译模型。

        Args:
            model: 模型名，默认使用 qwen3.8-livetranslate-flash-realtime。
            credential: DashScope 凭证。
            parameters: 音色、目标语种与输出模态。
        """
        super().__init__(
            model,
            credential,
            parameters or self.Parameters(),
            model_card=LIVETRANSLATE_CARD,
        )
        self.parameters: LiveTranslateRealtimeModel.Parameters
        self._session_ready = asyncio.Event()
        self._connect_error = ""

    async def connect(
        self,
        instructions: str,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        建立 WebSocket 并发送实时翻译会话配置。

        Args:
            instructions: 翻译模型不使用系统提示词，保留参数以兼容 RealtimeAgent。
            tools: 翻译模型不支持工具，忽略。
            **kwargs: RealtimeAgent 传入的兼容参数，忽略。

        Raises:
            RuntimeError: 建连失败、会话配置超时或服务端返回错误。
        """
        import websockets

        await self.close()
        while not self._queue.empty():
            self._queue.get_nowait()

        self._session_ready = asyncio.Event()
        self._connect_error = ""
        credential: DashScopeCredential = self.credential  # type: ignore[assignment]
        self._ws = await websockets.connect(
            f"{LIVETRANSLATE_URL}?model={self.model}",
            additional_headers={
                "Authorization": f"Bearer {credential.api_key.get_secret_value()}",
                "X-DashScope-DataInspection": "disable",
            },
        )
        self._reader = asyncio.create_task(self._read(), name="livetranslate-rt")
        await self._send(self._session_update(instructions, tools))

        try:
            await asyncio.wait_for(self._session_ready.wait(), timeout=15)
        except asyncio.TimeoutError as exc:
            await self.close()
            raise RuntimeError("实时翻译模型会话配置超时") from exc
        if self._connect_error:
            await self.close()
            raise RuntimeError(self._connect_error)

    async def close(self) -> None:
        """发送 session.finish 后关闭连接，尽量收完最后一段翻译。"""
        if self._ws is not None:
            try:
                await self._send({"type": "session.finish"})
            except Exception:
                # 连接已断开时不需要再发 finish；直接走父类关闭
                pass
            await asyncio.sleep(0.2)
        await super().close()

    async def commit_turn(self) -> None:
        """翻译模型由服务端 speaker_detection 自动断句，无需手动提交。"""

    async def request_response(self) -> None:
        """翻译响应由服务端在断句后自动生成，无需主动请求。"""

    async def cancel_response(self) -> None:
        """翻译协议不提供可靠的取消帧，保留当前响应由 Agent 侧丢弃。"""

    def _session_update(
        self,
        instructions: str,
        tools: list[dict] | None,
    ) -> dict:
        """构建实时翻译的 session.update 消息。"""
        p = self.parameters
        return {
            "type": "session.update",
            "session": {
                "output_modalities": list(p.output_modalities),
                "voice": p.voice,
                "translation": {"language": p.translation_language},
                "audio": {
                    "input": {
                        "turn_detection": {
                            "type": "speaker_detection",
                            "threshold": 0.5,
                        },
                    },
                },
            },
        }

    def _parse(self, data: dict) -> me.ModelEvent | None:  # noqa: C901
        """把实时翻译服务端事件翻译成 AgentScope 模型事件。"""
        kind = data.get("type", "")
        item_id = data.get("item_id", "")

        match kind:
            case "session.updated":
                self._session_ready.set()
                return None

            case "error":
                err = data.get("error", {})
                message = err.get("message", "") or str(data)
                self._connect_error = message
                self._session_ready.set()
                return me.ModelErrorEvent(
                    code=err.get("code", ""),
                    message=message,
                )

            case "input_audio_buffer.speech_started":
                return me.SpeechStartedEvent(
                    item_id=item_id,
                    at_ms=data.get("audio_start_ms", 0),
                )

            case "input_audio_buffer.speech_stopped":
                return me.SpeechEndedEvent(
                    item_id=item_id,
                    at_ms=data.get("audio_end_ms", 0),
                )

            case "conversation.item.input_audio_transcription.completed":
                return me.InputTranscriptionEvent(
                    item_id=item_id,
                    text=data.get("transcript", ""),
                )

            case "response.created":
                response = data.get("response", {})
                self._item_id = response.get("id") or data.get("item_id", "")
                return me.ResponseCreatedEvent(item_id=self._item_id)

            case "response.audio.delta":
                delta = data.get("delta")
                if not delta:
                    return None
                return me.AudioDeltaEvent(
                    item_id=self._item_id,
                    pcm=base64.b64decode(delta),
                    sample_rate=self.output_sample_rate,
                )

            case "response.audio_transcript.delta" | "response.text.delta":
                delta = data.get("delta")
                if not delta:
                    return None
                return me.TranscriptDeltaEvent(
                    item_id=self._item_id,
                    delta=delta,
                )

            case "response.done":
                response = data.get("response", {})
                usage = response.get("usage") or {}
                event = me.ResponseDoneEvent(
                    item_id=response.get("id") or self._item_id,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                )
                self._item_id = ""
                return event

            case "session.finished":
                return me.SessionEndedEvent(reason="finished")

            case _:
                return None


__all__ = [
    "LIVETRANSLATE_CARD",
    "LIVETRANSLATE_MODEL",
    "LIVETRANSLATE_URL",
    "LiveTranslateRealtimeModel",
]
