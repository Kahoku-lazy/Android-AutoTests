"""设备动作登记清单 —— 名字 + 说明书 + 实现引用 + 元数据（纯数据、零框架依赖）。

说明书（描述与 `Args:` 段）是唯一真相源，工具函数的 docstring 由本清单注入；
实现引用是函数名，函数实体在 `tool_device.py`（故本模块不 import 它）。
本模块不 import 任何 AI 框架、设备库或业务 App。
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["CATALOG", "DEVICE_TOOL_NAMES", "DeviceToolEntry", "entry"]


@dataclass(frozen=True)
class DeviceToolEntry:
    """一个设备动作工具的登记项：说明书 + 分派与执行策略。

    Attributes:
        name: 工具名（模型可见；与平台侧同名工具保持一致）。
        description: 说明书正文（描述 + `Args:` 段），注入到工具函数的 docstring。
        impl: 实现函数名（实体在 `tool_device.py`）。
        action: 动作名（对应 `engines/device/action.py` 的动作类；多动作以 `|` 连接）。
        mode: 动作方式名（coord / element / img / direction / ratio / text / key / save），无方式时为空串。
        read_only: 是否只读（只读工具不产生设备副作用）。
        concurrency_safe: 是否可并发执行（写动作串行）。
        auto_allow: 是否自动放行，不走人工确认。
        is_device_action: 是否为设备动作类工具（装配时据此跳过注入清单里的同名条目）。
    """

    name: str
    description: str
    impl: str
    action: str
    mode: str = ""
    read_only: bool = False
    concurrency_safe: bool = False
    auto_allow: bool = True
    is_device_action: bool = field(default=True)


CATALOG: tuple[DeviceToolEntry, ...] = (
    DeviceToolEntry(
        name="screenshot_page",
        impl="screenshot_page",
        action="screenshot",
        mode="save",
        read_only=True,
        concurrency_safe=True,
        description=(
            "截取设备当前屏幕并返回图片（给视觉模型看图）。轻量：仅截图，不 dump/OCR/落库。\n"
            "Args:\n"
            "    serial: 设备序列号\n"
            "    keep_local: True 时在 summary 中回传落盘相对路径/文件名（验收证据用）；\n"
            "        False 时仍截屏给模型看图，但不暴露路径。截图文件始终由引擎落盘。"
        ),
    ),
    DeviceToolEntry(
        name="click_ratio",
        impl="click_ratio",
        action="click",
        mode="img",
        description=(
            "按归一化坐标点击（视觉模型看图后输出相对位置，工具换算成屏幕像素坐标）。\n"
            "Args:\n"
            "    serial: 设备序列号\n"
            "    nx: 横向相对位置 0~1（0=最左，1=最右）\n"
            "    ny: 纵向相对位置 0~1（0=最上，1=最下）"
        ),
    ),
    DeviceToolEntry(
        name="tap_screen",
        impl="tap_screen",
        action="click|long_click",
        mode="coord",
        description=(
            "按像素坐标点击或长按设备屏幕；每次返回 package/activity 用于判断页面是否跳转。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）\n"
            "    mode: click 点击 / long_click 长按\n"
            "    x: 坐标 x（像素）\n"
            "    y: 坐标 y（像素）"
        ),
    ),
    DeviceToolEntry(
        name="xpath_action",
        impl="xpath_action",
        action="click|long_click|exists|get_text",
        mode="element",
        description=(
            "通过 xpath 定位并控制设备元素：检查存在 / 读取文本 / 点击 / 长按。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）\n"
            "    action: 动作类型: exists/get_text/click/long_click\n"
            "    xpath: 元素 xpath 表达式（如 //android.widget.TextView[@text='H6110']）\n"
            "    index: 多匹配时第几个，默认 0。get_text 会列出全部命中并标下标，text 取该下标\n"
            "    timeout: exists 时等待元素出现的秒数，默认 0（立即）"
        ),
    ),
    DeviceToolEntry(
        name="swipe_screen",
        impl="swipe_screen",
        action="swipe",
        mode="direction",
        description=(
            "按方向滑动设备屏幕；每次返回 package/activity 用于判断页面是否跳转。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）\n"
            "    direction: 滑动方向 up/down/left/right，默认 up\n"
            "    distance: 滑动距离，默认 500"
        ),
    ),
    DeviceToolEntry(
        name="drag_ratio",
        impl="drag_ratio",
        action="drag",
        mode="ratio",
        description=(
            "按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）。\n"
            "Args:\n"
            "    serial: 设备序列号\n"
            "    nx1: 起点横向相对位置 0~1（0=最左，1=最右）\n"
            "    ny1: 起点纵向相对位置 0~1（0=最上，1=最下）\n"
            "    nx2: 终点横向相对位置 0~1\n"
            "    ny2: 终点纵向相对位置 0~1"
        ),
    ),
    DeviceToolEntry(
        name="input_text",
        impl="input_text",
        action="input_text",
        mode="text",
        description=(
            "向设备当前输入框输入文本；每次返回 package/activity 用于判断页面是否跳转。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）\n"
            "    text: 要输入的文本\n"
            "    clear_first: 输入前是否清空输入框，默认 True"
        ),
    ),
    DeviceToolEntry(
        name="press_key",
        impl="press_key",
        action="press_key",
        mode="key",
        description=(
            "按设备返回键（BACK）返回上一页；每次返回 package/activity 用于判断页面是否跳转。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）"
        ),
    ),
    DeviceToolEntry(
        name="app_control",
        impl="app_control",
        action="app_start|app_stop",
        description=(
            "启动或停止指定设备上的 App；每次返回 package/activity 用于判断页面是否跳转。\n"
            "Args:\n"
            "    serial: 设备序列号（先 list_devices 查询）\n"
            "    action: start_app 启动 / stop_app 停止\n"
            "    package: 目标 App 包名"
        ),
    ),
)

DEVICE_TOOL_NAMES = frozenset(item.name for item in CATALOG)

_BY_NAME = {item.name: item for item in CATALOG}


def entry(name: str) -> DeviceToolEntry | None:
    """按工具名取登记项；未登记返回 None。"""
    return _BY_NAME.get(str(name or ""))
