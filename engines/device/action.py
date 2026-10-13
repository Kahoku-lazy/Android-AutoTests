"""设备动作层 —— 系统声明 + 三类方法名契约 + 动作类（每个动作一个类，每种方式一个独立函数）。

三层含义：

1. `System`：声明可选系统（ANDROID / IOS / WINDOWS），并按系统解析三类实现类。
   当前只有 ANDROID 有实现；IOS / WINDOWS 是预留选择位，取用时给可读结论（`SystemNotSupported`）。
2. **方法名契约**（`DeviceConnection` / `DeviceInfo` / `DeviceControl`，均为抽象基类）：
   三端实现 MUST 使用契约里的**同一套方法名**（例如图片点击一律 `click_img`，
   禁止某端写成 `click_image`），改名即违约——子类缺任一抽象方法都无法实例化。
3. **动作类**（`Click` / `LongClick` / `Swipe` / `Drag` / `InputText` / `PressKey` /
   `Screenshot` / `AppControl`）：每个类表示一个动作，天然兼容三端（只依赖 `DeviceControl` 契约），
   支持多种方式，**每种方式是一个独立函数**（如点击的 `by_coord` / `by_element` / `by_img`）。

用法：

    connection, info, control = open_device(System.ANDROID, "R5CT62RH88F")
    try:
        Click(control).by_img(0.5, 0.5)
        print(info.screen_size())
    finally:
        connection.disconnect()
"""

from __future__ import annotations

import base64
import importlib
import io
import os

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

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
    "SystemNotSupported",
    "open_device",
    "resolve_output_root",
]


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
        ANDROID: "engines.device.android.android_device.AndroidInfo",
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

    @abstractmethod
    def is_alive(self) -> bool:
        """连接是否仍然可用。"""

    @abstractmethod
    def reconnect(self) -> bool:
        """重建连接；重建失败返回 False 或抛错。"""


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
    def click_element(self, by: str, value: str, index: int = 0) -> bool:
        """按元素定位点击（by：xpath / id / text）；未命中返回 False。"""

    @abstractmethod
    def click_img(self, nx: float, ny: float) -> None:
        """按图像定位点击（归一化坐标，0~1）。"""

    # ── 长按 ──
    @abstractmethod
    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        """按像素坐标长按。"""

    @abstractmethod
    def long_click_element(
        self, by: str, value: str, index: int = 0, duration: float = 0.8
    ) -> bool:
        """按元素定位长按；未命中返回 False。"""

    @abstractmethod
    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> None:
        """按图像定位长按（归一化坐标）。"""

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
    def screenshot(self) -> bytes:
        """截取当前屏幕（字节）。"""

    @abstractmethod
    def screenshot_raw(self) -> bytes:
        """取**原始帧**（无损字节）：供调用方只编一次（给模型 / 落盘证据）。"""

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
    """点击动作：坐标 / 元素（xpath、id、text）/ 图像三种方式，各自独立函数。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_coord(self, x: int, y: int) -> dict:
        self._control.click_coord(int(x), int(y))
        return {"clicked": True, "mode": "coord", "x": int(x), "y": int(y)}

    def by_element(self, by: str = "xpath", value: str = "", index: int = 0) -> dict:
        hit = bool(self._control.click_element(str(by), str(value), int(index)))
        return {"clicked": hit, "mode": "element", "by": by, "value": value, "index": index}

    def by_img(self, nx: float, ny: float) -> dict:
        self._control.click_img(float(nx), float(ny))
        return {"clicked": True, "mode": "img", "nx": float(nx), "ny": float(ny)}


class LongClick:
    """长按动作：坐标 / 元素 / 图像三种方式，各自独立函数。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_coord(self, x: int, y: int, duration: float = 0.8) -> dict:
        self._control.long_click_coord(int(x), int(y), float(duration))
        return {"clicked": True, "mode": "coord", "x": int(x), "y": int(y)}

    def by_element(
        self, by: str = "xpath", value: str = "", index: int = 0, duration: float = 0.8
    ) -> dict:
        hit = bool(
            self._control.long_click_element(str(by), str(value), int(index), float(duration))
        )
        return {"clicked": hit, "mode": "element", "by": by, "value": value, "index": index}

    def by_img(self, nx: float, ny: float, duration: float = 0.8) -> dict:
        self._control.long_click_img(float(nx), float(ny), float(duration))
        return {"clicked": True, "mode": "img", "nx": float(nx), "ny": float(ny)}


