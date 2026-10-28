"""
python -m 调试路径: engines.agents.tools.tool_img_b64

本模块的业务功能如下：
1. mark_dot: 平台工具，截取设备当前屏幕并在坐标处画红点，返回标记后的图片。
2. mark_dot_b64: 纯函数，在 base64 图片上画圆点，base64 进、base64 出。
3. build_img_b64_tools / img_b64_tool_specs: 工具函数表与 `ToolSpec` 产出。

执行模型先用它核对点击坐标，确认红点落在目标上后再执行点击；图片不落盘。
"""

from __future__ import annotations

import base64
import io

from contextlib import contextmanager
from typing import Any, Callable

from PIL import Image, ImageDraw

from engines.device.action import Screenshot, System, open_device
from utils.logs import agent_event_log

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


def _annotate(
    image_b64: str,
    x: float,
    y: float,
    *,
    normalized: bool,
    color: str,
    ring: str,
) -> tuple[str, str]:
    """解码、画圆点、再编码；返回 (标记后的 base64, media_type)。

    Args:
        image_b64: 原始图片 base64。
        x: 横坐标。
        y: 纵坐标。
        normalized: 坐标是否为归一化坐标。
        color: 圆点颜色。
        ring: 外圈描边颜色。

    Returns:
        (标记后的 base64, 图片 media_type)，编码格式沿用输入图片。

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
    return base64.b64encode(buf.getvalue()).decode("ascii"), _media_type(fmt)


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
    marked, _media = _annotate(image_b64, x, y, normalized=normalized, color=color, ring=ring)
    return marked


def mark_dot(serial: str, x: float, y: float, normalized: bool = True) -> dict:
    """截图并在坐标处画红点，返回标记后的图片；点击前用它确认坐标是否落在目标元素上。
    Args:
        serial: 设备序列号
        x: 横坐标，normalized=True 时为 0~1
        y: 纵坐标，normalized=True 时为 0~1
        normalized: 坐标是否为归一化坐标，默认 True

    Returns:
        成功为 {"image": {"base64", "media_type"}}；失败为 {"error": 说明}。
    """
    try:
        shot_b64 = _screenshot_b64(serial)
        marked, media_type = _annotate(
            shot_b64, x, y, normalized=bool(normalized), color="red", ring="white"
        )
    except Exception as exc:  # noqa: BLE001 - 设备/图片侧失败一律转可读结论
        agent_event_log.warning(f"坐标标记失败：{exc}")
        return {"error": f"标记失败：{exc}"}
    return {"image": {"base64": marked, "media_type": media_type}}


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
