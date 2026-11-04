"""
文件名: ➡️ tool_img_b64.py 🏁
路径: ➡️ engines/agents/tools/tool_img_b64.py 🏁
模块功能：➡️ 2. mark_dot_b64: 纯函数，在 base64 图片上画圆点，base64 进、base64 出 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_img_b64 🏁
时间：➡️ 2026-10-22 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. mark_dot: 平台工具，截取设备当前屏幕并在坐标处画红点，返回标记后的图片、帧标识与像素坐标。
2. mark_dot_b64: 纯函数，在 base64 图片上画圆点，base64 进、base64 出。
3. build_img_b64_tools / img_b64_tool_specs: 工具函数表与 `ToolSpec` 产出。
🏁
关联模块：➡️
1. engines/agents/tools/tool_frame_cache.py: mark_dot 核对通过后把这一帧放进缓存并签发 token
2. engines.device.action: 导入 Screenshot, System, open_device
3. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/engines/agents/test_tool_img_b64.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_img_b64.py -vv --tb=shor
🏁
"""

from __future__ import annotations

import base64
import io

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable

from PIL import Image, ImageDraw

from engines.device.action import Screenshot, System, open_device
from utils.logs import agent_event_log

from . import tool_frame_cache as _frame_cache
from .tool_base import ToolSpec

__all__ = [
    "build_img_b64_tools",
    "img_b64_tool_specs",
    "mark_dot",
    "mark_dot_b64",
]

_READ_ONLY = frozenset({"mark_dot"})
_TOOL_ORDER = ("mark_dot",)
_FORMAT_MEDIA = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "MPO": "image/jpeg",
    "WEBP": "image/webp",
    "GIF": "image/gif",
    "BMP": "image/bmp",
}
# 圆点半径 = 图片短边 × 该比例；加白色外圈，深浅背景上都看得见
_DOT_RATIO = 0.015
_JPEG_QUALITY = 92


def _decode(image_b64: str) -> bytes:
    """base64（可带 data URI 前缀）→ 原始图片字节。

    Args:
        image_b64: 图片 base64，允许 `data:image/png;base64,...` 形式。

    Returns:
        解码后的图片字节。

    Raises:
        ValueError: 入参为空或不是合法 base64。
    """
    if not image_b64 or not image_b64.strip():
        raise ValueError("image_b64 不能为空")
    payload = image_b64.strip()
    if payload.lstrip().startswith("data:"):
        payload = payload.split(",", 1)[1]
    try:
        return base64.b64decode(payload, validate=False)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"image_b64 不是合法的 base64：{exc}") from exc


def _media_type(fmt: str) -> str:
    """PIL 格式名 → media_type；未知格式按 image/<小写> 兜底。"""
    return _FORMAT_MEDIA.get(fmt, f"image/{fmt.lower()}")


@contextmanager
def _device(serial: str):
    """打开一台设备，离开时断开。"""
    connection, info, control = open_device(System.ANDROID, str(serial))
    try:
        yield info, control
    finally:
        connection.disconnect()


def _screenshot_b64(serial: str) -> str:
    """截取设备当前屏幕，返回原始图片的 base64。"""
    with _device(serial) as (_info, control):
        return Screenshot(control).capture()["image_base64"]


def _point(x: float, y: float, width: int, height: int, normalized: bool) -> tuple[int, int]:
    """坐标 → 图片像素坐标。

    Args:
        x: 横坐标；normalized=True 时为 0~1，否则为像素。
        y: 纵坐标；normalized=True 时为 0~1，否则为像素。
        width: 图片宽（像素）。
        height: 图片高（像素）。
        normalized: 坐标口径。

    Returns:
        落在图片内的像素坐标 (cx, cy)。

    Raises:
        ValueError: 坐标不是数字，或像素坐标越界。
    """
    try:
        px, py = float(x), float(y)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"坐标必须是数字：x={x!r}, y={y!r}") from exc
    if normalized:
        # 夹到 0~1：模型偶尔给 1.0001，不应当报错
        nx = min(max(px, 0.0), 1.0)
        ny = min(max(py, 0.0), 1.0)
        return min(int(nx * width), width - 1), min(int(ny * height), height - 1)
    cx, cy = int(round(px)), int(round(py))
    if not (0 <= cx < width and 0 <= cy < height):
        raise ValueError(f"坐标越界：({cx}, {cy}) 不在 {width}x{height} 图片内")
    return cx, cy


@dataclass(frozen=True)
class _Marked:
    """
    标记结果：标记后的图片与它落点的几何信息。

    Attributes:
        base64: 标记后的图片 base64。
        media_type: 标记后图片的 media_type。
        width: 图片宽（像素）。
        height: 图片高（像素）。
        x: 红点落点的像素横坐标。
        y: 红点落点的像素纵坐标。
    """

    base64: str
    media_type: str
    width: int
    height: int
    x: int
    y: int


