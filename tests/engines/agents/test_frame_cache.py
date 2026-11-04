"""
单文件调试指令：python -m pytest tests/engines/agents/test_frame_cache.py -vv --tb=short

本文件是坐标核对帧缓存的契约测试（纯单测，不连设备）：

1. test_put_* —— 放帧返回 token，按（设备, token）能取回同样的几何信息。
2. test_expired_* —— 超过 TTL 取不到。
3. test_cross_device_* —— 别的设备拿同一个 token 取不到。
4. test_limit_* —— 同一设备超过 2 帧时淘汰最旧的一帧。
5. test_empty_token_returns_none / test_clear_* —— 空 token 与清空行为。
"""

from __future__ import annotations

import time

import pytest

from engines.agents.tools import tool_frame_cache as _frame_cache

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _empty_frames() -> None:
    """每个用例从空缓存开始。"""
    _frame_cache.clear()


def _put(serial: str = "serial-1", point_x: int = 540, point_y: int = 1200) -> str:
    """放一帧默认几何的截图（单个标记点），返回 token。"""
    return _frame_cache.put(
        serial,
        width=1080,
        height=2400,
        points=((point_x, point_y),),
        image_b64="frame-bytes",
        media_type="image/jpeg",
    )


def test_put_returns_token_and_frame_round_trips() -> None:
    """放帧后能按 token 取回同样的几何与图片信息。"""
    token = _put()

    frame = _frame_cache.get("serial-1", token)

    assert frame is not None
    assert frame.token == token
    assert frame.serial == "serial-1"
    assert (frame.width, frame.height) == (1080, 2400)
    assert frame.points == ((540, 1200),)
    assert frame.image_b64 == "frame-bytes"
    assert frame.media_type == "image/jpeg"


def test_expired_frame_is_not_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    """超过 TTL 的帧取不到。"""
    monkeypatch.setattr(_frame_cache, "TTL_SECONDS", 0.0)
    token = _put()
    time.sleep(0.002)

    assert _frame_cache.get("serial-1", token) is None


def test_cross_device_token_is_rejected() -> None:
    """别的设备拿同一个 token 取不到帧。"""
    token = _put(serial="serial-1")

    assert _frame_cache.get("serial-2", token) is None
    assert _frame_cache.get("serial-1", token) is not None


def test_limit_keeps_only_latest_two_frames() -> None:
    """同一设备放三帧时淘汰最旧的一帧，最新两帧还在。"""
    first = _put(point_x=1)
    second = _put(point_x=2)
    third = _put(point_x=3)

    assert _frame_cache.get("serial-1", first) is None
    assert _frame_cache.get("serial-1", second) is not None
    assert _frame_cache.get("serial-1", third) is not None


def test_empty_token_returns_none() -> None:
    """空 token 一律取不到，不报错。"""
    _put()

    assert _frame_cache.get("serial-1", "") is None
    assert _frame_cache.get("serial-1", "   ") is None


def test_clear_drops_every_frame() -> None:
    """清空后再也取不到。"""
    token = _put()

    _frame_cache.clear()

    assert _frame_cache.get("serial-1", token) is None
