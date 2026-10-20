"""
调试运行入口：python -m engines.device.action

模块说明：
设备动作封装模块，提供设备连接、信息查询、控制功能。

类功能简介：
1. System: 系统声明 + 各系统实现类解析。
2. DeviceConnection: 设备连接：连接 / 断开 / 存活探测 / 重连。
3. DeviceInfo: 设备信息查询（只读，不产生副作用）。
4. DeviceControl: 设备控制：动作方法名统一，三端实现 MUST NOT 各创别名。
5. Click: 点击动作：坐标 / 图像两种方式，各自独立函数。
6. LongClick: 长按动作：坐标 / 图像两种方式，各自独立函数。
7. Swipe: 滑动动作：按方向 / 按坐标两种方式，各自独立函数。
8. Drag: 拖动动作：按归一化起终点拖动。

9. DeviceConnection
10. DeviceInfo
11. DeviceControl

"""

from __future__ import annotations

import base64
import importlib

from abc import ABC, abstractmethod

from utils.logs import device_log

__all__ = [
    "AppControl",
    "Click",
    "DeviceConnection",
    "DeviceControl",
    "DeviceInfo",
    "Drag",
    "InputText",
    "LongClick",
    "PressKey",
    "Screenshot",
    "Swipe",
    "System",
    "EngineConnectError",
    "SystemNotSupported",
    "open_device",
]


class EngineConnectError(RuntimeError):
    """设备连接失败。"""


class SystemNotSupported(RuntimeError):
    """目标系统尚未实现（IOS / WINDOWS 为预留位）。"""


class System:
    """系统声明 + 各系统实现类解析。

    实现类路径按「三类」分别登记；未登记或值为 None 即尚未实现。
    """

    ANDROID = "android"
    IOS = "ios"
    WINDOWS = "windows"
    ALL: tuple[str, ...] = (ANDROID, IOS, WINDOWS)

    _CONNECTION: dict[str, str | None] = {
        ANDROID: "engines.device.android.android_device.AndroidConnection",
        IOS: None,
        WINDOWS: None,
    }
    _INFO: dict[str, str | None] = {
        ANDROID: "engines.device.android.android_device.AdbInfo",
        IOS: None,
        WINDOWS: None,
    }
    _CONTROL: dict[str, str | None] = {
        ANDROID: "engines.device.android.android_device.AndroidControl",
        IOS: None,
        WINDOWS: None,
    }

    @classmethod
    def available(cls) -> list[str]:
        """已实现的系统列表。"""
        return [name for name in cls.ALL if cls._CONTROL.get(name)]

    @classmethod
    def _resolve(cls, table: dict[str, str | None], system: str) -> type:
        name = str(system or "").strip().lower()
        if name not in cls.ALL:
            raise SystemNotSupported(f"未知系统 {system!r}；可选：{list(cls.ALL)}")
        path = table.get(name)
        if not path:
            raise SystemNotSupported(
                f"{name} 系统尚未实现（当前已实现：{', '.join(cls.available())}）"
            )
        module_path, _, attr = path.rpartition(".")
        module = importlib.import_module(module_path)
        return getattr(module, attr)

    @classmethod
    def connection(cls, system: str) -> type:
        """该系统的连接实现类。"""
        return cls._resolve(cls._CONNECTION, system)

    @classmethod
    def info(cls, system: str) -> type:
        """该系统的信息查询实现类。"""
        return cls._resolve(cls._INFO, system)

    @classmethod
    def control(cls, system: str) -> type:
        """该系统的控制实现类。"""
        return cls._resolve(cls._CONTROL, system)


# ══════════════════════════════════════════════════════════════════════
# 方法名契约（三端实现必须一致；改名即违约）
# ══════════════════════════════════════════════════════════════════════


