"""
python -m 调试路径: engines.agents.realtime_vocie.session

本模块的业务功能如下：
1. RealtimeVoiceSession.run(): 连接 AgentScope 实时模型，跑一轮语音会话的事件循环。
2. 把 ready / 转写 / 状态事件写给浏览器，并在会话收尾写 session_end。

会话不写数据库；模型、传输与日志都由调用方注入，便于替换与测试。
"""

from __future__ import annotations

import asyncio

from collections.abc import Awaitable, Callable

from agentscope.tool import Toolkit

from engines.agents.rag.service import RagService
from engines.agents.rag.tool import build_rag_tool
from utils.logs import agent_event_log

from .config import OMNI_MODE, RealtimeVoiceConfig, create_realtime_model
from .events import TranscriptBridge, VoiceLogSink
from .transport import WebSocketAudioTransport

SendJson = Callable[[dict], Awaitable[None]]


class RealtimeVoiceSession:
    """
    一次实时语音会话。

    Attributes:
        config: 会话配置。
        transport: 浏览器音频传输。
        send_json: 向浏览器发送 JSON 事件的协程。
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
        初始化会话。

        Args:
            config: 已校验的配置。
            transport: 浏览器音频传输。
            send_json: 向浏览器发送 JSON 事件的协程。
            log: 对话日志写入方。
        """
        self.config = config
        self.transport = transport
        self.send_json = send_json
        self.log = log

    async def run(self) -> None:
        """
        连接模型并持续消费事件，直到传输关闭或任务被取消。

        Raises:
            RuntimeError: 模型/依赖配置无效，或模型会话启动失败。
        """
        from agentscope.agent import RealtimeAgent

        model = create_realtime_model(self.config)
        self.transport.input_sample_rate = model.input_sample_rate
        self.transport.output_sample_rate = model.output_sample_rate
        rag = RagService.from_env()
        toolkit: Toolkit | None = None
        system_prompt = self.config.system_prompt
        if self.config.mode == OMNI_MODE and rag.enabled:
            toolkit = Toolkit(tools=[build_rag_tool(rag)])
            system_prompt = (
                f"{system_prompt}\n"
                "当用户询问按键、指示灯、固件、恢复出厂、H717D 等产品资料时，"
                "先调用 search_knowledge 工具检索；依据检索结果回答，"
                "资料没有覆盖的内容不要编造。需要检索时直接调用工具，"
                "不要在调用前先回复“稍等/我查一下”。"
            )
        agent = RealtimeAgent(
            name=self.config.agent_name,
            system_prompt=system_prompt,
            model=model,
            toolkit=toolkit,
        )
        bridge = TranscriptBridge(self.log, model=self.config.model)
        reason = "closed"
        watchdog: asyncio.Task | None = None

        try:
            async with agent, self.transport:
                await self.send_json(
                    {
                        "type": "ready",
                        "session_id": self.log.session_id,
                        "agent_name": self.config.agent_name,
                        "model": self.config.model,
                        "voice": self.config.voice,
                        "turn_detection": self.config.turn_detection,
                        "mode": self.config.mode,
                        "translation_language": self.config.translation_language,
                        "rag_enabled": rag.enabled,
                        "input_sample_rate": model.input_sample_rate,
                        "output_sample_rate": model.output_sample_rate,
                        "log_path": self.log.display_path,
                    },
                )
                self.log.event(
                    "session_start",
                    model=self.config.model,
                    voice=self.config.voice,
                    turn_detection=self.config.turn_detection,
                    rag=rag.enabled,
                )
                watchdog = asyncio.create_task(
                    self._watch_microphone(),
                    name="kb-mic-watchdog",
                )
                async for event in agent.reply_stream(self.transport):
                    for payload in bridge.handle(event):
                        await self.send_json(payload)
        except asyncio.CancelledError:
            reason = "cancelled"
            raise
        except Exception as exc:
            reason = "error"
            agent_event_log.exception("实时语音会话失败: %s", exc)
            raise
        finally:
            if watchdog is not None:
                watchdog.cancel()
                await asyncio.gather(watchdog, return_exceptions=True)
            # 用户点「结束」或通道断开时可能来不及收到 TextBlockEnd：
            # 把屏幕上已显示的文本补写进日志，避免「看到了但日志没有」。
            bridge.flush()
            self.log.event(
                "session_end",
                reason=reason,
                audio_frames=self.transport.audio_frames,
                audio_bytes=self.transport.audio_bytes,
                audio_level_max=round(self.transport.audio_level_max, 4),
                audio_peak=round(self.transport.audio_peak, 4),
                input_tokens=bridge.usage_input,
                output_tokens=bridge.usage_output,
                cache_input_tokens=bridge.usage_cache_input,
                cache_creation_input_tokens=bridge.usage_cache_creation,
            )

    async def _watch_microphone(self) -> None:
        """3 秒记一次帧数，6 秒仍无帧时给用户一条可操作的提示。"""
        await asyncio.sleep(3)
        # 写对话档案而不是 backend.log：后者在 Windows 双进程下滚动失败会吞掉诊断行。
        self.log.event(
            "audio_probe",
            audio_frames=self.transport.audio_frames,
            audio_bytes=self.transport.audio_bytes,
            audio_level_max=round(self.transport.audio_level_max, 4),
            audio_peak=round(self.transport.audio_peak, 4),
        )
        await asyncio.sleep(3)
        if self.transport.audio_frames > 0:
            return
        await self.send_json(
            {
                "type": "notice",
                "message": "没有检测到麦克风音频，请检查系统默认输入设备与浏览器麦克风权限",
            },
        )
