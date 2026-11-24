from __future__ import annotations

import base64
import importlib

from abc import ABC, abstractmethod

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
    pass


class SystemNotSupported(RuntimeError):
    pass


class System:
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
        return cls._resolve(cls._CONNECTION, system)

    @classmethod
    def info(cls, system: str) -> type:
        return cls._resolve(cls._INFO, system)

    @classmethod
    def control(cls, system: str) -> type:
        return cls._resolve(cls._CONTROL, system)


class DeviceConnection(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass


class DeviceInfo(ABC):
    @abstractmethod
    def screen_size(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def current_app(self) -> dict:
        pass

    @abstractmethod
    def packages(self, query: str = "") -> list[str]:
        pass

    @abstractmethod
    def connected_devices(self) -> list[str]:
        pass

    @abstractmethod
    def hierarchy_xml(self) -> str:
        pass


class DeviceControl(ABC):
    @abstractmethod
    def click_coord(self, x: int, y: int) -> None:
        pass

    @abstractmethod
    def click_img(self, nx: float, ny: float) -> tuple[int, int]:
        pass

    @abstractmethod
    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        pass

    @abstractmethod
    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> tuple[int, int]:
        pass

    @abstractmethod
    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        pass

    @abstractmethod
    def swipe_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        pass

    @abstractmethod
    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        pass

    @abstractmethod
    def input_text(self, text: str, clear_first: bool = True) -> None:
        pass

    @abstractmethod
    def press_key(self, key: str = "back") -> None:
        pass

    @abstractmethod
    def screenshot_bytes(self) -> bytes:
        pass

    def screenshot_b64(self) -> str:
        raw = self.screenshot_bytes()
        if not raw:
            raise RuntimeError("截屏失败：控制实现返回了空内容")
        return base64.b64encode(raw).decode("ascii")

    @abstractmethod
    def app_start(self, package: str) -> None:
        pass

    @abstractmethod
    def app_stop(self, package: str) -> None:
        pass


class Click:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_coord(self, x: int, y: int) -> dict:
        self._control.click_coord(int(x), int(y))
        return {"x": int(x), "y": int(y)}

    def by_img(self, nx: float, ny: float) -> dict:
        x, y = self._control.click_img(float(nx), float(ny))
        return {"x": int(x), "y": int(y)}


class LongClick:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_coord(self, x: int, y: int, duration: float = 0.8) -> dict:
        self._control.long_click_coord(int(x), int(y), float(duration))
        return {"x": int(x), "y": int(y)}

    def by_img(self, nx: float, ny: float, duration: float = 0.8) -> dict:
        x, y = self._control.long_click_img(float(nx), float(ny), float(duration))
        return {"x": int(x), "y": int(y)}


class Swipe:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_direction(self, direction: str = "up", distance: int = 500) -> dict:
        self._control.swipe(
            "up" if direction is None else str(direction),
            500 if distance is None else int(distance),
        )
        return {}

    def by_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> dict:
        self._control.swipe_coord(int(x1), int(y1), int(x2), int(y2), float(duration))
        return {}


class Drag:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_ratio(self, nx1: float, ny1: float, nx2: float, ny2: float) -> dict:
        self._control.drag(float(nx1), float(ny1), float(nx2), float(ny2))
        return {}


class InputText:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_text(self, text: str, clear_first: bool = True) -> dict:
        self._control.input_text(str(text or ""), bool(clear_first))
        return {}


class PressKey:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_key(self, key: str = "back") -> dict:
        self._control.press_key(str(key or "back"))
        return {}

    def back(self) -> dict:
        return self.by_key("back")


class AppControl:
    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def start(self, package: str) -> dict:
        self._control.app_start(str(package))
        return {"package": str(package), "action": "start_app"}

    def stop(self, package: str) -> dict:
        self._control.app_stop(str(package))
        return {"package": str(package), "action": "stop_app"}


class Screenshot:
    MODEL_MEDIA_TYPE = "image/jpeg"

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def capture(self) -> dict:
        image = self._control.screenshot_b64()
        return {
            "image_base64": image,
            "media_type": getattr(self._control, "screenshot_media_type", self.MODEL_MEDIA_TYPE),
        }


def _android_connection(target: str) -> DeviceConnection:
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
    target = str(addr or serial).strip()
    if not target:
        raise EngineConnectError("设备标识不能为空")
    name = str(system or "").strip().lower()
    if name == System.ANDROID:
        connection = _android_connection(target)
    else:
        connection = System.connection(name)(target)
        connection.connect()
    try:
        info = System.info(name)(target)
        control = System.control(name)(target)
    except Exception:
        connection.disconnect()
        raise
    return connection, info, control
