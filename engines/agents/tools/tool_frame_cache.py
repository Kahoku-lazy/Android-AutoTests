"""
文件名: ➡️ tool_frame_cache.py 🏁
路径: ➡️ engines/agents/tools/tool_frame_cache.py 🏁
模块功能：➡️ 坐标核对帧的进程内短时缓存：核对工具放帧并签发 token，点击类工具凭 token 复用同一帧 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_frame_cache 🏁
时间：➡️ 2026-11-04 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-04 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. Frame: 一帧已核对截图（设备、尺寸、核对点、图片与签发时刻）
2. put: 放帧并签发 token；每设备最多保留 2 帧，超限淘汰最旧
3. get: 按（设备, token）取帧；过期或不属于该设备时返回 None
4. clear: 清空缓存，仅供测试使用
🏁
关联模块：➡️
1. engines/agents/tools/tool_img_b64.py: mark_dot 核对后放帧
2. engines/agents/tools/tool_device.py: click_ratio / tap_screen 凭 token 取帧
🏁
测试：➡️
1. tests/engines/agents/test_frame_cache.py: 单文件调试指令：python -m pytest tests/engines/agents/test_frame_cache.py -vv --tb=short
🏁
"""

from __future__ import annotations

import threading
import time
import uuid

from dataclasses import dataclass

__all__ = [
    "MAX_FRAMES_PER_DEVICE",
    "TTL_SECONDS",
    "Frame",
    "clear",
    "get",
    "put",
]

# 一帧只在「核对完 → 点击」这段里有用；90 秒足够覆盖一次重标与一次模型往返
TTL_SECONDS = 90.0
# 一次核对之后可能再标一次（首标没打准），留两帧即可覆盖
MAX_FRAMES_PER_DEVICE = 2


@dataclass(frozen=True)
class Frame:
    """
    一帧已核对截图。

    Attributes:
        serial: 设备序列号。
        token: 该帧的标识，点击类工具凭它复用这一帧。
        width: 图片宽（像素），归一化坐标按它换算。
        height: 图片高（像素）。
        points: 已核对并标记的点，序号 = 下标 + 1；单点核对时长度为 1。
        image_b64: 原始截图 base64（不含红点）。
        media_type: 原始截图的 media_type。
        issued_at: 签发时刻（`time.monotonic()`），只用于算过期。
    """

    serial: str
    token: str
    width: int
    height: int
    points: tuple[tuple[int, int], ...]
    image_b64: str
    media_type: str
    issued_at: float


_lock = threading.Lock()
_frames: dict[str, Frame] = {}


def put(
    serial: str,
    *,
    width: int,
    height: int,
    points: tuple[tuple[int, int], ...],
    image_b64: str,
    media_type: str,
) -> str:
    """
    放一帧并签发 token。

    Args:
        serial: 设备序列号。
        width: 图片宽（像素）。
        height: 图片高（像素）。
        points: 已标记的点，序号 = 下标 + 1。
        image_b64: 原始截图 base64。
        media_type: 原始截图的 media_type。

    Returns:
        新签发的 token。
    """
    token = uuid.uuid4().hex[:8]
    frame = Frame(
        serial=str(serial),
        token=token,
        width=int(width),
        height=int(height),
        points=tuple((int(x), int(y)) for x, y in points),
        image_b64=image_b64,
        media_type=media_type,
        issued_at=time.monotonic(),
    )
    now = frame.issued_at
    with _lock:
        _purge_expired(now)
        _frames[token] = frame
        _enforce_limit(frame.serial)
    return token


def get(serial: str, token: str) -> Frame | None:
    """
    按设备与 token 取帧。

    Args:
        serial: 设备序列号。
        token: 核对工具签发的帧标识。

    Returns:
        有效帧；token 为空、已过期，或该帧不属于这台设备时为 None。
    """
    key = str(token or "").strip()
    if not key:
        return None
    now = time.monotonic()
    with _lock:
        _purge_expired(now)
        frame = _frames.get(key)
    if frame is None or frame.serial != str(serial):
        return None
    return frame


def clear() -> None:
    """清空缓存；只在测试里用，生产路径不调用。"""
    with _lock:
        _frames.clear()


def _purge_expired(now: float) -> None:
    """
    丢掉过期帧；调用方必须已持锁。

    Args:
        now: 当前 `time.monotonic()` 取值。
    """
    expired = [key for key, frame in _frames.items() if now - frame.issued_at > TTL_SECONDS]
    for key in expired:
        _frames.pop(key, None)


def _enforce_limit(serial: str) -> None:
    """
    按「每设备最多 MAX_FRAMES_PER_DEVICE 帧」淘汰最旧的；调用方必须已持锁。

    Args:
        serial: 设备序列号。
    """
    mine = [key for key, frame in _frames.items() if frame.serial == serial]
    overflow = len(mine) - MAX_FRAMES_PER_DEVICE
    for key in mine[: max(overflow, 0)]:
        _frames.pop(key, None)
