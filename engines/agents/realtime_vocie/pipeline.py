"""
python -m 调试路径: engines.agents.realtime_vocie.pipeline

本模块的业务功能如下：
1. PipelineVoiceSession: ASR（livetranslate）→ DeepSeek Flash → Qwen-TTS 的语音问答会话。
2. _forward_audio(): 把浏览器上行 PCM 送进 ASR，并处理打断。
3. _consume_asr(): 只消费 ASR 源语转写，翻译文本不进入回答。
4. _answer(): 流式显示 DeepSeek 回答，再合成 TTS 音频下发浏览器。

该会话不经过 RealtimeAgent；它复用 WebSocketAudioTransport 的上行/下行与打断能力。
"""

from __future__ import annotations

import asyncio
import os
import uuid

from collections.abc import Awaitable, Callable

from agentscope.credential import DashScopeCredential
from agentscope.realtime import (
    AudioFrame,
    ControlFrame,
    ControlFrameType,
    InputTranscriptionEvent,
    ResponseDoneEvent,
    SessionEndedEvent,
    SpeechEndedEvent,
    SpeechStartedEvent,
)

from engines.agents.rag.service import RagService

from .agent_answerer import AgentAnswerer
from .config import (
    PIPELINE_MODE,
    RealtimeVoiceConfig,
)
from .events import VoiceLogSink
from .livetranslate import LiveTranslateRealtimeModel
from .pipeline_llm import DeepSeekAnswerer
from .pipeline_tts import QwenTts, SambertTts
from .transport import WebSocketAudioTransport
from .tts_model import LocalTtsModel

SendJson = Callable[[dict], Awaitable[None]]


