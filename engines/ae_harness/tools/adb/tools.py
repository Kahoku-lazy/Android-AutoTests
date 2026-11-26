"""
文件名: ➡️ tools.py 🏁
路径: ➡️ engines/ae_harness/tools/adb/tools.py 🏁
模块功能：➡️ adb 设备工具：16 个函数工具与列表装配 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.adb.tools 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. adb_devices: 列出已连接设备。
2. adb_tap: 点击屏幕坐标。
3. adb_swipe: 从一点滑到另一点。
4. adb_long_press: 在一点长按。
5. adb_input_text: 向当前输入框输入 ASCII 文本。
6. adb_press_key: 按一个按键（名字或 keycode）。
7. adb_install: 安装 APK。
8. adb_uninstall: 卸载应用。
9. adb_screen_off: 熄屏。
10. adb_unlock: 唤醒并解除锁屏。
11. adb_screenshot: 截屏，返回图片块与元信息。
12. adb_screenshot_grid: 以粗估点撒环点阵，一次给出多个候选点。
13. adb_dump_ui: 导出当前界面控件（文字、描述、边界）。
14. adb_app_start: 按包名启动应用，可等就绪并同返首屏。
15. adb_app_stop: 按包名强制停止应用。
16. adb_app_state: 查看应用在前台、后台还是未运行。
17. build_adb_tools: 产出工具列表，供创建后挂载。
18. build_adb_readonly_tools: 只读子集，供验收角色使用。
🏁
关联模块：➡️
1. engines.ae_harness.tools.adb.core: 导入 AdbError / list_devices / resolve_serial / run_adb。
🏁
测试：➡️
1. 本模块可直接运行：python -m engines.ae_harness.tools.adb.tools
🏁
"""

from __future__ import annotations

import base64
import json
import re
import time
import xml.etree.ElementTree as ET

from datetime import datetime
from pathlib import Path

from agentscope.message import Base64Source, DataBlock, TextBlock
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool, ToolChunk

from .core import (
    AdbError,
    list_devices,
    resolve_serial,
    run_adb,
    run_adb_bytes,
    screen_size,
)

__all__ = [
    "adb_app_start",
    "adb_app_state",
    "adb_app_stop",
    "adb_devices",
    "adb_dump_ui",
    "adb_input_text",
    "adb_install",
    "adb_long_press",
    "adb_press_key",
    "adb_screen_off",
    "adb_screenshot",
    "adb_screenshot_grid",
    "adb_swipe",
    "adb_tap",
    "adb_unlock",
    "adb_uninstall",
    "build_adb_readonly_tools",
    "build_adb_tools",
]

# 按键名到 keycode；也允许直接传数字。
_KEYCODES = {
    "home": 3,
    "back": 4,
    "call": 5,
    "end_call": 6,
    "volume_up": 24,
    "volume_down": 25,
    "power": 26,
    "camera": 27,
    "enter": 66,
    "delete": 67,
    "menu": 82,
    "notification": 83,
    "search": 84,
    "wakeup": 224,
    "sleep": 223,
}

# 工具统一放行：这是本机调试设备，不需要逐次确认。
_ALLOW = PermissionDecision(behavior=PermissionBehavior.ALLOW, message="adb 调试工具，允许执行")

# 交给模型前把长边压到这个值以内，减少视觉误差与 token。
_SEND_LONG_SIDE = 1024
# 网格图要放得下多个圆环与行列号，用更高的上限。
_GRID_LONG_SIDE = 1024

# 从 dumpsys 的前台行里取包名，形如 com.pkg/.MainActivity。
_PACKAGE_RE = re.compile(r"([A-Za-z][\w.]*)/([\w.$]+)")


def _render(
    data: bytes,
    marks: list[tuple[float, float]] | None = None,
    *,
    style: str = "point",
    grid_size: int = 0,
) -> tuple[bytes, tuple[int, int], tuple[int, int]]:
    """
    缩放截图，可选在图上画出待确认的点。

    Args:
        data: 原始 PNG 字节。
        marks: 归一化坐标列表；为空时只缩放不标注。
        style: 标记形态，point 画空心圆环加序号，ring 画点阵圆环加行列号。
        grid_size: 每边点数；ring 时用于定位行列号。

    Returns:
        (发送用字节, 发送尺寸, 原始尺寸)；缺 Pillow 时原样返回。

    Raises:
        ValueError: 坐标超出 0~1，或点数超过该形态上限。
    """
    try:
        from io import BytesIO

        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return data, (0, 0), (0, 0)

    with Image.open(BytesIO(data)) as opened:
        opened.load()
        image = opened.copy()

    original = image.size
    # 网格点密集，留更高分辨率，圆环与标注才分得开。
    limit = _GRID_LONG_SIDE if marks and len(marks) > 1 else _SEND_LONG_SIDE
    if max(original) > limit:
        scale = limit / max(original)
        size = (
            max(1, round(original[0] * scale)),
            max(1, round(original[1] * scale)),
        )
        image = image.resize(size, Image.LANCZOS)
    else:
        size = original

    if marks:
        _annotate(image, marks, ImageDraw, ImageFont, style=style, grid_size=grid_size)

    buffer = BytesIO()
    # 不开 optimize：实测多花约 300ms 只省 7KB，不划算。
    image.save(buffer, format="PNG")
    return buffer.getvalue(), size, original


