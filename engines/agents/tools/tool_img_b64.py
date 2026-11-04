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

from PIL import Image, ImageDraw, ImageFont

from engines.device.action import Screenshot, System, open_device
from utils.logs import agent_event_log

from . import tool_frame_cache as _frame_cache
from .tool_base import ToolSpec

__all__ = [
    "annotate_points",
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


def _image_size(image_b64: str) -> tuple[int, int]:
    """图片像素尺寸。

    Args:
        image_b64: 原始图片 base64，可带 data URI 前缀。

    Returns:
        (宽, 高)。

    Raises:
        ValueError: base64 非法，或图片无法解码。
    """
    raw = _decode(image_b64)
    try:
        with Image.open(io.BytesIO(raw)) as src:
            width, height = src.size
    except (OSError, ValueError) as exc:
        raise ValueError(f"image_b64 不是可识别的图片：{exc}") from exc
    return width, height


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
        points: 已标记的点，序号 = 下标 + 1；单点标记时长度为 1。
    """

    base64: str
    media_type: str
    width: int
    height: int
    points: tuple[tuple[int, int], ...]


def _label_font(short_side: int):
    """按图片短边算序号字号；Pillow 版本不支持带尺寸默认字体时退回默认字号。

    Args:
        short_side: 图片短边像素。

    Returns:
        可用于 `ImageDraw.text` 的字体对象。
    """
    size = max(18, int(short_side * 0.035))
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _render(
    image_b64: str,
    points: tuple[tuple[int, int], ...],
    *,
    color: str = "red",
    ring: str = "white",
    path: bool = False,
) -> _Marked:
    """解码、在每个点画圆点（多点时带序号）、再编码。

    Args:
        image_b64: 原始图片 base64，可带 data URI 前缀。
        points: 要标记的像素坐标点，序号 = 下标 + 1。
        color: 圆点填充色。
        ring: 圆点外圈与序号描边色。
        path: 是否把前两个点连成带箭头的轨迹（拖动核对用）。

    Returns:
        标记结果：标记后的 base64、media_type 与图片尺寸。

    Raises:
        ValueError: base64 非法，或图片无法解码。
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
    radius = max(4, int(min(width, height) * _DOT_RATIO))
    ring_width = max(2, radius // 3)
    draw = ImageDraw.Draw(img)
    font = _label_font(min(width, height))
    numbered = len(points) > 1
    if path and len(points) >= 2:
        start, end = points[0], points[1]
        draw.line((start, end), fill=ring, width=max(4, radius))
        draw.line((start, end), fill=color, width=max(2, radius // 2))
        _draw_arrow_head(draw, start, end, radius, color, ring)
    for index, (cx, cy) in enumerate(points, start=1):
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
        if numbered:
            draw.text(
                (cx + radius, max(cy - radius - radius, 0)),
                str(index),
                fill=color,
                font=font,
                stroke_width=max(2, radius // 3),
                stroke_fill=ring,
            )

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
        points=points,
    )


def _draw_arrow_head(
    draw, start: tuple[int, int], end: tuple[int, int], radius: int, color: str, ring: str
) -> None:
    """在轨迹终点画一个箭头，标出拖动方向。

    Args:
        draw: `ImageDraw` 对象。
        start: 起点像素坐标。
        end: 终点像素坐标。
        radius: 圆点半径，箭头尺寸按它放大。
        color: 箭头填充色。
        ring: 箭头描边色。
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux, uy = dx / length, dy / length
    size = max(radius * 2.2, 10.0)
    tip = (end[0], end[1])
    left = (end[0] - ux * size - uy * size * 0.5, end[1] - uy * size + ux * size * 0.5)
    right = (end[0] - ux * size + uy * size * 0.5, end[1] - uy * size - ux * size * 0.5)
    draw.polygon((tip, left, right), fill=color, outline=ring)


def annotate_path(
    image_b64: str,
    points: tuple[tuple[int, int], ...],
    *,
    color: str = "red",
    ring: str = "white",
) -> _Marked:
    """在一张图上画出拖动轨迹：起点 1、终点 2、两点连线与箭头。

    Args:
        image_b64: 原始图片 base64。
        points: 起点与终点的像素坐标，顺序即拖动方向。
        color: 轨迹与圆点填充色。
        ring: 描边色。

    Returns:
        标记结果：标记后的 base64、media_type、图片尺寸与这些点。

    Raises:
        ValueError: base64 非法、图片无法解码，或点少于 2 个。
    """
    if len(points) < 2:
        raise ValueError("拖动轨迹至少需要起点与终点")
    return _render(image_b64, tuple(points), color=color, ring=ring, path=True)


def annotate_points(
    image_b64: str,
    points: tuple[tuple[int, int], ...],
    *,
    color: str = "red",
    ring: str = "white",
) -> _Marked:
    """在一张图上标记多个点；多点时每个点带序号（从 1 起）。

    Args:
        image_b64: 原始图片 base64。
        points: 像素坐标点，序号 = 下标 + 1。
        color: 圆点填充色。
        ring: 圆点外圈与序号描边色。

    Returns:
        标记结果：标记后的 base64、media_type、图片尺寸与这些点。

    Raises:
        ValueError: base64 非法，或图片无法解码。
    """
    if not points:
        raise ValueError("points 不能为空")
    return _render(image_b64, tuple(points), color=color, ring=ring)


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
        color: 圆点颜色（保留参数，实际按红点绘制）。
        ring: 外圈描边颜色（保留参数，实际按白圈绘制）。

    Returns:
        标记结果：标记后的 base64、media_type、图片尺寸与落点像素。

    Raises:
        ValueError: base64 非法、图片无法解码，或像素坐标越界。
    """
    width, height = _image_size(image_b64)
    cx, cy = _point(x, y, width, height, normalized)
    return _render(image_b64, ((cx, cy),), color=color, ring=ring)


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


def mark_dot(
    serial: str,
    x: float,
    y: float,
    normalized: bool = True,
    x2: float | None = None,
    y2: float | None = None,
) -> dict:
    """截图并在坐标处画红点；给了终点时改画起点→终点的拖动轨迹。

    点击前用它确认点击位置；拖动前用它确认起点落在目标列/滑块上、终点方向与距离合适。

    Args:
        serial: 设备序列号
        x: 横坐标，normalized=True 时为 0~1
        y: 纵坐标，normalized=True 时为 0~1
        normalized: 坐标是否为归一化坐标，默认 True
        x2: 拖动终点的横坐标，口径同 x；与 y2 同时给出时按轨迹绘制
        y2: 拖动终点的纵坐标，口径同 y

    Returns:
        成功为 {"image": {"base64", "media_type"}, "summary": {"token", "x", "y"}}；
        画轨迹时额外带 "x2" / "y2"。`token` 可在 90 秒内交给点击或拖动工具复用这一帧；
        失败为 {"error": 说明}。
    """
    drawing_path = x2 is not None and y2 is not None
    try:
        shot_b64 = _screenshot_b64(serial)
        if drawing_path:
            width, height = _image_size(shot_b64)
            start = _point(x, y, width, height, bool(normalized))
            end = _point(float(x2), float(y2), width, height, bool(normalized))
            marked = annotate_path(shot_b64, (start, end))
        else:
            marked = _annotate(
                shot_b64, x, y, normalized=bool(normalized), color="red", ring="white"
            )
    except Exception as exc:  # noqa: BLE001 - 设备/图片侧失败一律转可读结论
        agent_event_log.warning(f"坐标标记失败：{exc}")
        return {"error": f"标记失败：{exc}"}
    token = _frame_cache.put(
        serial,
        width=marked.width,
        height=marked.height,
        points=marked.points,
        image_b64=shot_b64,
        media_type=marked.media_type,
    )
    x_px, y_px = marked.points[0]
    summary: dict[str, int | str] = {"token": token, "x": x_px, "y": y_px}
    if drawing_path and len(marked.points) > 1:
        summary["x2"], summary["y2"] = marked.points[1]
    return {
        "image": {"base64": marked.base64, "media_type": marked.media_type},
        "summary": summary,
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