class DeviceConnection(ABC):
    """设备连接：连接 / 断开 / 存活探测 / 重连。"""

    @abstractmethod
    def connect(self, serial: str, addr: str = "") -> None:
        """建立连接（addr 为空时用 serial，无线设备传 IP:port）。"""

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接。"""


class DeviceInfo(ABC):
    """设备信息查询（只读，不产生副作用）。"""

    @abstractmethod
    def screen_size(self) -> tuple[int, int]:
        """屏幕分辨率 (宽, 高)。"""

    @abstractmethod
    def current_app(self) -> dict:
        """当前前台应用（package / activity / pid）。"""

    @abstractmethod
    def packages(self, query: str = "") -> list[str]:
        """已安装包名列表（可按关键词收窄）。"""

    @abstractmethod
    def connected_devices(self) -> list[str]:
        """当前已连接的设备标识列表。"""

    @abstractmethod
    def hierarchy_xml(self) -> str:
        """页面层级原始 XML（解析归算法层）。"""


class DeviceControl(ABC):
    """设备控制：动作方法名统一，三端实现 MUST NOT 各创别名。"""

    # ── 点击 ──
    @abstractmethod
    def click_coord(self, x: int, y: int) -> None:
        """按设备像素坐标点击。"""

    @abstractmethod
    def click_img(self, nx: float, ny: float) -> tuple[int, int]:
        """按图像定位点击（归一化坐标，0~1）；返回实际点击的像素坐标。"""

    # ── 长按 ──
    @abstractmethod
    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        """按像素坐标长按。"""

    @abstractmethod
    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> tuple[int, int]:
        """按图像定位长按（归一化坐标）；返回实际按下的像素坐标。"""

    # ── 滑动 / 拖动 ──
    @abstractmethod
    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        """按方向滑动（up / down / left / right）。"""

    @abstractmethod
    def swipe_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        """按像素起终点滑动。"""

    @abstractmethod
    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        """按归一化起终点拖动。"""

    # ── 输入 / 按键 ──
    @abstractmethod
    def input_text(self, text: str, clear_first: bool = True) -> None:
        """向当前输入框输入文本。"""

    @abstractmethod
    def press_key(self, key: str = "back") -> None:
        """按系统按键（back / home 等）。"""

    # ── 截图 / 应用 ──
    @abstractmethod
    def screenshot_bytes(self) -> bytes:
        """设备当前屏幕的原始图片字节；编码格式由实现自述（screenshot_media_type，缺省按 JPEG）。"""

    def screenshot_b64(self) -> str:
        """设备当前屏幕的 base64；由 `screenshot_bytes` 统一编码，实现侧不必各写一遍。"""
        return base64.b64encode(self.screenshot_bytes()).decode("ascii")

    @abstractmethod
    def app_start(self, package: str) -> None:
        """启动应用。"""

    @abstractmethod
    def app_stop(self, package: str) -> None:
        """停止应用。"""


# ══════════════════════════════════════════════════════════════════════
# 动作类（一类一动作，多方式，每方式一个独立函数）
# ══════════════════════════════════════════════════════════════════════


class Click:
    """点击动作：坐标 / 图像两种方式，各自独立函数；只回传实际点击的像素坐标。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_coord(self, x: int, y: int) -> dict:
        self._control.click_coord(int(x), int(y))
        return {"x": int(x), "y": int(y)}

    def by_img(self, nx: float, ny: float) -> dict:
        x, y = self._control.click_img(float(nx), float(ny))
        return {"x": int(x), "y": int(y)}


class LongClick:
    """长按动作：坐标 / 图像两种方式，各自独立函数；只回传实际按下的像素坐标。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_coord(self, x: int, y: int, duration: float = 0.8) -> dict:
        self._control.long_click_coord(int(x), int(y), float(duration))
        return {"x": int(x), "y": int(y)}

    def by_img(self, nx: float, ny: float, duration: float = 0.8) -> dict:
        x, y = self._control.long_click_img(float(nx), float(ny), float(duration))
        return {"x": int(x), "y": int(y)}


class Swipe:
    """滑动动作：按方向 / 按坐标两种方式，各自独立函数；不回传内容，由调用方补动作时间。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_direction(self, direction: str = "up", distance: int = 500) -> dict:
        self._control.swipe(str(direction or "up"), int(distance or 500))
        return {}

    def by_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> dict:
        self._control.swipe_coord(int(x1), int(y1), int(x2), int(y2), float(duration))
        return {}


