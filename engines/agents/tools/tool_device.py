"""
调试运行入口：python -m engines.agents.tools.tool_device


功能说明：引擎侧设备工具：工具函数本体与 `ToolSpec` 产出。
动作经 `engines.device.action` 执行；截图只回传 base64，不落盘。

"""

from __future__ import annotations

import json
import time

from contextlib import contextmanager
from typing import Any, Callable

from engines.device.action import (
    AppControl,
    Click,
    Drag,
    InputText,
    LongClick,
    PressKey,
    Screenshot,
    Swipe,
    System,
    open_device,
)
from utils.logs import agent_event_log, logging_now_stamp

from .tool_base import ToolSpec

__all__ = [
    "app_control",
    "build_device_tools",
    "click_ratio",
    "device_tool_specs",
    "drag_ratio",
    "input_text",
    "press_key",
    "swipe_screen",
    "tap_screen",
    "xpath_action",
]

_READ_ONLY = frozenset({"screenshot_page", "xpath_action"})
# 取值白名单：非法值一律返回可读错误，不静默退回默认动作（点错、滑错方向的代价更大）
_TAP_MODES = ("click", "long_click")
_SWIPE_DIRECTIONS = ("up", "down", "left", "right")
# 启停 App 后等前台切过来：monkey/force-stop 返回时窗口还没切（实测冷启动约 4s 才出现
# mCurrentFocus），最多等这么久；停止通常是第一次读到就已离开，不会真等。
_APP_SETTLE_TIMEOUT = 6.0
_APP_POLL_INTERVAL = 0.2
_TOOL_ORDER = (
    "screenshot_page",
    "click_ratio",
    "tap_screen",
    "xpath_action",
    "swipe_screen",
    "drag_ratio",
    "input_text",
    "press_key",
    "app_control",
)


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


@contextmanager
def _device(serial: str):
    """打开一台设备，离开时断开。连接失败原样抛出。"""
    connection, info, control = open_device(System.ANDROID, str(serial))
    try:
        yield info, control
    finally:
        connection.disconnect()


def _foreground_app(info: Any) -> dict:
    """读一次前台应用；取不到时 package / activity 均为空串。"""
    app = info.current_app() or {}
    return {
        "package": str(app.get("package") or ""),
        "activity": str(app.get("activity") or ""),
    }


def _wait_app(info: Any, target: str, mode: str) -> dict:
    """等前台切到 `target`（mode=enter）或离开 `target`（mode=leave）。

    启停 App 是异步的：`monkey` / `am force-stop` 返回后窗口还要几百毫秒才切过来，
    立刻读会读到最后一次重绘之前的旧前台，所以这里轮询到切好为止。

    Args:
        info: 设备信息查询对象。
        target: 目标包名。
        mode: enter 等它出现 / leave 等它消失。

    Returns:
        切换后的前台应用；超时返回最后一次读到的值。
    """
    deadline = time.monotonic() + _APP_SETTLE_TIMEOUT
    while True:
        current = _foreground_app(info)
        settled = current["package"] == target if mode == "enter" else current["package"] != target
        if settled or time.monotonic() >= deadline:
            return current
        time.sleep(_APP_POLL_INTERVAL)


def _execute(
    serial: str,
    body: Callable[[Any, Any], dict],
    *,
    side_effect: bool = False,
    watch_app: tuple[str, str] | None = None,
) -> str:
    """执行一次动作并返回 JSON。连接失败与动作失败分开返回。

    Args:
        serial: 设备序列号。
        body: 在设备会话里执行的动作，返回要回传给模型的字段。
        side_effect: 有副作用时补 `action_time`（工具调用起始时刻）。
        watch_app: 监控前台切换时传 `(目标包名, enter|leave)`；会额外补
            `before_app` / `after_app`。只有启停 App 需要。

    Returns:
        JSON 字符串；失败时是 {"error": 可读原因}。
    """
    stamp = logging_now_stamp() if (side_effect or watch_app) else ""
    opened = False
    try:
        with _device(serial) as (info, control):
            opened = True
            before = _foreground_app(info) if watch_app else None
            payload = dict(body(info, control) or {})
            if side_effect or watch_app:
                payload["action_time"] = stamp
            if watch_app and before is not None:
                target, mode = watch_app
                payload["before_app"] = before
                payload["after_app"] = _wait_app(info, target, mode)
            return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        if opened:
            agent_event_log.warning(f"设备动作执行失败：{exc}")
            return _error(f"动作执行失败：{exc}")
        agent_event_log.warning(f"打开设备失败：{exc}")
        return _error(f"连接设备失败：{exc}")


