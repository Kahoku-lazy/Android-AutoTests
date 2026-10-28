"""
python -m 调试路径: engines.agents.realtime_vocie.transport

本模块的业务功能如下：
1. WebSocketAudioTransport: TransportBase 的浏览器实现。
   - incoming(): 把浏览器二进制音频与控制帧交给 RealtimeAgent。
   - send_audio(): 把模型音频按二进制帧下发，并在条目变化时先发 audio_item。
   - clear_audio() / playout(): 用浏览器回报的播放进度截断被打断的回复。

音频只做透传，不重采样；采样率由模型卡决定，前端按 ready 事件里的
采样率采集与播放。
"""

from __future__ import annotations

import array
import asyncio
import sys
import time

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from agentscope.realtime import (
    AudioFrame,
    ControlFrame,
    ControlFrameType,
    PlayoutPosition,
    TransportBase,
    TransportFrame,
)

JsonSender = Callable[[dict], Awaitable[None]]
BytesSender = Callable[[bytes], Awaitable[None]]

# 最多缓存 10 秒上行音频（100ms 一块）；超出时丢最旧的一块，避免模型变慢后回放陈旧语音。
_MAX_QUEUED_FRAMES = 100


class WebSocketAudioTransport(TransportBase):
    """
    浏览器 <-> RealtimeAgent 的音频传输。

    Attributes:
        input_sample_rate: 浏览器上行 PCM16 的采样率。
        output_sample_rate: 模型下行 PCM16 的采样率。
    """

    def __init__(
        self,
        send_json: JsonSender,
        send_bytes: BytesSender,
        *,
        input_sample_rate: int = 16000,
        output_sample_rate: int = 24000,
    ) -> None:
        """
        初始化传输。

        Args:
            send_json: 向浏览器发送一条 JSON 控制/转写事件的协程。
            send_bytes: 向浏览器发送一帧二进制音频的协程。
            input_sample_rate: 上行采样率，默认 16000。
            output_sample_rate: 下行采样率，默认 24000。
        """
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self._send_json = send_json
        self._send_bytes = send_bytes
        self._queue: asyncio.Queue[TransportFrame | None] = asyncio.Queue()
        self._closed = False
        self._item_id = ""
        self._played = PlayoutPosition(item_id="", played_ms=0)
        self._first_played_at: float | None = None
        # 诊断用：本次会话收到多少上行音频、最响电平；session_end 会写进对话日志。
        self.audio_frames = 0
        self.audio_bytes = 0
        self.audio_level_max = 0.0
        self.audio_peak = 0.0

    async def start(self) -> None:
        """标记传输已打开；本实现的队列在构造时即就绪。"""
        self._closed = False

    async def close(self) -> None:
        """结束 incoming() 迭代；重复调用安全。"""
        if self._closed:
            return
        self._closed = True
        self._put(None)

    async def incoming(self) -> AsyncIterator[TransportFrame]:
        """持续产出浏览器上行帧，直到 close()。"""
        while True:
            frame = await self._queue.get()
            if frame is None:
                return
            yield frame

    def push_audio(self, pcm: bytes) -> None:
        """
        把浏览器的一帧音频放入上行队列。

        Args:
            pcm: 单声道 PCM16 字节；空帧忽略。
        """
        if self._closed or not pcm:
            return
        self.audio_frames += 1
        self.audio_bytes += len(pcm)
        level, peak = _pcm_stats(pcm)
        self.audio_level_max = max(self.audio_level_max, level)
        self.audio_peak = max(self.audio_peak, peak)
        self._put(AudioFrame(pcm=pcm))

    def push_control(self, frame: ControlFrame) -> None:
        """
        把一条浏览器控制帧放入上行队列。

        Args:
            frame: 已解析的控制帧。
        """
        if self._closed:
            return
        self._put(frame)

    def push_interrupt(self) -> None:
        """把浏览器的「打断」消息封装成 AgentScope 控制帧并入队。"""
        self.push_control(ControlFrame(type=ControlFrameType.INTERRUPT))

    async def send_audio(self, pcm: bytes, item_id: str) -> None:
        """
        把模型音频下发给浏览器。

        Args:
            pcm: 单声道 PCM16 音频块。
            item_id: 该音频所属的助手条目 id。
        """
        if not pcm:
            return
        if item_id != self._item_id:
            self._item_id = item_id
            self._played = PlayoutPosition(item_id=item_id, played_ms=0)
            self._first_played_at = None
            await self._send_json({"type": "audio_item", "item_id": item_id})
        await self._send_bytes(pcm)

    async def clear_audio(self) -> PlayoutPosition:
        """
        通知浏览器清空播放队列，并返回清空前实际播放到的位置。

        Returns:
            最近一次播放进度回报；没有回报时为当前条目的 0ms。
        """
        await self._send_json({"type": "clear_audio"})
        return self.playout()

    def playout(self) -> PlayoutPosition:
        """返回最近一次浏览器回报的播放位置。"""
        if self._item_id and self._played.item_id != self._item_id:
            return PlayoutPosition(item_id=self._item_id, played_ms=0)
        return self._played

    def report_played(self, item_id: str, played_ms: int) -> None:
        """
        记录浏览器回报的播放进度。

        Args:
            item_id: 正在播放的助手条目 id。
            played_ms: 已播放毫秒数；负值按 0 处理。
        """
        if not item_id:
            return
        position = max(0, int(played_ms))
        if position > 0 and self._first_played_at is None:
            self._first_played_at = time.monotonic()
        self._played = PlayoutPosition(
            item_id=item_id,
            played_ms=position,
            first_played_at=self._first_played_at,
        )

    def _put(self, item: Any) -> None:
        """
        入队一帧；队列满时丢弃最旧的一帧。

        Args:
            item: AudioFrame / ControlFrame / None 哨兵。
        """
        if self._queue.qsize() >= _MAX_QUEUED_FRAMES:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                # 并发消费已经取空：直接入队即可，不需要额外处理
                pass
        self._queue.put_nowait(item)


def _pcm_stats(pcm: bytes) -> tuple[float, float]:
    """
    计算一帧 PCM16 的归一化 RMS 与峰值，用于判断麦克风是静音还是有声音。

    Args:
        pcm: 单声道 PCM16 小端字节。

    Returns:
        `(rms, peak)`，均在 0..1 范围内；空帧返回 `(0, 0)`。
    """
    usable = len(pcm) - (len(pcm) % 2)
    if usable <= 0:
        return 0.0, 0.0
    samples = array.array("h")
    samples.frombytes(pcm[:usable])
    if sys.byteorder != "little":
        samples.byteswap()
    squared = 0
    peak = 0
    for sample in samples:
        squared += sample * sample
        peak = max(peak, abs(sample))
    rms = (squared / len(samples)) ** 0.5 / 32768
    return min(1.0, rms), min(1.0, peak / 32768)