def _annotate(
    image: object,
    marks: list[tuple[float, float]],
    draw_mod: object,
    font_mod: object,
    *,
    style: str = "point",
    grid_size: int = 0,
) -> None:
    """
    在图上标出每个待确认的点。

    所有形态都用空心圆环：单点用大环加中心点，多点用小环加序号；
    style 为 ring 时改用点阵圆环并用行列号标注，目标可从环心透出。

    Args:
        image: 已缩放的 PIL 图像。
        marks: 归一化坐标列表。
        draw_mod: PIL.ImageDraw 模块。
        font_mod: PIL.ImageFont 模块。
        style: 标记形态，point 或 ring。
        grid_size: 每边点数；ring 时必填，用于摆放行列号。

    Raises:
        ValueError: 坐标超出 0~1，或点数超过该形态上限。
    """
    limit = 49 if style == "ring" else 25
    if len(marks) > limit:
        raise ValueError(f"marks 最多 {limit} 个点")
    if style == "ring":
        _annotate_rings(image, marks, draw_mod, font_mod, grid_size=grid_size)
        return
    width, height = image.size
    draw = draw_mod.Draw(image)
    dense = len(marks) > 1
    unit = min(width, height)

    if dense:
        radius = max(7, round(unit * 0.012))
        line_width = 3
        font_size = max(16, round(unit * 0.018))
    else:
        radius = max(16, round(unit * 0.022))
        line_width = 5
        font_size = max(18, round(unit * 0.022))

    try:
        font = font_mod.load_default(size=font_size)
    except TypeError:
        font = font_mod.load_default()

    for index, (nx, ny) in enumerate(marks, start=1):
        if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
            raise ValueError(f"marks 第 {index} 个点超出 0~1：nx={nx}, ny={ny}")
        x = nx * (width - 1)
        y = ny * (height - 1)
        box = [x - radius, y - radius, x + radius, y + radius]
        draw.ellipse(box, outline="white", width=line_width + 2)
        draw.ellipse(box, outline="red", width=line_width)
        if not dense:
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill="red")
        draw.text(
            (x + radius + 2, y - radius),
            str(index),
            fill="red",
            font=font,
            stroke_width=2,
            stroke_fill="white",
        )


def _annotate_rings(
    image: object,
    marks: list[tuple[float, float]],
    draw_mod: object,
    font_mod: object,
    *,
    grid_size: int,
) -> None:
    width, height = image.size
    if grid_size < 2 or grid_size * grid_size != len(marks):
        raise ValueError(f"环点阵需要 size² 个点，收到 size={grid_size}、{len(marks)} 个点")
    span_x = abs(marks[grid_size - 1][0] - marks[0][0]) * (width - 1)
    span_y = abs(marks[-1][1] - marks[0][1]) * (height - 1)
    gap_x = span_x / (grid_size - 1)
    gap_y = span_y / (grid_size - 1)
    radius = max(3, min(9, round(min(gap_x, gap_y) * 0.3)))
    font = _label_font(font_mod, max(8, min(14, round(gap_x))))
    draw = draw_mod.Draw(image)
    for nx, ny in marks:
        if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
            raise ValueError(f"marks 超出 0~1：nx={nx}, ny={ny}")
        x = nx * (width - 1)
        y = ny * (height - 1)
        box = [x - radius, y - radius, x + radius, y + radius]
        draw.ellipse(box, outline="white", width=4)
        draw.ellipse(box, outline="red", width=2)
    top = marks[0][1] * (height - 1)
    left = marks[0][0] * (width - 1)
    label_gap = radius + 14
    for col in range(grid_size):
        _label(
            draw,
            font,
            str(col + 1),
            marks[col][0] * (width - 1),
            top - label_gap,
            width,
            height,
            center_x=True,
        )
    for row in range(grid_size):
        label = row * grid_size
        _label(
            draw,
            font,
            str(row + 1),
            left - label_gap,
            marks[label][1] * (height - 1),
            width,
            height,
            center_x=False,
        )