def click_ratio(serial: str, nx: float, ny: float) -> str:
    """按归一化坐标点击（视觉模型看图后输出相对位置，工具换算成屏幕像素坐标）；返回实际点击的像素坐标 x、y 与点击时间。
    Args:
        serial: 设备序列号
        nx: 横向相对位置 0~1（0=最左，1=最右）
        ny: 纵向相对位置 0~1（0=最上，1=最下）
    """
    return _execute(
        serial,
        lambda info, control: Click(control).by_img(float(nx), float(ny)),
        side_effect=True,
    )


def tap_screen(serial: str, mode: str = "click", x: int = 0, y: int = 0) -> str:
    """按像素坐标点击或长按设备屏幕；返回实际点击的像素坐标 x、y 与点击时间。
    mode 只接受 click 与 long_click，其它值直接返回错误，不会退回点击；x/y 不传即为 0，会点到屏幕左上角。
    Args:
        serial: 设备序列号（由上游任务给出）
        mode: click 点击 / long_click 长按；其它值报错
        x: 坐标 x（像素）
        y: 坐标 y（像素）
    """
    chosen = str(mode or "").strip()
    if chosen not in _TAP_MODES:
        return _error(f"不支持的点击模式: {chosen or '(空)'}；可用：click / long_click")
    px, py = int(x or 0), int(y or 0)
    actions = {
        "long_click": lambda info, control: LongClick(control).by_coord(px, py),
        "click": lambda info, control: Click(control).by_coord(px, py),
    }
    return _execute(serial, actions[chosen], side_effect=True)


def _xpath_payload(found: list[dict] | None) -> dict:
    """把查找结果裁成文本与中心坐标。一条扁平返回，多条按下标列出。"""
    hits = [
        {
            "text": str(item.get("text") or ""),
            "x": int(item.get("x") or 0),
            "y": int(item.get("y") or 0),
        }
        for item in (found or [])
    ]
    if len(hits) == 1:
        return {"count": 1, **hits[0]}
    marked = [{"index": index, **hit} for index, hit in enumerate(hits)]
    return {"count": len(hits), "items": marked}


def xpath_action(serial: str, xpath: str) -> str:
    """获取页面 xpath 元素的文本与中心坐标（只查询，不点击）；未命中时 count 为 0、items 为空。
    命中一条时返回 text、x、y，不写下标；多条时 items 按下标 0 起列出。
    拿到坐标后用 tap_screen 的像素 x、y 点击或长按。
    Args:
        serial: 设备序列号（由上游任务给出）
        xpath: 元素 xpath 表达式（如 //android.widget.TextView[@text='H6110']）
    """
    target = str(xpath)
    return _execute(
        serial,
        lambda info, control: _xpath_payload(control.find_xpath(target)),
        side_effect=False,
    )


def swipe_screen(serial: str, direction: str = "up", distance: int = 500) -> str:
    """按方向滑动设备屏幕；只返回动作时间。
    direction 只接受 up/down/left/right，其它值直接返回错误，不会退回 up。
    Args:
        serial: 设备序列号（由上游任务给出）
        direction: 滑动方向 up/down/left/right，默认 up；其它值报错
        distance: 滑动距离（像素），默认 500
    """
    chosen = str(direction or "").strip()
    if chosen not in _SWIPE_DIRECTIONS:
        return _error(f"不支持的滑动方向: {chosen or '(空)'}；可用：up / down / left / right")
    return _execute(
        serial,
        lambda info, control: Swipe(control).by_direction(chosen, int(distance or 500)),
        side_effect=True,
    )