class Drag:
    """拖动动作：按归一化起终点拖动；不回传内容，由调用方补动作时间。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_ratio(self, nx1: float, ny1: float, nx2: float, ny2: float) -> dict:
        self._control.drag(float(nx1), float(ny1), float(nx2), float(ny2))
        return {}


class InputText:
    """输入动作：向当前输入框输入文本；不回传内容，由调用方补动作时间。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_text(self, text: str, clear_first: bool = True) -> dict:
        self._control.input_text(str(text or ""), bool(clear_first))
        return {}


class PressKey:
    """按键动作：按系统按键（默认返回键）；不回传内容，由调用方补动作时间。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def by_key(self, key: str = "back") -> dict:
        self._control.press_key(str(key or "back"))
        return {}

    def back(self) -> dict:
        return self.by_key("back")


class AppControl:
    """应用动作：启动 / 停止；回传包名与动作，前后前台应用由调用方补。"""

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def start(self, package: str) -> dict:
        self._control.app_start(str(package))
        return {"package": str(package), "action": "start_app"}

    def stop(self, package: str) -> dict:
        self._control.app_stop(str(package))
        return {"package": str(package), "action": "stop_app"}


class Screenshot:
    """截图动作：截取屏幕，产出无损图片的 base64 与格式（不落盘）。"""

    # 截图编码口径：格式由控制实现自述（缺省按 JPEG）；base64 由设备原始字节一次编出，不转码
    MODEL_MEDIA_TYPE = "image/jpeg"

    def __init__(self, control: DeviceControl) -> None:
        self.log = device_log
        self._control = control

    def capture(self) -> dict:
        """截屏，返回无损图片的 base64 与格式；不写任何文件。

        Returns:
            {"image_base64", "media_type"}；base64 是设备返回的原始字节编出的，
            与模型看到的是同一份像素，中间不做二次编码。

        Raises:
            RuntimeError: 控制实现截屏失败或返回的不是图片。
        """
        raw = self._control.screenshot_bytes()
        # 控制实现可声明自己的截图格式（纯 adb 给无损 PNG）；未声明时按 u2 的 JPEG 口径。
        return {
            "image_base64": base64.b64encode(raw).decode("ascii"),
            "media_type": getattr(self._control, "screenshot_media_type", self.MODEL_MEDIA_TYPE),
        }


def _android_connection(target: str) -> DeviceConnection:
    """按设备标识建立 Android 连接。无线标识为 ``地址:端口``，否则视为 USB 序列号。"""
    from engines.device.android.android_device import AndroidConnection, AndroidConnectionConfig

    if ":" in target:
        host, port_text = target.rsplit(":", 1)
        try:
            port = int(port_text)
        except ValueError as exc:
            raise EngineConnectError(f"无线端口无效：{target}") from exc
        config = AndroidConnectionConfig(address=host, address_port=port)
    else:
        config = AndroidConnectionConfig(uuid=target)
    connection = AndroidConnection(config)
    connection.connect()
    return connection


def open_device(
    system: str = System.ANDROID,
    serial: str = "",
    addr: str = "",
) -> tuple[DeviceConnection, DeviceInfo, DeviceControl]:
    """打开一个设备：连接 + 信息 + 控制三件套。

    设备标识优先用 ``addr``，为空时用 ``serial``。
    未实现的系统抛 `SystemNotSupported`；连接失败抛 `EngineConnectError`。
    """
    target = str(addr or serial).strip()
    if not target:
        raise EngineConnectError("设备标识不能为空")
    name = str(system or "").strip().lower()
    if name == System.ANDROID:
        connection = _android_connection(target)
    else:
        connection = System.connection(name)()
        connection.connect(target)
    return (
        connection,
        System.info(name)(target),
        System.control(name)(target),
    )
