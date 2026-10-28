"""
python -m 调试路径: engines.agents.realtime_vocie.pipeline_tts

本模块的业务功能如下：
1. QwenTts: 调百炼 qwen3-tts-flash，把回答文本合成为 24kHz PCM16 单声道音频。
2. SambertTts: 调 Sambert（默认 sambert-zhichu-v1），通过 WebSocket run-task 合成 PCM16。
3. _split_text(): 按标点切分长文本，绕过单次字符上限。
4. _wav_to_pcm(): 解析 WAV、降混单声道并重采样到 24kHz。

说明：qwen3.8-livetranslate 的输入模态只有 Audio/Image，不能接收文本做 TTS；
Pipeline 的 TTS 使用 Sambert 或 qwen3-tts-flash（Text → Audio）。
"""

from __future__ import annotations

import array
import asyncio
import io
import json
import re
import sys
import uuid
import wave

import httpx
import websockets

from engines.agents.realtime_vocie.config import (
    DEFAULT_PIPELINE_TTS_MODEL,
    DEFAULT_PIPELINE_TTS_VOICE,
)

_TTS_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
_SAMBERT_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
_TTS_SAMPLE_RATE = 24000
_TTS_CHUNK_CHARS = 500


class QwenTts:
    """
    Qwen3-TTS-Flash 语音合成器。

    Attributes:
        model: TTS 模型名。
        voice: 系统音色。
        sample_rate: 输出 PCM 采样率，固定 24000。
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_PIPELINE_TTS_MODEL,
        voice: str = DEFAULT_PIPELINE_TTS_VOICE,
    ) -> None:
        """
        初始化 TTS。

        Args:
            api_key: DashScope API Key。
            model: TTS 模型名。
            voice: 音色名。

        Raises:
            RuntimeError: API Key 为空。
        """
        if not api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法调用 TTS")
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.sample_rate = _TTS_SAMPLE_RATE

    async def synthesize(self, text: str) -> bytes:
        """
        把一段文本合成为 PCM16 单声道 24kHz 音频。

        Args:
            text: 回答文本。

        Returns:
            PCM16 little-endian 字节；文本为空时返回空字节。

        Raises:
            RuntimeError: TTS 请求失败、返回缺少音频或 WAV 解析失败。
        """
        chunks = _split_text(text)
        if not chunks:
            return b""
        pcm_parts: list[bytes] = []
        for chunk in chunks:
            pcm_parts.append(await self._synthesize_chunk(chunk))
        return b"".join(pcm_parts)

    async def _synthesize_chunk(self, text: str) -> bytes:
        """合成单段文本并下载音频。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": {
                "text": text,
                "voice": self.voice,
                "language_type": "Chinese",
            },
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(_TTS_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                audio = (data.get("output") or {}).get("audio") or {}
                url = audio.get("url") or ""
                encoded = audio.get("data") or ""
                if url:
                    audio_response = await client.get(url)
                    audio_response.raise_for_status()
                    raw = audio_response.content
                elif encoded:
                    import base64

                    raw = base64.b64decode(encoded)
                else:
                    raise RuntimeError("TTS 返回中没有音频数据")
        except httpx.HTTPError as exc:
            raise RuntimeError(f"TTS 请求失败：{exc}") from exc

        try:
            return await asyncio.to_thread(_wav_to_pcm, raw, _TTS_SAMPLE_RATE)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"TTS 音频解析失败：{exc}") from exc