def _label(
    draw: object,
    font: object,
    text: str,
    x: float,
    y: float,
    width: int,
    height: int,
    *,
    center_x: bool,
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    text_w = box[2] - box[0]
    text_h = box[3] - box[1]
    left = x - text_w / 2 if center_x else x - text_w
    left = min(max(1.0, left), width - text_w - 1)
    top = min(max(1.0, y), height - text_h - 2)
    draw.text((left, top), text, fill="red", font=font, stroke_width=1, stroke_fill="white")


def _label_font(font_mod: object, size: int) -> object:
    try:
        return font_mod.load_default(size=size)
    except TypeError:
        return font_mod.load_default()


def _stamp() -> str:
    """
    产出操作时间戳。

    Returns:
        形如 2026-11-13_10-53-12.321 的字符串，毫秒三位。
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def _ok(**payload: object) -> str:
    """
    产出成功结果。

    Args:
        **payload: 动作、坐标等要返回的字段。

    Returns:
        JSON 文本，含 timestamp、status=true 与载荷字段。
    """
    return json.dumps(
        {"timestamp": _stamp(), "status": True, **payload},
        ensure_ascii=False,
    )


def _fail(exc: Exception) -> str:
    """
    产出失败结果。

    Args:
        exc: 捕获到的异常。

    Returns:
        JSON 文本，含 timestamp、status=false 与 error。
    """
    return json.dumps(
        {"timestamp": _stamp(), "status": False, "error": str(exc)},
        ensure_ascii=False,
    )


def adb_devices() -> str:
    """
    列出当前通过 adb 连接的手机，包含序列号、状态、型号。

    Returns:
        JSON 文本：devices 为设备数组；没设备时为空数组。
    """
    try:
        devices = list_devices()
        return _ok(
            count=len(devices),
            devices=[
                {
                    "serial": device.serial,
                    "state": device.state,
                    "model": device.model,
                    "product": device.product,
                }
                for device in devices
            ],
        )
    except AdbError as exc:
        return _fail(exc)


def _normalized_to_px(nx: float, ny: float, width: int, height: int) -> tuple[int, int]:
    """
    把归一化坐标换算成像素坐标。

    Args:
        nx: 横坐标，0~1，0 是屏幕最左，1 是最右。
        ny: 纵坐标，0~1，0 是屏幕最上，1 是最下。
        width: 屏幕宽（像素）。
        height: 屏幕高（像素）。

    Returns:
        (x, y) 像素坐标。

    Raises:
        ValueError: 坐标超出 0~1。
    """
    if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
        raise ValueError(f"归一化坐标必须在 0~1：nx={nx}, ny={ny}")
    return round(nx * (width - 1)), round(ny * (height - 1))


def adb_tap(nx: float, ny: float, serial: str = "") -> str:
    """
    点击屏幕上的一个点。

    Args:
        nx: 横坐标的归一化值，0~1；0 最左，1 最右。
        ny: 纵坐标的归一化值，0~1；0 最上，1 最下。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带归一化坐标与换算后的像素坐标。
    """
    try:
        target = resolve_serial(serial)
        width, height = screen_size(target)
        x, y = _normalized_to_px(nx, ny, width, height)
        run_adb(["shell", "input", "tap", str(x), str(y)], serial=target)
        return _ok(action="tap", serial=target, nx=nx, ny=ny, x=x, y=y)
    except (AdbError, ValueError) as exc:
        return _fail(exc)


def adb_swipe(
    nx1: float,
    ny1: float,
    nx2: float,
    ny2: float,
    duration_ms: int = 300,
    serial: str = "",
) -> str:
    """
    从一点滑到另一点。

    Args:
        nx1: 起点横坐标归一化值，0~1。
        ny1: 起点纵坐标归一化值，0~1。
        nx2: 终点横坐标归一化值，0~1。
        ny2: 终点纵坐标归一化值，0~1。
        duration_ms: 滑动耗时（毫秒），越大越慢。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带归一化起终点、换算后的像素点与耗时。
    """
    try:
        target = resolve_serial(serial)
        width, height = screen_size(target)
        x1, y1 = _normalized_to_px(nx1, ny1, width, height)
        x2, y2 = _normalized_to_px(nx2, ny2, width, height)
        run_adb(
            [
                "shell",
                "input",
                "swipe",
                str(x1),
                str(y1),
                str(x2),
                str(y2),
                str(duration_ms),
            ],
            serial=target,
        )
        return _ok(
            action="swipe",
            serial=target,
            start=[nx1, ny1],
            end=[nx2, ny2],
            px_start=[x1, y1],
            px_end=[x2, y2],
            duration_ms=duration_ms,
        )
    except (AdbError, ValueError) as exc:
        return _fail(exc)


def adb_long_press(nx: float, ny: float, duration_ms: int = 800, serial: str = "") -> str:
    """
    在一点长按。

    Args:
        nx: 横坐标归一化值，0~1。
        ny: 纵坐标归一化值，0~1。
        duration_ms: 按住时长（毫秒），一般 600~1200。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带归一化坐标、像素坐标与按住时长。
    """
    try:
        target = resolve_serial(serial)
        width, height = screen_size(target)
        x, y = _normalized_to_px(nx, ny, width, height)
        run_adb(
            [
                "shell",
                "input",
                "swipe",
                str(x),
                str(y),
                str(x),
                str(y),
                str(duration_ms),
            ],
            serial=target,
        )
        return _ok(
            action="long_press",
            serial=target,
            nx=nx,
            ny=ny,
            x=x,
            y=y,
            duration_ms=duration_ms,
        )
    except (AdbError, ValueError) as exc:
        return _fail(exc)


def _shell_quote(text: str) -> str:
    """
    把文本包成设备 shell 的单引号参数。

    `adb shell` 之后的参数由设备上的 `/system/bin/sh` 解释，
    只替换空格挡不住分号、管道与反引号。

    Args:
        text: 原始文本。

    Returns:
        以单引号包裹、内部单引号已转义的字符串。
    """
    return "'" + text.replace("'", "'\\''") + "'"


def adb_input_text(text: str, serial: str = "") -> str:
    """
    向当前聚焦的输入框输入文本。

    只支持 ASCII；中文需要设备安装 ADBKeyboard 等输入法。

    Args:
        text: 要输入的文本。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带输入内容。
    """
    try:
        if not text.isascii():
            return _fail(ValueError("input text 只支持 ASCII；中文请用设备输入法"))
        target = resolve_serial(serial)
        # 空格换成 %s 是 input text 的转义；再加单引号，避免被设备 shell 当成命令。
        payload = _shell_quote(text.replace(" ", "%s"))
        run_adb(["shell", "input", "text", payload], serial=target)
        return _ok(action="input_text", serial=target, text=text)
    except AdbError as exc:
        return _fail(exc)


def adb_press_key(key: str, serial: str = "") -> str:
    """
    按一个按键，用于返回、主页、电源等。

    Args:
        key: 按键名或数字 keycode。可用名字：home、back、menu、power、
            enter、delete、volume_up、volume_down、wakeup、sleep、
            notification、search、call、end_call、camera。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带实际使用的 keycode。
    """
    try:
        name = key.strip().lower()
        code = _KEYCODES.get(name)
        if code is None:
            if name.isdigit():
                code = int(name)
            else:
                choices = ", ".join(sorted(_KEYCODES))
                return _fail(ValueError(f"未知按键 {key!r}；可用：{choices}，或直接传数字 keycode"))
        target = resolve_serial(serial)
        run_adb(["shell", "input", "keyevent", str(code)], serial=target)
        return _ok(action="press_key", serial=target, key=key, keycode=code)
    except AdbError as exc:
        return _fail(exc)


def adb_install(apk_path: str, serial: str = "") -> str:
    """
    安装一个 APK；已安装时覆盖安装。

    Args:
        apk_path: APK 文件在本机的绝对路径。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带 adb 输出摘要。
    """
    try:
        path = Path(apk_path).expanduser()
        if not path.is_file():
            return _fail(FileNotFoundError(f"APK 不存在：{path}"))
        target = resolve_serial(serial)
        output = run_adb(["install", "-r", str(path)], serial=target, timeout=300)
        return _ok(action="install", serial=target, apk=str(path), output=output)
    except AdbError as exc:
        return _fail(exc)


def adb_uninstall(package: str, serial: str = "") -> str:
    """
    卸载一个应用。

    Args:
        package: 包名，如 com.example.app。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，成功后带 adb 输出摘要。
    """
    try:
        target = resolve_serial(serial)
        output = run_adb(["uninstall", package], serial=target, timeout=120)
        return _ok(action="uninstall", serial=target, package=package, output=output)
    except AdbError as exc:
        return _fail(exc)


_READY_TIMEOUT_S = 12.0
_READY_SETTLE_MS = 1200
_READY_POLL_S = 0.2


def _wait_app_ready(
    serial: str,
    package: str,
    *,
    timeout_s: float,
    settle_ms: int,
) -> dict:
    """
    等应用进入前台并稳定下来。

    判定要同时满足：前台包名等于目标包名；自最后一次前台变化起连续稳定 settle_ms。
    首次采样就已在目标前台时，稳定窗口从首次采样算起，不额外要求变化。

    Args:
        serial: 设备序列号。
        package: 包名。
        timeout_s: 等待上限秒数。
        settle_ms: 稳定窗口毫秒数。

    Returns:
        ready / timed_out / activity / activity_changes / waited_ms / polls 六个字段。
    """
    prefix = f"{package}/"
    begin = time.perf_counter()
    changes: list[str] = []
    polls = 0
    last = ""
    last_change = begin
    while True:
        component = _resumed_component(serial)
        polls += 1
        moment = time.perf_counter()
        if component != last:
            last = component
            last_change = moment
            if component:
                changes.append(component)
        stable_ms = (moment - last_change) * 1000
        waited_ms = round((moment - begin) * 1000)
        if component.startswith(prefix) and stable_ms >= settle_ms:
            return {
                "ready": True,
                "timed_out": False,
                "activity": component,
                "activity_changes": changes,
                "waited_ms": waited_ms,
                "polls": polls,
            }
        if (moment - begin) >= timeout_s:
            return {
                "ready": False,
                "timed_out": True,
                "activity": component,
                "activity_changes": changes,
                "waited_ms": waited_ms,
                "polls": polls,
            }
        time.sleep(_READY_POLL_S)


def adb_app_start(
    package: str,
    serial: str = "",
    wait_ready: bool = True,
    with_screen: bool = False,
    timeout_s: float = _READY_TIMEOUT_S,
    settle_ms: int = _READY_SETTLE_MS,
) -> ToolChunk | str:
    """
    按包名启动应用，默认等到应用就绪再返回。

    用 monkey 拉起 LAUNCHER 入口，不需要知道 Activity 名。

    就绪的判据是「前台包名等于目标包名，且前台 Activity 自最后一次变化起稳定 settle_ms」，
    不是只看包名：实测有启动页的应用会在启动页阶段就已经满足包名匹配。

    wait_ready=False 时拉起即返回，行为与旧版一致。

    with_screen=True 时，就绪后把首屏截图随结果一起返回（JSON 元信息 + 一张图片块），
    可以省掉紧接着的一次截图调用；图片不落盘，长边压到 1024 以内。

    稳定窗口默认 1200 ms：主 Activity 挂载后列表往往还在转圈，600 ms 会拿到「转圈中」的首屏，
    模型仍要补一张截图。

    Args:
        package: 包名，如 com.govee.home。
        serial: 设备序列号；只连一台时留空。
        wait_ready: 是否等到应用就绪；关掉即拉起后立刻返回。
        with_screen: 就绪后是否把首屏截图一起返回。
        timeout_s: 等待上限秒数，默认 12。
        settle_ms: 前台 Activity 的稳定窗口毫秒数，默认 1200。

    Returns:
        成功时：未开 with_screen 为 JSON 文本，开启时为「JSON 元信息 + PNG 图片块」；
        失败时为 JSON 文本。
    """
    try:
        target = resolve_serial(serial)
        output = run_adb(
            [
                "shell",
                "monkey",
                "-p",
                package,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ],
            serial=target,
            timeout=30,
        )
        if "No activities found" in output:
            return _fail(RuntimeError(f"{package} 没有可启动的 LAUNCHER 入口"))
        payload: dict = {
            "action": "app_start",
            "serial": target,
            "package": package,
            "output": output[-200:],
        }
        if wait_ready:
            payload.update(
                _wait_app_ready(
                    target,
                    package,
                    timeout_s=float(timeout_s),
                    settle_ms=int(settle_ms),
                )
            )
        if not with_screen:
            return _ok(**payload)
        return _screenshot_with_points(
            None,
            serial=target,
            with_timing=False,
            action="app_start",
            extra=payload,
        )
    except AdbError as exc:
        return _fail(exc)


def adb_app_stop(package: str, serial: str = "") -> str:
    """
    按包名强制停止应用。

    这是直接杀进程，不是优雅退出；未保存的状态会丢。

    Args:
        package: 包名，如 com.govee.home。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本。
    """
    try:
        target = resolve_serial(serial)
        run_adb(["shell", "am", "force-stop", package], serial=target, timeout=30)
        return _ok(action="app_stop", serial=target, package=package)
    except AdbError as exc:
        return _fail(exc)


def adb_app_state(package: str, serial: str = "") -> str:
    """
    查看应用是在前台、后台，还是没在运行。

    Args:
        package: 包名，如 com.govee.home。
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，带 running、foreground 与当前前台包名。
    """
    try:
        target = resolve_serial(serial)
        front = _front_package(target)
        running = _is_running(target, package)
        return _ok(
            action="app_state",
            serial=target,
            package=package,
            running=running,
            foreground=front == package,
            front_package=front,
        )
    except AdbError as exc:
        return _fail(exc)


def _resumed_component(serial: str) -> str:
    """
    读当前前台组件。

    优先用 mResumedActivity，取不到时退回 mCurrentFocus。

    Args:
        serial: 设备序列号。

    Returns:
        `包名/Activity` 形式的组件串；解析不出来时返回空串。
    """
    text = run_adb(["shell", "dumpsys", "activity", "activities"], serial=serial, timeout=30)
    for keyword in ("mResumedActivity", "mCurrentFocus"):
        for line in text.splitlines():
            if keyword in line:
                match = _PACKAGE_RE.search(line)
                if match:
                    return f"{match.group(1)}/{match.group(2)}"
    return ""


def _front_package(serial: str) -> str:
    """
    读当前前台包名。

    Args:
        serial: 设备序列号。

    Returns:
        包名；解析不出来时返回空串。
    """
    component = _resumed_component(serial)
    return component.split("/", 1)[0] if component else ""


def _is_running(serial: str, package: str) -> bool:
    """
    判断进程是否存在。

    Args:
        serial: 设备序列号。
        package: 包名。

    Returns:
        有 PID 为 True；pidof 返回非零也算没在跑。
    """
    try:
        output = run_adb(["shell", "pidof", package], serial=serial, timeout=15)
    except AdbError:
        return False
    return bool(output.strip())


def adb_screen_off(serial: str = "") -> str:
    """
    让手机熄屏。

    Args:
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本。
    """
    try:
        target = resolve_serial(serial)
        run_adb(["shell", "input", "keyevent", str(_KEYCODES["sleep"])], serial=target)
        return _ok(action="screen_off", serial=target)
    except AdbError as exc:
        return _fail(exc)


def adb_unlock(serial: str = "") -> str:
    """
    唤醒屏幕并解除锁屏（无密码或滑动锁屏时有效）。

    Args:
        serial: 设备序列号；只连一台时留空。

    Returns:
        JSON 文本，带唤醒与解锁两步的结果。
    """
    try:
        target = resolve_serial(serial)
        run_adb(["shell", "input", "keyevent", str(_KEYCODES["wakeup"])], serial=target)
        dismiss = run_adb(["shell", "wm", "dismiss-keyguard"], serial=target)
        return _ok(action="unlock", serial=target, dismiss=dismiss or "done")
    except AdbError as exc:
        return _fail(exc)


def _grid_points(
    nx: float,
    ny: float,
    size: int,
    step: float,
    step_y: float = 0.0,
) -> list[tuple[float, float]]:
    """
    以一点为中心生成方形网格候选点。

    Args:
        nx: 中心横坐标归一化值。
        ny: 中心纵坐标归一化值。
        size: 每边点数，只能是 3、5 或 7。
        step: 相邻点横向间隔（归一化）。
        step_y: 相邻点纵向间隔；0 表示与 step 相同。

    Returns:
        按行优先排列的坐标列表，长度 size²。

    Raises:
        ValueError: size 不是 3/5/7，或步长不为正。
    """
    if size not in (3, 5, 7):
        raise ValueError(f"size 只能是 3、5 或 7，收到 {size}")
    if step <= 0:
        raise ValueError(f"step 必须为正，收到 {step}")
    gap_y = step_y if step_y > 0 else step
    half = (size - 1) / 2
    points: list[tuple[float, float]] = []
    for row in range(size):
        for col in range(size):
            px = min(1.0, max(0.0, nx + (col - half) * step))
            py = min(1.0, max(0.0, ny + (row - half) * gap_y))
            points.append((round(px, 4), round(py, 4)))
    return points


def _marker_style(marker: str) -> str:
    style = (marker or "ring").strip().lower()
    if style == "cross":
        return "ring"
    if style != "ring":
        raise ValueError(f"marker 只能是 ring（cross 已废弃），收到 {marker}")
    return style


def _grid_records(points: list[tuple[float, float]], grid_size: int) -> list[dict]:
    records: list[dict] = []
    for index, (nx, ny) in enumerate(points, start=1):
        record: dict = {"index": index, "nx": nx, "ny": ny}
        if grid_size > 0:
            record["row"] = (index - 1) // grid_size + 1
            record["col"] = (index - 1) % grid_size + 1
        records.append(record)
    return records


def _screenshot_with_points(
    points: list[tuple[float, float]] | None,
    *,
    serial: str,
    with_timing: bool,
    action: str,
    extra: dict | None = None,
    style: str = "point",
    grid_size: int = 0,
) -> ToolChunk | str:
    """
    截屏，可选把待确认的点画上去，再包成图片块。

    Args:
        points: 要标注的归一化坐标；空则不标注。
        serial: 设备序列号。
        with_timing: 是否附带 cost_ms。
        action: 写进元信息的动作名。
        extra: 追加到元信息的字段。
        style: 标记形态，point 或 ring。
        grid_size: 每边点数；大于 0 时返回体补行号与列号。

    Returns:
        ToolChunk 或失败 JSON 文本。
    """
    begin = time.perf_counter()
    try:
        target = resolve_serial(serial)
        data = run_adb_bytes(["exec-out", "screencap", "-p"], serial=target, timeout=60)
        if not data:
            return _fail(RuntimeError("截屏返回空内容"))
        sent, image_size, original = _render(data, points or None, style=style, grid_size=grid_size)
        payload: dict = {
            "timestamp": _stamp(),
            "status": True,
            "action": action,
            "serial": target,
            "bytes": len(sent),
            "original_bytes": len(data),
            "image": list(image_size),
            "screen": list(original),
            "media_type": "image/png",
        }
        if extra:
            payload.update(extra)
        if points:
            payload["marks"] = _grid_records(points, grid_size)
        if with_timing:
            payload["cost_ms"] = round((time.perf_counter() - begin) * 1000)
        return ToolChunk(
            content=[
                TextBlock(type="text", text=json.dumps(payload, ensure_ascii=False)),
                DataBlock(
                    source=Base64Source(
                        data=base64.b64encode(sent).decode("ascii"),
                        media_type="image/png",
                    ),
                    name="screenshot.png",
                ),
            ],
        )
    except (AdbError, ValueError) as exc:
        return _fail(exc)


def adb_screenshot(
    serial: str = "",
    with_timing: bool = True,
    marks: list[list[float]] | None = None,
) -> ToolChunk | str:
    """
    截取当前屏幕，把画面作为图片块交给模型直接查看。

    不落盘：图像只以 base64 形式随结果返回，长边压到 1024 以内。

    传 marks 时会在图上把每个点画成红圈加序号，用于点击前核对点位是否落在目标上。

    Args:
        serial: 设备序列号；只连一台时留空。
        with_timing: 是否在元信息里带上本次耗时 cost_ms。
        marks: 要标注的归一化坐标，如 [[0.92, 0.07]]；最多 9 个。

    Returns:
        成功时为 ToolChunk：一段 JSON 元信息 + 一张 PNG 图片块；
        失败时为 JSON 文本。
    """
    try:
        points = [(float(item[0]), float(item[1])) for item in (marks or [])]
    except (IndexError, TypeError, ValueError) as exc:
        return _fail(ValueError(f"marks 格式应为 [[nx, ny], ...]：{exc}"))
    return _screenshot_with_points(
        points or None,
        serial=serial,
        with_timing=with_timing,
        action="screenshot",
    )


def adb_screenshot_grid(
    nx: float,
    ny: float,
    size: int = 3,
    step: float = 0.03,
    serial: str = "",
    with_timing: bool = True,
    marker: str = "ring",
    step_y: float = 0.0,
) -> ToolChunk | str:
    """
    以粗估点为中心撒一张环点阵，把候选位置一次画在图上。

    用于粗估点不够准的时候：模型一次看到全部候选点，按行列号挑最贴目标的一个。

    每个候选点画成空心圆环，列号标在首行上方、行号标在首列左侧，目标从环心透出；
    按「第几行第几列」取坐标即可直接点击。cross 为已废弃别名，按 ring 渲染。

    Args:
        nx: 粗估的横坐标归一化值。
        ny: 粗估的纵坐标归一化值。
        size: 每边点数，3、5 或 7；先用 3，没覆盖到再用 5 或 7。
        step: 相邻点横向间隔；3×3 用 0.03，5×5 用 0.02。
        serial: 设备序列号；只连一台时留空。
        with_timing: 是否在元信息里带上本次耗时 cost_ms。
        marker: 标记形态，只接受 ring（缺省）；cross 已废弃，收到时按 ring 渲染。
        step_y: 相邻点纵向间隔；0 表示与 step 相同，方形点阵可传 step 的一半。

    Returns:
        成功时为 ToolChunk：元信息含每个候选点的序号、行号、列号与坐标 + 一张标记图；
        失败时为 JSON 文本。
    """
    try:
        style = _marker_style(marker)
        gap_y = float(step_y)
        if gap_y <= 0:
            gap_y = float(step)
        points = _grid_points(float(nx), float(ny), int(size), float(step), gap_y)
    except (TypeError, ValueError) as exc:
        return _fail(exc)
    return _screenshot_with_points(
        points,
        serial=serial,
        with_timing=with_timing,
        action="screenshot_grid",
        extra={
            "grid": {
                "nx": nx,
                "ny": ny,
                "size": size,
                "step": step,
                "step_y": round(gap_y, 4),
                "marker": style,
            }
        },
        style=style,
        grid_size=int(size),
    )


def adb_dump_ui(serial: str = "", limit: int = 60) -> str:
    """
    导出当前界面的控件信息，包含文字、内容描述、类名、边界、是否可点。

    部分设备（含三星 Android 11）上 uiautomator 被系统限制，dump 不会生成文件；
    这种情况返回 available=false 并附当前焦点窗口，请改用 adb_screenshot。

    Args:
        serial: 设备序列号；只连一台时留空。
        limit: 最多返回多少个有文字或描述的控件。

    Returns:
        JSON 文本，items 为控件数组；不可用时 available 为 false。
    """
    target = ""
    try:
        target = resolve_serial(serial)
        remote = "/sdcard/ae_harness_window_dump.xml"
        # 先删旧文件，否则会把上一次的 dump 当成这一次的结果。
        run_adb(["shell", "rm", "-f", remote], serial=target)
        try:
            run_adb(["shell", "uiautomator", "dump", remote], serial=target, timeout=60)
        except AdbError:
            # 137 等退出码表示 uiautomator 被系统终止，属于设备限制。
            return _dump_unavailable(target)
        try:
            xml_text = run_adb(["shell", "cat", remote], serial=target, timeout=60)
        except AdbError:
            return _dump_unavailable(target)
        if not xml_text.strip():
            return _dump_unavailable(target)
        items = _parse_ui(xml_text, limit=limit)
        return _ok(action="dump_ui", serial=target, count=len(items), items=items)
    except (AdbError, ET.ParseError) as exc:
        return _fail(exc)


def _dump_unavailable(serial: str) -> str:
    """
    uiautomator 不可用时，返回焦点窗口并建议改用截图。

    Args:
        serial: 设备序列号。

    Returns:
        JSON 文本，available 为 false。
    """
    focus = ""
    try:
        text = run_adb(["shell", "dumpsys", "window"], serial=serial, timeout=30)
        for line in text.splitlines():
            if "mCurrentFocus=" in line:
                focus = line.strip()
                break
    except AdbError:
        focus = ""
    return json.dumps(
        {
            "timestamp": _stamp(),
            "status": False,
            "action": "dump_ui",
            "serial": serial,
            "available": False,
            "reason": "uiautomator dump 未生成文件，该设备可能限制了 uiautomator",
            "focus": focus,
            "hint": "改用 adb_screenshot 看图",
        },
        ensure_ascii=False,
    )


def _parse_ui(xml_text: str, *, limit: int) -> list[dict]:
    """
    从 UI dump 里挑出有文字或内容描述的控件。

    Args:
        xml_text: uiautomator dump 出来的 XML 文本。
        limit: 最多返回多少条。

    Returns:
        控件数组，每项含 text、desc、class、bounds、clickable。
    """
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    for node in root.iter("node"):
        text = (node.get("text") or "").strip()
        desc = (node.get("content-desc") or "").strip()
        if not text and not desc:
            continue
        items.append(
            {
                "text": text,
                "desc": desc,
                "class": (node.get("class") or "").rsplit(".", 1)[-1],
                "bounds": node.get("bounds") or "",
                "clickable": node.get("clickable") == "true",
            }
        )
        if len(items) >= limit:
            break
    return items


def build_adb_tools(*, include_devices: bool = True) -> list[FunctionTool]:
    """
    产出 adb 工具，供创建后逐个挂到 Agent。

    Args:
        include_devices: 是否包含列出设备的工具；平台已指定设备时应传 False。

    Returns:
        FunctionTool 列表，顺序固定。
    """
    tools = [
        FunctionTool(adb_screenshot, is_read_only=True, permission=_ALLOW),
        FunctionTool(adb_screenshot_grid, is_read_only=True, permission=_ALLOW),
        FunctionTool(adb_dump_ui, is_read_only=True, permission=_ALLOW),
        FunctionTool(adb_tap, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_swipe, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_long_press, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_input_text, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_press_key, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_install, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_uninstall, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_app_start, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_app_stop, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_app_state, is_read_only=True, permission=_ALLOW),
        FunctionTool(adb_screen_off, is_concurrency_safe=False, permission=_ALLOW),
        FunctionTool(adb_unlock, is_concurrency_safe=False, permission=_ALLOW),
    ]
    if include_devices:
        tools.insert(0, FunctionTool(adb_devices, is_read_only=True, permission=_ALLOW))
    return tools


def build_adb_readonly_tools() -> list[FunctionTool]:
    """
    只读子集：给验收角色用，从工具层面杜绝写操作。

    Returns:
        只含 `is_read_only=True` 的工具，共 5 个。
    """
    return [tool for tool in build_adb_tools() if tool.is_read_only]


if __name__ == "__main__":
    print(adb_devices())  # noqa: T201 - 模块自测入口：仅打印本机设备清单