def _annotate(
    image_b64: str,
    x: float,
    y: float,
    *,
    normalized: bool,
    color: str,
    ring: str,
) -> _Marked:
    """解码、画圆点、再编码；返回标记结果（含图片尺寸与落点像素）。

    Args:
        image_b64: 原始图片 base64。
        x: 横坐标。
        y: 纵坐标。
        normalized: 坐标是否为归一化坐标。
        color: 圆点颜色。
        ring: 外圈描边颜色。

    Returns:
        标记结果：标记后的 base64、media_type、图片尺寸与红点落点像素。

    Raises:
        ValueError: base64 非法、图片无法解码，或像素坐标越界。
    """
    raw = _decode(image_b64)
    try:
        with Image.open(io.BytesIO(raw)) as src:
            fmt = (src.format or "PNG").upper()
            img = src.copy()
    except (OSError, ValueError) as exc:
        raise ValueError(f"image_b64 不是可识别的图片：{exc}") from exc

    save_fmt = "JPEG" if fmt in ("JPEG", "MPO") else fmt
    if save_fmt == "JPEG" or img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    width, height = img.size
    cx, cy = _point(x, y, width, height, normalized)
    radius = max(4, int(min(width, height) * _DOT_RATIO))
    ring_width = max(2, radius // 3)
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        (
            cx - radius - ring_width,
            cy - radius - ring_width,
            cx + radius + ring_width,
            cy + radius + ring_width,
        ),
        fill=ring,
    )
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)

    buf = io.BytesIO()
    if save_fmt == "JPEG":
        img.save(buf, "JPEG", quality=_JPEG_QUALITY)
    else:
        img.save(buf, save_fmt)
    return _Marked(
        base64=base64.b64encode(buf.getvalue()).decode("ascii"),
        media_type=_media_type(fmt),
        width=width,
        height=height,
        x=cx,
        y=cy,
    )


def mark_dot_b64(
    image_b64: str,
    x: float,
    y: float,
    *,
    normalized: bool = True,
    color: str = "red",
    ring: str = "white",
) -> str:
    """在 base64 图片的指定坐标画一个圆点，返回标记后的 base64；不落盘。

    Args:
        image_b64: 原始图片 base64，可带 data URI 前缀。
        x: 横坐标；normalized=True 时为 0~1，否则为像素。
        y: 纵坐标；normalized=True 时为 0~1，否则为像素。
        normalized: 坐标口径，默认归一化（与 click_ratio 的 nx/ny 一致）。
        color: 圆点颜色，默认红色。
        ring: 外圈描边颜色，默认白色。

    Returns:
        标记后的 base64，编码格式沿用输入图片。

    Raises:
        ValueError: image_b64 非法、图片无法解码，或像素坐标越界。
    """
    marked = _annotate(image_b64, x, y, normalized=normalized, color=color, ring=ring)
    return marked.base64


def mark_dot(serial: str, x: float, y: float, normalized: bool = True) -> dict:
    """截图并在坐标处画红点，返回标记后的图片、帧标识与像素坐标；点击前用它确认坐标。

    Args:
        serial: 设备序列号
        x: 横坐标，normalized=True 时为 0~1
        y: 纵坐标，normalized=True 时为 0~1
        normalized: 坐标是否为归一化坐标，默认 True

    Returns:
        成功为 {"image": {"base64", "media_type"}, "summary": {"token", "x", "y"}}，
        `token` 可在 90 秒内交给点击类工具复用这一帧；失败为 {"error": 说明}。
    """
    try:
        shot_b64 = _screenshot_b64(serial)
        marked = _annotate(shot_b64, x, y, normalized=bool(normalized), color="red", ring="white")
    except Exception as exc:  # noqa: BLE001 - 设备/图片侧失败一律转可读结论
        agent_event_log.warning(f"坐标标记失败：{exc}")
        return {"error": f"标记失败：{exc}"}
    token = _frame_cache.put(
        serial,
        width=marked.width,
        height=marked.height,
        point_x=marked.x,
        point_y=marked.y,
        image_b64=shot_b64,
        media_type=marked.media_type,
    )
    return {
        "image": {"base64": marked.base64, "media_type": marked.media_type},
        "summary": {"token": token, "x": marked.x, "y": marked.y},
    }


def build_img_b64_tools() -> dict[str, Callable[..., Any]]:
    """按固定顺序产出图片标记工具函数表。"""
    impls = {"mark_dot": mark_dot}
    return {name: impls[name] for name in _TOOL_ORDER}


def img_b64_tool_specs() -> list[ToolSpec]:
    """按工具函数表产出 `ToolSpec` 列表（只读；装配给执行角色的常驻组）。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=name in _READ_ONLY,
            auto_allow=True,
        )
        for name, func in build_img_b64_tools().items()
    ]
