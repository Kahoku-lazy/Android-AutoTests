"""引擎侧设备工具：工具函数本体 + 说明书注入 + `ToolSpec` 产出。

说明书取自 `tool_device_catalog.py`；动作经 `engines.device.action` 执行；
截图落盘目录由装配期闭包注入。
"""

from __future__ import annotations

import json
import logging

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

from .tool_device_catalog import CATALOG, entry

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


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


def _execute(
    serial: str,
    body: Callable[[Any, Any], dict],
    *,
    side_effect: bool = False,
) -> str:
    """在设备上执行一次动作。

    Args:
        serial: 设备 serial。
        body: 动作体，接收 (info, control)。
        side_effect: 是否为产生副作用的动作；为真时在返回里附动作时刻与当前前台应用。

    Returns:
        JSON 字符串；未命中目标或执行异常时返回带 error 键的 JSON。
    """
    stamp = now_stamp() if side_effect else ""
    try:
        connection, info, control = open_device(System.ANDROID, str(serial))
    except Exception as exc:  # noqa: BLE001 - 连接失败也要给可读结论
        logger.warning("打开设备失败：%s", exc)
        return _error(f"连接设备失败：{exc}")
    try:
        payload = dict(body(info, control) or {})
        if payload.get("clicked") is False:
            target = payload.get("value") or payload.get("xpath") or ""
            return _error(f"未命中目标元素：{target}，未执行点击")
        if side_effect:
            payload.update(info.current_app() or {})
            payload["action_time"] = stamp
        return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        logger.warning("设备动作执行失败：%s", exc)
        return _error(f"动作执行失败：{exc}")
    finally:
        connection.disconnect()


def click_ratio(serial: str, nx: float, ny: float) -> str:
    return _execute(
        serial,
        lambda info, control: Click(control).by_img(float(nx), float(ny)),
        side_effect=True,
    )


def tap_screen(serial: str, mode: str = "click", x: int = 0, y: int = 0) -> str:
    if str(mode or "").strip() == "long_click":
        return _execute(
            serial,
            lambda info, control: LongClick(control).by_coord(int(x or 0), int(y or 0)),
            side_effect=True,
        )
    return _execute(
        serial,
        lambda info, control: Click(control).by_coord(int(x or 0), int(y or 0)),
        side_effect=True,
    )


def xpath_action(
    serial: str,
    action: str,
    xpath: str,
    index: int = 0,
    timeout: float = 0,
) -> str:
    kind = str(action or "").strip()
    if kind == "exists":
        return _execute(
            serial,
            lambda info, control: {"exists": bool(control.exists(str(xpath), float(timeout or 0)))},
        )
    if kind == "get_text":
        return _execute(
            serial,
            lambda info, control: control.get_text_matches(str(xpath), int(index or 0)),
        )
    if kind == "long_click":
        return _execute(
            serial,
            lambda info, control: LongClick(control).by_element(
                "xpath", str(xpath), int(index or 0)
            ),
            side_effect=True,
        )
    if kind == "click":
        return _execute(
            serial,
            lambda info, control: Click(control).by_element("xpath", str(xpath), int(index or 0)),
            side_effect=True,
        )
    return _error(
        f"不支持的 xpath 动作: {kind or '(空)'}；可用：exists / get_text / click / long_click"
    )


def swipe_screen(serial: str, direction: str = "up", distance: int = 500) -> str:
    return _execute(
        serial,
        lambda info, control: Swipe(control).by_direction(
            str(direction or "up"), int(distance or 500)
        ),
        side_effect=True,
    )


def drag_ratio(serial: str, nx1: float, ny1: float, nx2: float, ny2: float) -> str:
    return _execute(
        serial,
        lambda info, control: Drag(control).by_ratio(
            float(nx1), float(ny1), float(nx2), float(ny2)
        ),
        side_effect=True,
    )


def input_text(serial: str, text: str, clear_first: bool = True) -> str:
    return _execute(
        serial,
        lambda info, control: InputText(control).by_text(str(text or ""), bool(clear_first)),
        side_effect=True,
    )