class PipelineVoiceSession:
    """
    ASR + DeepSeek + TTS 的语音问答会话。

    Attributes:
        config: 本次会话配置。
        transport: 浏览器音频传输。
        send_json: 向浏览器发 JSON 事件的协程。
        log: 对话日志写入方。
    """

    def __init__(
        self,
        config: RealtimeVoiceConfig,
        transport: WebSocketAudioTransport,
        send_json: SendJson,
        log: VoiceLogSink,
    ) -> None:
        """
        初始化 Pipeline 会话。

        Args:
            config: 已校验配置；mode 必须为 pipeline。
            transport: 浏览器音频传输。
            send_json: 向浏览器发 JSON 事件的协程。
            log: 对话日志写入方。
        """
        self.config = config
        self.transport = transport
        self.send_json = send_json
        self.log = log
        self._asr: LiveTranslateRealtimeModel | None = None
        self._answerer: DeepSeekAnswerer | AgentAnswerer | None = None
        self._rag: RagService | None = None
        self._tts: QwenTts | SambertTts | None = None
        self._answer_task: asyncio.Task | None = None
        self._finalize_task: asyncio.Task | None = None
        self._assistant_reply_id = ""
        self._user_reply_id = ""
        self._user_text = ""
        self._state = ""
        self._ready_event = asyncio.Event()
        self._text_input_used = False
        self._usage_input = 0
        self._usage_output = 0
        self._usage_cache_input = 0
        self._usage_cache_creation = 0
        self._asr_input_tokens = 0
        self._asr_output_tokens = 0

    async def run(self) -> None:
        """
        运行一次 Pipeline 语音会话，直到通道关闭或任务被取消。

        Raises:
            RuntimeError: ASR 连接或依赖初始化失败。
        """
        self._asr = self._create_asr()
        self._rag = RagService.from_env(usage_sink=self._on_embedding_usage)
        if self.config.pipeline_tts_provider == "sambert":
            self._tts = SambertTts(
                self.config.api_key,
                model=self.config.pipeline_tts_model,
            )
        else:
            self._tts = QwenTts(
                self.config.api_key,
                model=self.config.pipeline_tts_model,
                voice=self.config.pipeline_tts_voice,
            )
        if self.config.pipeline_engine == "agent":
            self._answerer = self._create_agent_answerer()
        else:
            self._answerer = DeepSeekAnswerer(
                self.config.system_prompt,
                model_name=self.config.pipeline_llm_model,
                rag=self._rag,
            )
        await self._asr.connect("", None)
        # 首次会话建索引；失败只降级为无 RAG，不影响语音。
        await self._rag.ensure_index()
        self.transport.input_sample_rate = self._asr.input_sample_rate
        self.transport.output_sample_rate = self._tts.sample_rate

        reason = "closed"
        watchdog = asyncio.create_task(self._watch_microphone(), name="kb-pipeline-mic")
        try:
            async with self.transport:
                await self.send_json(
                    {
                        "type": "ready",
                        "session_id": self.log.session_id,
                        "agent_name": self.config.agent_name,
                        "model": (
                            f"{self.config.pipeline_llm_model} + {self.config.pipeline_tts_model}"
                        ),
                        "voice": self.config.pipeline_tts_voice,
                        "turn_detection": "speaker_detection",
                        "mode": PIPELINE_MODE,
                        "translation_language": "",
                        "input_sample_rate": self._asr.input_sample_rate,
                        "output_sample_rate": self._tts.sample_rate,
                        "log_path": self.log.display_path,
                    },
                )
                self._ready_event.set()
                self.log.event(
                    "session_start",
                    mode=PIPELINE_MODE,
                    asr=self.config.model,
                    llm=self.config.pipeline_llm_model,
                    tts=self.config.pipeline_tts_model,
                    rag=bool(self._rag and self._rag.enabled),
                )
                audio_task = asyncio.create_task(
                    self._forward_audio(),
                    name="kb-pipeline-audio",
                )
                asr_task = asyncio.create_task(
                    self._consume_asr(),
                    name="kb-pipeline-asr",
                )
                done, pending = await asyncio.wait(
                    {audio_task, asr_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    exception = task.exception()
                    if exception is not None:
                        raise exception
        except asyncio.CancelledError:
            reason = "cancelled"
            raise
        except Exception:
            reason = "error"
            raise
        finally:
            watchdog.cancel()
            await asyncio.gather(watchdog, return_exceptions=True)
            await self._cancel_finalize()
            await self._cancel_answer()
            if self._asr is not None:
                await self._asr.close()
            self.log.event(
                "session_end",
                reason=reason,
                mode=PIPELINE_MODE,
                audio_frames=self.transport.audio_frames,
                audio_bytes=self.transport.audio_bytes,
                audio_level_max=round(self.transport.audio_level_max, 4),
                audio_peak=round(self.transport.audio_peak, 4),
                input_tokens=self._usage_input,
                output_tokens=self._usage_output,
                cache_input_tokens=self._usage_cache_input,
                cache_creation_input_tokens=self._usage_cache_creation,
                asr_input_tokens=self._asr_input_tokens,
                asr_output_tokens=self._asr_output_tokens,
            )

    def _create_asr(self) -> LiveTranslateRealtimeModel:
        """创建只输出文本的 livetranslate ASR 模型。"""
        return LiveTranslateRealtimeModel(
            model=self.config.model,
            credential=DashScopeCredential(api_key=self.config.api_key),
            parameters=LiveTranslateRealtimeModel.Parameters(
                voice="Tina",
                translation_language="en",
                output_modalities=["text"],
            ),
        )

    async def submit_text(self, text: str) -> None:
        """
        处理一条纯文本提问：跳过 ASR，直接走 DeepSeek + RAG + TTS。

        Args:
            text: 用户输入的文字。
        """
        text = text.strip()
        if not text:
            return
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=20)
        except asyncio.TimeoutError:
            return
        self._text_input_used = True
        await self._cancel_finalize()
        self._user_text = ""
        self._user_reply_id = ""
        await self._cancel_answer()
        reply_id = f"user_{uuid.uuid4().hex[:10]}"
        await self.send_json(
            {
                "type": "reply_start",
                "reply_id": reply_id,
                "role": "user",
                "name": "user",
            },
        )
        await self.send_json(
            {
                "type": "transcript_delta",
                "reply_id": reply_id,
                "role": "user",
                "delta": text,
            },
        )
        await self.send_json(
            {
                "type": "transcript_final",
                "reply_id": reply_id,
                "role": "user",
                "text": text,
            },
        )
        await self.send_json(
            {
                "type": "reply_end",
                "reply_id": reply_id,
                "role": "user",
                "reason": "completed",
            },
        )
        self.log.message("user", text, reply_id)
        self._answer_task = asyncio.create_task(
            self._answer(text),
            name="kb-pipeline-text-answer",
        )

    async def _forward_audio(self) -> None:
        """持续把浏览器 PCM 送进 ASR，并处理打断。"""
        assert self._asr is not None
        async for frame in self.transport.incoming():
            if isinstance(frame, AudioFrame):
                await self._asr.push_audio(frame.pcm)
            elif isinstance(frame, ControlFrame) and frame.type == ControlFrameType.INTERRUPT:
                await self._interrupt()

    async def _consume_asr(self) -> None:
        """消费 ASR 事件：只处理语音开始与源语转写。"""
        assert self._asr is not None
        async for event in self._asr.events():
            if isinstance(event, SpeechStartedEvent):
                await self._on_speech_started(event.item_id)
            elif isinstance(event, SpeechEndedEvent):
                await self._schedule_finalize()
            elif isinstance(event, InputTranscriptionEvent):
                await self._on_transcript(event.text, event.item_id)
            elif isinstance(event, ResponseDoneEvent):
                self._on_asr_usage(event)
            elif isinstance(event, SessionEndedEvent):
                break

    def _on_embedding_usage(self, tokens: int) -> None:
        """记录 RAG 嵌入模型的 token 用量。"""
        if tokens <= 0 or self._rag is None:
            return
        self.log.event(
            "embedding_usage",
            provider="dashscope",
            category="Embedding",
            model=self._rag.config.embedding_model,
            tokens=tokens,
        )

    def _on_asr_usage(self, event: ResponseDoneEvent) -> None:
        """记录 ASR 模型返回的 token；全 0 不写伪造事件。"""
        if not (event.input_tokens or event.output_tokens):
            return
        self._asr_input_tokens += event.input_tokens
        self._asr_output_tokens += event.output_tokens
        self.log.event(
            "asr_usage",
            provider="dashscope",
            category="ASR",
            model=self.config.model,
            reply_id=event.item_id,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
        )

    async def _on_speech_started(self, item_id: str) -> None:
        """用户开始说话：开一条用户消息；同一句话的后续片段继续追加。"""
        await self._cancel_finalize()
        if not self._user_text:
            self._user_reply_id = item_id or f"user_{uuid.uuid4().hex[:10]}"
            await self.send_json(
                {
                    "type": "reply_start",
                    "reply_id": self._user_reply_id,
                    "role": "user",
                    "name": "user",
                },
            )
        await self._send_state("listening")
        self.log.event("vad_start", reply_id=self._user_reply_id)

    async def _on_transcript(self, text: str, item_id: str) -> None:
        """收到源语转写：追加到当前用户回合，等静音后再统一回答。"""
        text = text.strip()
        if not text:
            return
        if not self._user_reply_id:
            self._user_reply_id = item_id or f"user_{uuid.uuid4().hex[:10]}"
            await self.send_json(
                {
                    "type": "reply_start",
                    "reply_id": self._user_reply_id,
                    "role": "user",
                    "name": "user",
                },
            )
            await self._send_state("listening")
        separator = (
            " " if self._user_text and self._user_text[-1].isascii() and text[0].isascii() else ""
        )
        delta = f"{separator}{text}"
        self._user_text += delta
        await self.send_json(
            {
                "type": "transcript_delta",
                "reply_id": self._user_reply_id,
                "role": "user",
                "delta": delta,
            },
        )
        await self._schedule_finalize()

    async def _schedule_finalize(self) -> None:
        """每次语音片段结束后重置静音计时，避免一句话被拆成多轮回答。"""
        await self._cancel_finalize()
        self._finalize_task = asyncio.create_task(
            self._finalize_user_later(),
            name="kb-pipeline-finalize",
        )

    async def _finalize_user_later(self) -> None:
        """等 1.2 秒没有新片段后，把累计文本作为一轮用户问题。"""
        await asyncio.sleep(1.2)
        await self._finalize_user()

    async def _finalize_user(self) -> None:
        """收尾用户消息并启动回答。"""
        text = self._user_text.strip()
        reply_id = self._user_reply_id
        self._user_text = ""
        self._user_reply_id = ""
        self._finalize_task = None
        if not text:
            return
        await self.send_json(
            {
                "type": "transcript_final",
                "reply_id": reply_id,
                "role": "user",
                "text": text,
            },
        )
        await self.send_json(
            {
                "type": "reply_end",
                "reply_id": reply_id,
                "role": "user",
                "reason": "completed",
            },
        )
        self.log.message("user", text, reply_id)
        self.log.event("vad_end", reply_id=reply_id, reason="completed")
        await self._cancel_answer()
        self._answer_task = asyncio.create_task(
            self._answer(text),
            name="kb-pipeline-answer",
        )

    async def _cancel_finalize(self) -> None:
        """取消尚未到期的静音收尾计时。"""
        task = self._finalize_task
        self._finalize_task = None
        if task is None or task.done():
            return
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    def _create_agent_answerer(self) -> AgentAnswerer:
        """用 Agent + 中间件装配回答链路：文本走 Agent，语音走 TTS 中间件。

        Returns:
            已装配好的回答器；音频由 TTS 中间件产出、整段取走。

        Raises:
            RuntimeError: 缺少 DEEPSEEK_API_KEY。
        """
        from agentscope.agent import Agent, ReActConfig
        from agentscope.middleware import TTSMiddleware

        from engines.agents.config.models import DeepSeekModelConfig
        from engines.agents.middleware import RagContextMiddleware, build_agent_middlewares
        from engines.agents.role.config import ChatModelFactory, ModelConfig

        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY，无法使用 DeepSeek 回答")
        model = ChatModelFactory(
            ModelConfig(
                provider="deepseek",
                model_name=self.config.pipeline_llm_model,
                base_url=DeepSeekModelConfig.base_url,
                api_key=api_key,
            ),
            stream=True,
            vision=False,
        ).create()
        extra: list = []
        if self._rag is not None and self._rag.enabled:
            extra.append(RagContextMiddleware(self._rag))
        if self._tts is not None:
            extra.append(
                TTSMiddleware(
                    LocalTtsModel(
                        self._tts,
                        model=self.config.pipeline_tts_model,
                        api_key=self.config.api_key,
                        sample_rate=getattr(self._tts, "sample_rate", 24000),
                    )
                )
            )
        middlewares = build_agent_middlewares(with_tts=False, extra=extra)
        agent = Agent(
            name=self.config.agent_name,
            system_prompt=self.config.system_prompt,
            model=model,
            middlewares=middlewares,
            react_config=ReActConfig(max_iters=4),
        )
        return AgentAnswerer(agent)

    async def _answer(self, text: str) -> None:
        """流式显示 DeepSeek 回答，再合成 TTS 音频。"""
        assert self._answerer is not None
        assert self._tts is not None
        reply_id = f"resp_{uuid.uuid4().hex}"
        self._assistant_reply_id = reply_id
        await self.send_json(
            {
                "type": "reply_start",
                "reply_id": reply_id,
                "role": "assistant",
                "name": self.config.agent_name,
            },
        )
        await self._send_state("thinking")
        full = ""
        try:
            async for delta in self._answerer.stream(text):
                if not delta:
                    continue
                full += delta
                await self.send_json(
                    {
                        "type": "transcript_delta",
                        "reply_id": reply_id,
                        "role": "assistant",
                        "delta": delta,
                    },
                )
            if not full.strip():
                raise RuntimeError("DeepSeek 未返回文本")
            self._log_model_usage(reply_id)
            await self.send_json(
                {
                    "type": "transcript_final",
                    "reply_id": reply_id,
                    "role": "assistant",
                    "text": full,
                },
            )
            self.log.message("assistant", full, reply_id)
            await self._send_state("speaking")
            try:
                if isinstance(self._answerer, AgentAnswerer):
                    pcm = self._answerer.take_audio()
                else:
                    pcm = await self._tts.synthesize(full)
            except RuntimeError as exc:
                await self.send_json(
                    {
                        "type": "notice",
                        "message": f"语音播报失败，文字回答已保留：{exc}",
                    },
                )
            else:
                if pcm:
                    await self.transport.send_audio(pcm, reply_id)
                    self.log.event(
                        "tts_usage",
                        provider="dashscope",
                        category="TTS",
                        model=self.config.pipeline_tts_model,
                        reply_id=reply_id,
                        characters=len(full),
                    )
            await self.send_json(
                {
                    "type": "reply_end",
                    "reply_id": reply_id,
                    "role": "assistant",
                    "reason": "completed",
                },
            )
            self._assistant_reply_id = ""
            await self._send_state("listening")
        except asyncio.CancelledError:
            await self.send_json(
                {
                    "type": "reply_end",
                    "reply_id": reply_id,
                    "role": "assistant",
                    "reason": "interrupted",
                },
            )
            await self._send_state("listening")
            raise
        except Exception as exc:  # noqa: BLE001
            await self.send_json(
                {
                    "type": "error",
                    "message": f"回答生成失败：{exc}",
                },
            )
            await self._send_state("error")

    def _log_model_usage(self, reply_id: str) -> None:
        """记录本轮 DeepSeek token 并累计到会话汇总。"""
        if self._answerer is None or not self._answerer.last_usage:
            return
        usage = self._answerer.last_usage
        self._usage_input += usage.get("input_tokens", 0)
        self._usage_output += usage.get("output_tokens", 0)
        self._usage_cache_input += usage.get("cache_input_tokens", 0)
        self._usage_cache_creation += usage.get(
            "cache_creation_input_tokens",
            0,
        )
        self.log.event(
            "model_usage",
            provider="deepseek",
            category="LLM",
            model=self.config.pipeline_llm_model,
            reply_id=reply_id,
            **usage,
        )

    async def _interrupt(self) -> None:
        """取消当前回答并清空播放。"""
        had_answer = await self._cancel_answer()
        await self.transport.clear_audio()
        if self._assistant_reply_id and not had_answer:
            await self.send_json(
                {
                    "type": "reply_end",
                    "reply_id": self._assistant_reply_id,
                    "role": "assistant",
                    "reason": "interrupted",
                },
            )
            self._assistant_reply_id = ""
        await self._send_state("listening")

    async def _cancel_answer(self) -> bool:
        """取消正在运行的回答任务；返回是否确实取消了任务。"""
        task = self._answer_task
        self._answer_task = None
        if task is None or task.done():
            return False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return True

    async def _send_state(self, value: str) -> None:
        """发送状态事件；相同状态不重复。"""
        if value == self._state:
            return
        self._state = value
        await self.send_json({"type": "state", "value": value})

    async def _watch_microphone(self) -> None:
        """6 秒仍无上行音频时给一次可操作提示。"""
        await asyncio.sleep(3)
        self.log.event(
            "audio_probe",
            audio_frames=self.transport.audio_frames,
            audio_bytes=self.transport.audio_bytes,
            audio_level_max=round(self.transport.audio_level_max, 4),
            audio_peak=round(self.transport.audio_peak, 4),
        )
        await asyncio.sleep(3)
        if self.transport.audio_frames > 0 or self._text_input_used:
            return
        await self.send_json(
            {
                "type": "notice",
                "message": "没有检测到麦克风音频，请检查系统默认输入设备与浏览器麦克风权限",
            },
        )