class SambertTts:
    """
    Sambert 语音合成器（WebSocket run-task）。

    Attributes:
        model: Sambert 模型/音色 ID，例如 sambert-zhichu-v1。
        sample_rate: 输出 PCM 采样率，固定 24000。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "sambert-zhichu-v1",
        sample_rate: int = _TTS_SAMPLE_RATE,
    ) -> None:
        """
        初始化 Sambert TTS。

        Args:
            api_key: DashScope API Key。
            model: Sambert 模型/音色 ID。
            sample_rate: 输出 PCM 采样率。

        Raises:
            RuntimeError: API Key 为空。
        """
        if not api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法调用 Sambert TTS")
        self.api_key = api_key
        self.model = model
        self.sample_rate = sample_rate

    async def synthesize(self, text: str) -> bytes:
        """
        把文本合成为 PCM16 单声道音频。

        Args:
            text: 回答文本。

        Returns:
            PCM16 little-endian 字节；文本为空时返回空字节。

        Raises:
            RuntimeError: Sambert 任务失败或没有返回音频。
        """
        chunks = _split_text(text)
        if not chunks:
            return b""
        pcm_parts: list[bytes] = []
        for chunk in chunks:
            pcm_parts.append(await self._synthesize_chunk(chunk))
        return b"".join(pcm_parts)

    async def _synthesize_chunk(self, text: str) -> bytes:
        """合成单段文本并拼接二进制音频帧。"""
        task_id = uuid.uuid4().hex
        payload = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "out",
            },
            "payload": {
                "model": self.model,
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "input": {"text": text},
                "parameters": {
                    "text_type": "PlainText",
                    "format": "pcm",
                    "sample_rate": self.sample_rate,
                    "volume": 50,
                    "rate": 1.0,
                    "pitch": 1.0,
                },
            },
        }
        audio = bytearray()
        try:
            async with websockets.connect(
                _SAMBERT_URL,
                additional_headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-DashScope-DataInspection": "disable",
                },
                open_timeout=10,
            ) as ws:
                await ws.send(json.dumps(payload, ensure_ascii=False))
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=60)
                    if isinstance(raw, bytes):
                        audio.extend(raw)
                        continue
                    event = json.loads(raw)
                    header = event.get("header") or {}
                    kind = header.get("event", "")
                    if kind == "task-finished":
                        break
                    if kind == "task-failed":
                        message = header.get("error_message") or "Sambert 任务失败"
                        raise RuntimeError(message)
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Sambert TTS 请求失败：{exc}") from exc

        if not audio:
            raise RuntimeError("Sambert TTS 没有返回音频")
        return bytes(audio)


def _split_text(text: str) -> list[str]:
    """
    按句号/问号/感叹号等切分长文本。

    Args:
        text: 原始文本。

    Returns:
        每段不超过 _TTS_CHUNK_CHARS 的文本列表。
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= _TTS_CHUNK_CHARS:
        return [text]

    parts: list[str] = []
    current = ""
    for sentence in re.split(r"(?<=[。！？!?；;])", text):
        if not sentence:
            continue
        if len(current) + len(sentence) <= _TTS_CHUNK_CHARS:
            current += sentence
            continue
        if current:
            parts.append(current)
        current = sentence
        while len(current) > _TTS_CHUNK_CHARS:
            parts.append(current[:_TTS_CHUNK_CHARS])
            current = current[_TTS_CHUNK_CHARS:]
    if current:
        parts.append(current)
    return parts


def _wav_to_pcm(wav_bytes: bytes, target_rate: int) -> bytes:
    """
    把 WAV 转成 PCM16 单声道 target_rate。

    Args:
        wav_bytes: WAV 文件字节。
        target_rate: 目标采样率。

    Returns:
        PCM16 little-endian 字节。

    Raises:
        RuntimeError: WAV 不是 8/16/32 位 PCM。
    """
    with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
        channels = reader.getnchannels()
        width = reader.getsampwidth()
        rate = reader.getframerate()
        raw = bytearray()
        while True:
            block = reader.readframes(8192)
            if not block:
                break
            raw.extend(block)

    if width == 2:
        samples = array.array("h")
        samples.frombytes(bytes(raw))
        if sys.byteorder != "little":
            samples.byteswap()
        values = [sample / 32768.0 for sample in samples]
    elif width == 1:
        values = [(sample - 128) / 128.0 for sample in raw]
    elif width == 4:
        samples = array.array("i")
        samples.frombytes(bytes(raw))
        if sys.byteorder != "little":
            samples.byteswap()
        values = [sample / 2147483648.0 for sample in samples]
    else:
        raise RuntimeError(f"不支持的 WAV 位宽: {width * 8}")

    if channels > 1:
        frames = len(values) // channels
        values = [
            sum(values[index * channels + channel] for channel in range(channels)) / channels
            for index in range(frames)
        ]

    if rate != target_rate and values:
        output_length = int(len(values) * target_rate / rate)
        step = rate / target_rate
        values = [values[min(len(values) - 1, int(index * step))] for index in range(output_length)]

    pcm = array.array(
        "h",
        (int(max(-1.0, min(1.0, value)) * 32767) for value in values),
    )
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()
