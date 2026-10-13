"""引擎侧设备工具：工具函数本体与 `ToolSpec` 产出。

动作经 `engines.device.action` 执行；截图落盘目录由装配期闭包注入。
"""

from __future__ import annotations

import json
import logging

from contextlib import contextmanager
from typing import Any, Callable

from engines.ai.base import ToolSpec
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
from engines.device.logbus import now_stamp

logger = logging.getLogger(__name__)

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

_READ_ONLY = frozenset({"screenshot_page"})
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


def _execute(
    serial: str,
    body: Callable[[Any, Any], dict],
    *,
    side_effect: bool = False,
) -> str:
    """执行一次动作并返回 JSON。连接失败与动作失败分开返回。"""
    stamp = now_stamp() if side_effect else ""
    opened = False
    try:
        with _device(serial) as (info, control):
            opened = True
            payload = dict(body(info, control) or {})
            if payload.get("clicked") is False:
                target = payload.get("value") or payload.get("xpath") or ""
                return _error(f"未命中目标元素：{target}，未执行点击")
            if side_effect:
                payload.update(info.current_app() or {})
                payload["action_time"] = stamp
            return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        if opened:
            logger.warning("设备动作执行失败：%s", exc)
            return _error(f"动作执行失败：{exc}")
        logger.warning("打开设备失败：%s", exc)
        return _error(f"连接设备失败：{exc}")


def click_ratio(serial: str, nx: float, ny: float) -> str:
    """按归一化坐标点击（视觉模型看图后输出相对位置，工具换算成屏幕像素坐标）。
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
    """按像素坐标点击或长按设备屏幕；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        mode: click 点击 / long_click 长按
        x: 坐标 x（像素）
        y: 坐标 y（像素）
    """
    px, py = int(x or 0), int(y or 0)
    kind = "long_click" if str(mode or "").strip() == "long_click" else "click"
    actions = {
        "long_click": lambda info, control: LongClick(control).by_coord(px, py),
        "click": lambda info, control: Click(control).by_coord(px, py),
    }
    return _execute(serial, actions[kind], side_effect=True)


def xpath_action(
    serial: str,
    action: str,
    xpath: str,
    index: int = 0,
    timeout: float = 0,
) -> str:
    """通过 xpath 定位并控制设备元素：检查存在 / 读取文本 / 点击 / 长按。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        action: 动作类型: exists/get_text/click/long_click
        xpath: 元素 xpath 表达式（如 //android.widget.TextView[@text='H6110']）
        index: 多匹配时第几个，默认 0。get_text 会列出全部命中并标下标，text 取该下标
        timeout: exists 时等待元素出现的秒数，默认 0（立即）
    """
    kind = str(action or "").strip()
    target = str(xpath)
    nth = int(index or 0)
    wait = float(timeout or 0)
    table: dict[str, tuple[Callable[[Any, Any], dict], bool]] = {
        "exists": (lambda info, control: {"exists": bool(control.exists(target, wait))}, False),
        "get_text": (
            lambda info, control: control.get_text_matches(target, nth),
            False,
        ),
        "long_click": (
            lambda info, control: LongClick(control).by_element("xpath", target, nth),
            True,
        ),
        "click": (
            lambda info, control: Click(control).by_element("xpath", target, nth),
            True,
        ),
    }
    chosen = table.get(kind)
    if chosen is None:
        return _error(
            f"不支持的 xpath 动作: {kind or '(空)'}；可用：exists / get_text / click / long_click"
        )
    body, side_effect = chosen
    return _execute(serial, body, side_effect=side_effect)


def swipe_screen(serial: str, direction: str = "up", distance: int = 500) -> str:
    """按方向滑动设备屏幕；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        direction: 滑动方向 up/down/left/right，默认 up
        distance: 滑动距离，默认 500
    """
    return _execute(
        serial,
        lambda info, control: Swipe(control).by_direction(
            str(direction or "up"), int(distance or 500)
        ),
        side_effect=True,
    )


def drag_ratio(serial: str, nx1: float, ny1: float, nx2: float, ny2: float) -> str:
    """按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）。
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
    """向设备当前输入框输入文本；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        text: 要输入的文本
        clear_first: 输入前是否清空输入框，默认 True
    """
    return _execute(
        serial,
        lambda info, control: InputText(control).by_text(str(text or ""), bool(clear_first)),
        side_effect=True,
    )


def press_key(serial: str) -> str:
    """按设备返回键（BACK）返回上一页；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
    """
    return _execute(
        serial,
        lambda info, control: PressKey(control).back(),
        side_effect=True,
    )


def app_control(serial: str, action: str, package: str = "") -> str:
    """启动或停止指定设备上的 App；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
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
    return _execute(serial, actions[chosen], side_effect=True)


def build_device_tools(output_root: str = "") -> dict[str, Callable[..., Any]]:
    """按固定顺序产出工具函数表；截图的落盘目录在此闭包注入。"""

    def screenshot_page(serial: str, keep_local: bool = True) -> dict:
        """截取设备当前屏幕并返回图片（给视觉模型看图）。轻量：仅截图，不 dump/OCR/落库。
        Args:
            serial: 设备序列号
            keep_local: True 时在 summary 中回传落盘相对路径/文件名（验收证据用）；
                False 时仍截屏给模型看图，但不暴露路径。截图文件始终由引擎落盘。
        """
        opened = False
        try:
            with _device(serial) as (_info, control):
                opened = True
                shot = Screenshot(control).save(output_root, bool(keep_local))
        except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
            if opened:
                logger.warning("截屏执行失败：%s", exc)
            else:
                logger.warning("截屏连接失败：%s", exc)
            return {"error": f"截屏失败：{exc}"}
        return {
            "image": {"base64": shot["image_base64"], "media_type": shot["media_type"]},
            "summary": {
                "screenshot_path": shot["screenshot_path"],
                "screenshot_name": shot["screenshot_name"],
            },
        }

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


def device_tool_specs(output_root: str = "") -> list[ToolSpec]:
    """按工具函数表产出 `ToolSpec` 列表。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=name in _READ_ONLY,
            auto_allow=True,
        )
        for name, func in build_device_tools(output_root).items()
    ]