class Swipe:
    """滑动动作：按方向 / 按坐标两种方式，各自独立函数。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_direction(self, direction: str = "up", distance: int = 500) -> dict:
        self._control.swipe(str(direction or "up"), int(distance or 500))
        return {"direction": direction, "distance": int(distance or 500)}

    def by_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> dict:
        self._control.swipe_coord(int(x1), int(y1), int(x2), int(y2), float(duration))
        return {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)}


class Drag:
    """拖动动作：按归一化起终点拖动。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_ratio(self, nx1: float, ny1: float, nx2: float, ny2: float) -> dict:
        self._control.drag(float(nx1), float(ny1), float(nx2), float(ny2))
        return {"nx1": float(nx1), "ny1": float(ny1), "nx2": float(nx2), "ny2": float(ny2)}


class InputText:
    """输入动作：向当前输入框输入文本。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_text(self, text: str, clear_first: bool = True) -> dict:
        self._control.input_text(str(text or ""), bool(clear_first))
        return {"text": str(text or ""), "clear_first": bool(clear_first)}


class PressKey:
    """按键动作：按系统按键（默认返回键）。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def by_key(self, key: str = "back") -> dict:
        self._control.press_key(str(key or "back"))
        return {"key": str(key or "back")}

    def back(self) -> dict:
        return self.by_key("back")


class AppControl:
    """应用动作：启动 / 停止。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def start(self, package: str) -> dict:
        self._control.app_start(str(package))
        return {"package": str(package), "action": "start_app"}

    def stop(self, package: str) -> dict:
        self._control.app_stop(str(package))
        return {"package": str(package), "action": "stop_app"}


def resolve_output_root(explicit: str = "") -> str:
    """截图落盘根目录：显式给出 > 环境变量 `ENGINE_DEVICE_SHOT_DIR` > `<当前目录>/temps/engine_shots`。"""
    value = str(explicit or "").strip()
    if value:
        return value
    env_value = os.environ.get("ENGINE_DEVICE_SHOT_DIR", "").strip()
    if env_value:
        return env_value
    return str(Path.cwd() / "temps" / "engine_shots")


# 截图编码口径：给模型的那份**无损、不缩放**（PNG 原尺寸）；落盘证据那份 JPEG 90（给人看）
MODEL_MEDIA_TYPE = "image/png"
LOCAL_JPEG_QUALITY = 90


def millisecond_stamp() -> str:
    """毫秒精度时间戳（文件名用）：`YYYYmmdd_HHMMSS_mmm`。"""
    now = datetime.now()
    return f"{now:%Y%m%d_%H%M%S}_{now.microsecond // 1000:03d}"


def _encode_png(raw: bytes) -> bytes:
    """原始帧字节 → 无损 PNG 字节（不缩放、不有损压缩）。"""
    from PIL import Image

    with Image.open(io.BytesIO(raw)) as img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
    return buf.getvalue()


def _encode_jpeg(raw: bytes, *, quality: int) -> bytes:
    """原始帧字节 → JPEG 字节（仅用于落盘证据）。"""
    from PIL import Image

    with Image.open(io.BytesIO(raw)) as img:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


class Screenshot:
    """截图动作：截取屏幕，产出图片数据与（可选的）本地落盘路径。"""

    def __init__(self, control: DeviceControl) -> None:
        self._control = control

    def full(self) -> bytes:
        """取原始帧字节（无损）。"""
        return self._control.screenshot_raw()

    def save(self, output_root: str = "", keep_local: bool = True) -> dict:
        """截屏，编码图片并按需落盘。

        Args:
            output_root: 落盘根目录（空则用引擎默认目录）。
            keep_local: 是否落盘一份本地图片。

        Returns:
            {"screenshot_path", "screenshot_name", "image_base64", "media_type"}；
            不落盘时路径与文件名为空串。
        """
        raw = self._control.screenshot_raw()
        model_b64 = base64.b64encode(_encode_png(raw)).decode("ascii")
        result = {
            "screenshot_path": "",
            "screenshot_name": "",
            "image_base64": model_b64,
            "media_type": MODEL_MEDIA_TYPE,
        }
        if not keep_local:
            return result
        name = f"capture_{millisecond_stamp()}.jpg"
        shots = Path(resolve_output_root(output_root)) / "inspector" / "shots"
        shots.mkdir(parents=True, exist_ok=True)
        (shots / name).write_bytes(_encode_jpeg(raw, quality=LOCAL_JPEG_QUALITY))
        result["screenshot_path"] = f"inspector/shots/{name}"
        result["screenshot_name"] = name
        return result


def open_device(
    system: str = System.ANDROID,
    serial: str = "",
    addr: str = "",
) -> tuple[DeviceConnection, DeviceInfo, DeviceControl]:
    """打开一个设备：连接 + 信息 + 控制三件套（三端同一套用法）。

    未实现的系统抛 `SystemNotSupported`（附可用系统）；连接失败由连接实现抛错。
    """
    connection = System.connection(system)()
    connection.connect(str(serial), str(addr or ""))
    return (
        connection,
        System.info(system)(connection),
        System.control(system)(connection),
    )
