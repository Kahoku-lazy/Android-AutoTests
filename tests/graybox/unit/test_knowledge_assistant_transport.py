"""知识库助手浏览器音频传输单测：不启服务、不用声卡。"""

from __future__ import annotations

import pytest

from agentscope.realtime import AudioFrame, ControlFrame, ControlFrameType

from engines.agents.realtime_vocie.transport import WebSocketAudioTransport

pytestmark = [pytest.mark.unit]


def _make_transport():
    sent: list[tuple[str, object]] = []

    async def send_json(payload):
        sent.append(("json", payload))

    async def send_bytes(payload):
        sent.append(("bytes", payload))

    return WebSocketAudioTransport(send_json, send_bytes), sent


def test_push_audio_counts_frames_for_diagnostics():
    """会话结束日志用帧数判断麦克风是否真的送来了音频。"""
    transport, _ = _make_transport()

    transport.push_audio(b"\x01\x02")
    transport.push_audio(b"")

    assert transport.audio_frames == 1
    assert transport.audio_bytes == 2


def test_push_audio_tracks_level_and_peak():
    """静音帧电平原样为 0；有信号帧峰值/RMS 能反映音量。"""
    transport, _ = _make_transport()

    transport.push_audio(b"\x00\x00" * 1600)
    assert transport.audio_peak == 0.0
    assert transport.audio_level_max == 0.0

    transport.push_audio(b"\x00\x40" * 1600)
    assert transport.audio_peak == pytest.approx(0.5, abs=0.01)
    assert transport.audio_level_max == pytest.approx(0.5, abs=0.01)


async def test_incoming_yields_audio_and_control_then_stops():
    """上行音频与控制帧按入队顺序产出，close 后迭代结束。"""
    transport, _ = _make_transport()
    await transport.start()
    transport.push_audio(b"\x01\x02")
    transport.push_control(ControlFrame(type=ControlFrameType.INTERRUPT))
    stream = transport.incoming()

    first = await anext(stream)
    second = await anext(stream)
    assert isinstance(first, AudioFrame)
    assert first.pcm == b"\x01\x02"
    assert isinstance(second, ControlFrame)
    assert second.type is ControlFrameType.INTERRUPT

    await transport.close()
    with pytest.raises(StopAsyncIteration):
        await anext(stream)


async def test_push_interrupt_enqueues_control_frame():
    """浏览器打断消息由引擎封装成 AgentScope 控制帧。"""
    transport, _ = _make_transport()
    transport.push_interrupt()

    frame = await anext(transport.incoming())

    assert isinstance(frame, ControlFrame)
    assert frame.type is ControlFrameType.INTERRUPT


async def test_send_audio_marks_item_before_binary_frames():
    """条目变化时先发 audio_item，再发二进制音频。"""
    transport, sent = _make_transport()

    await transport.send_audio(b"a", "item-1")
    await transport.send_audio(b"b", "item-1")
    await transport.send_audio(b"c", "item-2")

    assert sent == [
        ("json", {"type": "audio_item", "item_id": "item-1"}),
        ("bytes", b"a"),
        ("bytes", b"b"),
        ("json", {"type": "audio_item", "item_id": "item-2"}),
        ("bytes", b"c"),
    ]


async def test_clear_audio_returns_reported_playout():
    """clear_audio 通知浏览器清空，并返回最近一次播放进度。"""
    transport, sent = _make_transport()
    transport.report_played("item-1", 1234)

    position = await transport.clear_audio()

    assert position.item_id == "item-1"
    assert position.played_ms == 1234
    assert sent == [("json", {"type": "clear_audio"})]


async def test_playout_defaults_to_current_item_when_report_is_stale():
    """回报属于旧条目时，当前条目按 0ms 处理。"""
    transport, _ = _make_transport()
    await transport.send_audio(b"a", "item-2")
    transport.report_played("item-1", 500)

    position = transport.playout()

    assert position.item_id == "item-2"
    assert position.played_ms == 0


def test_negative_played_is_clamped():
    """负的播放进度按 0 处理。"""
    transport, _ = _make_transport()
    transport.report_played("item-1", -99)

    assert transport.playout().played_ms == 0