def drag_ratio(serial: str, nx1: float, ny1: float, nx2: float, ny2: float) -> str:
    """按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）；只返回动作时间。
    Args:
        serial: 设备序列号
        nx1: 起点横向相对位置 0~1（0=最左，1=最右）
        ny1: 起点纵向相对位置 0~1（0=最上，1=最下）
        nx2: 终点横向相对位置 0~1
        ny2: 终点纵向相对位置 0~1
    """
    return _execute(
        serial,
        lambda info, control: Drag(control).by_ratio(
            float(nx1), float(ny1), float(nx2), float(ny2)
        ),
        side_effect=True,
    )


def input_text(serial: str, text: str, clear_first: bool = True) -> str:
    """向设备当前输入框输入文本（支持中文等非 ASCII 字符）；只返回动作时间。
    Args:
        serial: 设备序列号（由上游任务给出）
        text: 要输入的文本
        clear_first: 输入前是否清空输入框，默认 True
    """
    return _execute(
        serial,
        lambda info, control: InputText(control).by_text(str(text or ""), bool(clear_first)),
        side_effect=True,
    )


def press_key(serial: str) -> str:
    """按设备返回键（BACK）返回上一页；只返回动作时间。
    Args:
        serial: 设备序列号（由上游任务给出）
    """
    return _execute(
        serial,
        lambda info, control: PressKey(control).back(),
        side_effect=True,
    )


def app_control(serial: str, action: str, package: str = "") -> str:
    """启动或停止指定设备上的 App；返回启动/关闭时间点、包名与启停前后的前台应用。
    action 只接受 start_app / stop_app，其它值报错；两个动作都必须给 package。
    Args:
        serial: 设备序列号（由上游任务给出）
        action: start_app 启动 / stop_app 停止
        package: 目标 App 包名
    """
    chosen = str(action or "").strip()
    if chosen not in ("start_app", "stop_app"):
        return _error(f"不支持的 App 动作: {chosen or '(空)'}；可用：start_app / stop_app")
    if not package:
        return _error(f"{chosen} 需要 package 参数")
    pkg = str(package)
    actions = {
        "stop_app": lambda info, control: AppControl(control).stop(pkg),
        "start_app": lambda info, control: AppControl(control).start(pkg),
    }
    # 启动等它进入前台、关闭等它离开前台，都在 _execute 里带上前后台快照
    mode = "enter" if chosen == "start_app" else "leave"
    return _execute(
        serial,
        actions[chosen],
        side_effect=True,
        watch_app=(pkg, mode),
    )


def build_device_tools() -> dict[str, Callable[..., Any]]:
    """按固定顺序产出工具函数表。"""

    def screenshot_page(serial: str) -> dict:
        """截取设备当前屏幕并返回无损图片（给视觉模型看图）。
        Args:
            serial: 设备序列号
        """
        opened = False
        try:
            with _device(serial) as (_info, control):
                opened = True
                shot = Screenshot(control).capture()
        except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
            if opened:
                agent_event_log.warning(f"截屏执行失败：{exc}")
            else:
                agent_event_log.warning(f"截屏连接失败：{exc}")
            return {"error": f"截屏失败：{exc}"}
        return {"image": {"base64": shot["image_base64"], "media_type": shot["media_type"]}}

    impls = {
        "click_ratio": click_ratio,
        "tap_screen": tap_screen,
        "xpath_action": xpath_action,
        "swipe_screen": swipe_screen,
        "drag_ratio": drag_ratio,
        "input_text": input_text,
        "press_key": press_key,
        "app_control": app_control,
        "screenshot_page": screenshot_page,
    }
    return {name: impls[name] for name in _TOOL_ORDER}


def device_tool_specs() -> list[ToolSpec]:
    """按工具函数表产出 `ToolSpec` 列表。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=name in _READ_ONLY,
            auto_allow=True,
        )
        for name, func in build_device_tools().items()
    ]