def press_key(serial: str) -> str:
    return _execute(
        serial,
        lambda info, control: PressKey(control).back(),
        side_effect=True,
    )


def app_control(serial: str, action: str, package: str = "") -> str:
    chosen = str(action or "").strip()
    if chosen not in ("start_app", "stop_app"):
        return _error(f"不支持的 App 动作: {chosen or '(空)'}；可用：start_app / stop_app")
    if not package:
        return _error(f"{chosen} 需要 package 参数")
    if chosen == "stop_app":
        return _execute(
            serial,
            lambda info, control: AppControl(control).stop(str(package)),
            side_effect=True,
        )
    return _execute(
        serial,
        lambda info, control: AppControl(control).start(str(package)),
        side_effect=True,
    )


# 模块级实现（截图例外：它需要闭包注入落盘目录，在 build_device_tools 里生成）
_MODULE_IMPLS: dict[str, Callable[..., Any]] = {
    func.__name__: func
    for func in (
        click_ratio,
        tap_screen,
        xpath_action,
        swipe_screen,
        drag_ratio,
        input_text,
        press_key,
        app_control,
    )
}


def _with_device(serial: str, body: Callable[[Any], dict], *, label: str) -> dict:
    """在设备上执行一次取值。

    Args:
        serial: 设备 serial。
        body: 动作体，接收 control。
        label: 失败文案里的动作名。

    Returns:
        动作体返回值；连接或执行失败时返回 ``{"error": ...}``。
    """
    try:
        connection, _info, control = open_device(System.ANDROID, str(serial))
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        logger.warning("%s连接失败：%s", label, exc)
        return {"error": f"{label}失败：{exc}"}
    try:
        return body(control)
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        logger.warning("%s执行失败：%s", label, exc)
        return {"error": f"{label}失败：{exc}"}
    finally:
        connection.disconnect()


def build_device_tools(output_root: str = "") -> dict[str, Callable[..., Any]]:
    """按登记清单产出工具函数表；截图的落盘目录在此闭包注入。

    Args:
        output_root: 截图落盘根目录；空则用设备引擎默认目录。

    Returns:
        工具名 → 工具函数。
    """

    def screenshot_page(serial: str, keep_local: bool = True) -> dict:
        """截取设备当前屏幕。

        Args:
            serial: 设备 serial。
            keep_local: 是否在引擎侧落盘一份（False 时仍返回图片数据）。

        Returns:
            {"image": {"base64", "media_type"}, "summary": {"screenshot_path", "screenshot_name"}}。
        """
        shot = _with_device(
            serial,
            lambda control: Screenshot(control).save(output_root, bool(keep_local)),
            label="截屏",
        )
        if "error" in shot:
            return shot
        return {
            "image": {"base64": shot["image_base64"], "media_type": shot["media_type"]},
            "summary": {
                "screenshot_path": shot["screenshot_path"],
                "screenshot_name": shot["screenshot_name"],
            },
        }

    screenshot_page.__doc__ = entry("screenshot_page").description
    return {**_MODULE_IMPLS, "screenshot_page": screenshot_page}


def device_tool_specs(output_root: str = "") -> list[ToolSpec]:
    """按登记清单产出引擎自带设备工具的 `ToolSpec` 列表；实现缺失的条目被跳过。"""
    impls = build_device_tools(output_root)
    specs: list[ToolSpec] = []
    for item in CATALOG:
        func = impls.get(item.impl)
        if func is None:
            logger.warning("登记清单里的实现缺失：%s -> %s", item.name, item.impl)
            continue
        specs.append(
            ToolSpec(
                name=item.name,
                handler=func,
                read_only=item.read_only,
                auto_allow=item.auto_allow,
            )
        )
    return specs


def _apply_descriptions() -> None:
    """把登记清单的说明书注入工具函数 docstring。"""
    for item in CATALOG:
        func = _MODULE_IMPLS.get(item.impl)
        if func is not None:
            func.__doc__ = item.description


_apply_descriptions()
