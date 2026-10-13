"""Android 引擎门面 —— 把三个类（连接 / 信息查询 / 控制）组合成既有引擎协议实现。

为什么需要它：上层（`apps/device_pool`、`apps/device_inspector` 与设备引擎注册表）消费的是
`engines/device/base.py::UiEngine` 协议（`open_engine(serial, addr)` 拿一个实现类实例）。
本门面只做**协议方法名 → 三个类的方法名**的转发，不含任何设备逻辑：

    UiEngine.click           -> AndroidControl.click_coord
    UiEngine.click_ratio     -> AndroidControl.click_img
    UiEngine.drag_ratio      -> AndroidControl.drag
    UiEngine.swipe_direction -> AndroidControl.swipe
    UiEngine.get_resolution  -> AndroidInfo.screen_size
    UiEngine.dump_hierarchy_xml -> AndroidInfo.hierarchy_xml

`U2Engine` 是历史类名的别名（注册表与既有测试按此名取用）。
"""

from __future__ import annotations

from engines.device.base import EngineCapabilities

from .android_device import AndroidConnection, AndroidControl, AndroidInfo

__all__ = ["AndroidDevice", "U2Engine"]


class AndroidDevice:
    """Android 引擎门面：实现 engines/device/base.py::UiEngine（组合三个类）。"""

    capabilities = EngineCapabilities(xpath_locate=True, toast_wait=True, ocr=False)

    def __init__(self) -> None:
        self._connection = AndroidConnection()
        self._info = AndroidInfo(self._connection)
        self._control = AndroidControl(self._connection)

    # ── 过渡期句柄（既有兼容壳与 pool 属性经此取值）──

    @property
    def u2(self):
        return self._connection.u2

    @property
    def _u2(self):
        return self._connection.u2

    @_u2.setter
    def _u2(self, value) -> None:
        self._connection.u2 = value

    @property
    def device_info(self) -> dict:
        return dict(self._connection.device_info)

    # ── 连接 ──

    def connect(self, serial: str, addr: str = "", on_log=None):
        self._connection.connect(serial, addr, on_log=on_log)
        return self

    def disconnect(self) -> None:
        self._connection.disconnect()

    def is_alive(self) -> bool:
        return self._connection.is_alive()

    def reconnect(self) -> bool:
        return self._connection.reconnect()

    # ── 信息查询 ──

    def get_resolution(self) -> tuple[int, int]:
        return self._info.screen_size()

    def app_current(self) -> dict:
        return self._info.current_app()

    def list_packages(self, query: str = "") -> list[str]:
        return self._info.packages(query)

    def dump_hierarchy_xml(self) -> str:
        return self._info.hierarchy_xml()

    def shell(self, cmd: str) -> str:
        return self._info.shell(cmd)

    # ── 控制 ──

    def click(self, x: int, y: int) -> None:
        self._control.click_coord(x, y)

    def click_ratio(self, nx: float, ny: float) -> None:
        self._control.click_img(nx, ny)

    def long_click(self, x: int, y: int, duration: float = 0.8) -> None:
        self._control.long_click_coord(x, y, duration)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self._control.swipe_coord(x1, y1, x2, y2, duration)

    def swipe_direction(self, direction: str = "up", distance: int = 500) -> None:
        self._control.swipe(direction, distance)

    def drag_ratio(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        self._control.drag(nx1, ny1, nx2, ny2)

    def input_text(self, text: str, clear_first: bool = True) -> None:
        self._control.input_text(text, clear_first)

    def press_key(self, key: str) -> None:
        self._control.press_key(key)

    def start_app(self, pkg: str) -> None:
        self._control.app_start(pkg)

    def stop_app(self, pkg: str) -> None:
        self._control.app_stop(pkg)

    def screenshot(self) -> bytes:
        return self._control.screenshot()

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        return self._control.screenshot_b64(quality=quality, max_width=max_width)

    def screenshot_file(self, path: str) -> None:
        self._control.screenshot_file(path)

    # ── XPath 与 Toast（既有协议面）──

    def exists(self, xpath: str, timeout: float = 0) -> bool:
        return self._control.exists(xpath, timeout)

    def get_text(self, xpath: str) -> str:
        return self._control.get_text(xpath)

    def get_text_matches(self, xpath: str, index: int = 0) -> dict:
        return self._control.get_text_matches(xpath, index)

    def click_xpath(self, xpath: str, index: int = 0) -> bool:
        return self._control.click_xpath(xpath, index)

    def long_click_xpath(self, xpath: str, index: int = 0, duration: float = 0.8) -> bool:
        return self._control.long_click_xpath(xpath, index, duration)

    def click_text(self, text: str, index: int = 0) -> int:
        hits = self._control.count_element("text", text)
        if hits:
            self._control.click_element("text", text, index)
        return hits

    def wait_toast(self, expected_text: str, timeout: float = 15) -> bool:
        return self._control.wait_toast(expected_text, timeout)

    def get_toast_message(self) -> str:
        return self._control.get_toast_message()

    def reset_toast(self) -> None:
        self._control.reset_toast()

    # ── 三类实现（供只依赖三类契约的调用方直接取用）──

    @property
    def connection(self) -> AndroidConnection:
        return self._connection

    @property
    def info(self) -> AndroidInfo:
        return self._info

    @property
    def control(self) -> AndroidControl:
        return self._control


# 历史类名别名（注册表与既有测试按 U2Engine 取用）
U2Engine = AndroidDevice
