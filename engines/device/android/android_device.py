from __future__ import annotations

import re
import shlex
import subprocess
import time

from dataclasses import dataclass

import uiautomator2 as u2

from engines.device.action import DeviceConnection, DeviceControl, DeviceInfo, EngineConnectError
from utils.adb import adb_binary
from utils.logs import device_log

U2_OP_TIMEOUT = 20

_SUBPROCESS_TIMEOUT = subprocess.TimeoutExpired


def _tune_u2_http_timeout() -> None:
    try:
        from uiautomator2 import base as u2_base
    except ImportError:  # pragma: no cover - 仅 u2 结构变化时触发
        device_log.warning("uiautomator2.base 不可导入，u2 请求超时保持默认值")
        return
    current = getattr(u2_base, "HTTP_TIMEOUT", None)
    if current == U2_OP_TIMEOUT:
        return
    if current is None:  # pragma: no cover - 仅 u2 结构变化时触发
        device_log.warning("uiautomator2 没有 HTTP_TIMEOUT，u2 请求超时保持默认值")
        return
    u2_base.HTTP_TIMEOUT = U2_OP_TIMEOUT


_CONNECTED_KEYWORDS = ("connected", "already", "已连接", "已经连接", "成功")


def _masked_command(args: tuple[str, ...]) -> str:
    parts = list(args)
    if parts and parts[0] == "pair" and len(parts) >= 3:
        parts[-1] = "******"
    return " ".join(parts)


@dataclass(frozen=True)
class AndroidConnectionConfig:
    uuid: str | None = None

    address: str | None = None
    address_port: int | None = None

    pair_port: int | None = None
    pair_code: str | None = None


class AndroidConnection(DeviceConnection):
    def __init__(self, config: AndroidConnectionConfig) -> None:
        self.config = config
        self.log = device_log

    def _check_ip_address(self) -> str:
        if self.config.address is None or self.config.address_port is None:
            raise EngineConnectError("无线连接地址与端口号不能为空，请检查配置")

        return f"{self.config.address}:{self.config.address_port}"

    def _check_pair_code(self) -> tuple[str, str]:
        if (
            self.config.pair_code is None
            or self.config.address is None
            or self.config.pair_port is None
        ):
            raise EngineConnectError("配对码不能为空，请检查配置")

        return f"{self.config.address}:{self.config.pair_port}", self.config.pair_code

    def _run_adb(self, *args: str, stdin=None) -> str:
        shown = _masked_command(args)
        self.log.info(f"执行命令: adb {shown}")
        try:
            result = subprocess.run(
                [adb_binary(), *args],
                capture_output=True,
                text=True,
                timeout=10,
                stdin=stdin,
            )
        except subprocess.TimeoutExpired:
            raise EngineConnectError(f"ADB {shown} timed out (10s). Check network.") from None
        output = f"{result.stdout} + {result.stderr}".strip()
        self.log.info(f"adb {shown} 命令的执行结果是: {output}")
        if result.returncode != 0:
            raise EngineConnectError(f"ADB {shown} failed. {output}")
        return output

    def _adb_connect(self) -> str:
        ip_address = self._check_ip_address()
        self.log.info(f"待连接的设备地址与端口号是: {ip_address}")
        output = self._run_adb("connect", ip_address)
        if not any(word in output for word in _CONNECTED_KEYWORDS):
            raise EngineConnectError(f"ADB connect 失败: {output}")
        return output

    def _adb_disconnect(self) -> None:
        ip_address = self._check_ip_address()
        self.log.info(f"待断开的设备地址与端口号是:{ip_address}")
        self._run_adb("disconnect", ip_address)

    def _adb_pair(self) -> None:
        endpoint, code = self._check_pair_code()
        self.log.info(f"待配对的设备地址与端口号是: {endpoint}")
        self._run_adb("pair", endpoint, code, stdin=subprocess.DEVNULL)

    def _verify_usb(self) -> None:
        output = self._run_adb("-s", str(self.config.uuid), "get-state")
        if "device" not in output:
            raise EngineConnectError(f"USB 设备不在线: {self.config.uuid}")

    def disconnect(self) -> None:
        if self.config.address is None:
            return
        self._adb_disconnect()

    def connect(self) -> None:
        if self.config.pair_code is not None:
            self._adb_pair()
        if self.config.address is not None:
            self._adb_connect()
        elif self.config.uuid:
            self._verify_usb()

    def adb_devices(self) -> str:
        return self._run_adb("devices")


def _bounds_center(bounds: str) -> tuple[int, int]:
    parts = bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")
    if len(parts) != 4 or not all(re.fullmatch(r"-?\d+", part.strip()) for part in parts):
        return 0, 0
    left, top, right, bottom = (int(part) for part in parts)
    return (left + right) // 2, (top + bottom) // 2


_UIDUMP_PATH = "/data/local/tmp/window_dump.xml"
_FAIL_DETAIL_LIMIT = 200


def _failure_detail(stdout: bytes, stderr: bytes) -> str:
    for raw in (stderr, stdout):
        text = " ".join((raw or b"").decode("utf-8", "replace").split())
        if not text:
            continue
        if len(text) > _FAIL_DETAIL_LIMIT:
            return text[:_FAIL_DETAIL_LIMIT] + "…"
        return text
    return "未知错误"


def _quoted_input_text(text: str) -> str:
    return shlex.quote(str(text or "").replace(" ", "%s"))


class AdbChannel:
    def __init__(self, serial: str, executable: str | None = None) -> None:
        self.serial = serial
        self.executable = executable or adb_binary()

    def shell(self, args: list[str], timeout: float = 30.0) -> str:
        return self.shell_bytes(args, timeout).decode("utf-8", "replace")

    def shell_bytes(self, args: list[str], timeout: float = 30.0) -> bytes:
        return self._exec(["shell", *args], timeout)

    def exec_out(self, args: list[str], timeout: float = 30.0) -> bytes:
        return self._exec(["exec-out", *args], timeout)

    def host(self, args: list[str], timeout: float = 10.0) -> str:
        return self._exec(args, timeout, with_serial=False).decode("utf-8", "replace")

    def _exec(self, args: list[str], timeout: float, with_serial: bool = True) -> bytes:
        command = [self.executable]
        if with_serial:
            command += ["-s", self.serial]
        try:
            proc = subprocess.run(command + args, capture_output=True, timeout=timeout)
        except _SUBPROCESS_TIMEOUT as exc:
            raise RuntimeError(f"adb {' '.join(args)} 超时（{timeout}s）") from exc
        if proc.returncode != 0:
            detail = _failure_detail(proc.stdout, proc.stderr)
            raise RuntimeError(f"adb {' '.join(args)} 失败：{detail}")
        return proc.stdout


def _parse_wm_size(text: str) -> tuple[int, int]:
    for pattern in (r"Override size:\s*(\d+)x(\d+)", r"Physical size:\s*(\d+)x(\d+)"):
        match = re.search(pattern, text or "")
        if match:
            return int(match.group(1)), int(match.group(2))
    raise RuntimeError(f"wm size 输出无法解析：{(text or '').strip()}")


_FOCUS_PATTERN = re.compile(r"mCurrentFocus=.*?\s([\w.]+)/([\w.$]+)")
_RESUMED_PATTERN = re.compile(r"mResumedActivity.*?\s([\w.]+)/([\w.$]+)")


def _parse_current_app(text: str) -> dict:
    for pattern in (_FOCUS_PATTERN, _RESUMED_PATTERN):
        match = pattern.search(text or "")
        if match:
            return {"package": match.group(1), "activity": match.group(2)}
    return {"package": "", "activity": ""}


def _parse_packages(text: str, query: str = "") -> list[str]:
    names = [
        line.split(":", 1)[1].strip()
        for line in (text or "").splitlines()
        if line.startswith("package:") and ":" in line
    ]
    keyword = str(query or "").strip().casefold()
    return [name for name in names if keyword in name.casefold()]


def _parse_devices(text: str) -> list[str]:
    serials: list[str] = []
    for line in (text or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


class AdbInfo(DeviceInfo):
    def __init__(self, serial: str) -> None:
        self.adb = AdbChannel(serial)

    def screen_size(self) -> tuple[int, int]:
        return _parse_wm_size(self.adb.shell(["wm", "size"]))

    def current_app(self) -> dict:
        app = _parse_current_app(self.adb.shell(["dumpsys", "window", "displays"]))
        if app["package"]:
            return app
        return _parse_current_app(self.adb.shell(["dumpsys", "activity", "activities"]))

    def packages(self, query: str = "") -> list[str]:
        return _parse_packages(self.adb.shell(["pm", "list", "packages"]), query)

    def connected_devices(self) -> list[str]:
        return _parse_devices(self.adb.host(["devices"]))

    def hierarchy_xml(self) -> str:
        self.adb.shell(["uiautomator", "dump", _UIDUMP_PATH])
        return self.adb.shell(["cat", _UIDUMP_PATH])


class AdbControl(DeviceControl):
    screenshot_media_type = "image/png"

    def __init__(self, serial: str) -> None:
        self.log = device_log
        self.adb = AdbChannel(serial)
        self.info = AdbInfo(serial)

    def click_coord(self, x: int, y: int) -> None:
        self.adb.shell(["input", "tap", str(int(x)), str(int(y))])

    def click_img(self, nx: float, ny: float) -> tuple[int, int]:
        x, y = self._to_pixel(nx, ny)
        self.click_coord(x, y)
        return x, y

    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        ms = str(int(float(duration) * 1000))
        self.adb.shell(["input", "swipe", str(int(x)), str(int(y)), str(int(x)), str(int(y)), ms])

    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> tuple[int, int]:
        x, y = self._to_pixel(nx, ny)
        self.long_click_coord(x, y, duration=duration)
        return x, y

    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        width, height = self.info.screen_size()
        cx, cy = width // 2, height // 2
        span = int(distance or 500)
        moves = {
            "up": (cx, height * 3 // 4, cx, height * 3 // 4 - span),
            "down": (cx, height // 4, cx, height // 4 + span),
            "left": (width * 3 // 4, cy, width * 3 // 4 - span, cy),
            "right": (width // 4, cy, width // 4 + span, cy),
        }
        self.swipe_coord(*moves.get(str(direction or "up"), moves["up"]))

    def swipe_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        points = [str(int(v)) for v in (x1, y1, x2, y2)]
        ms = str(int(float(duration) * 1000))
        self.adb.shell(["input", "swipe", *points, ms])

    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        x1, y1 = self._to_pixel(nx1, ny1)
        x2, y2 = self._to_pixel(nx2, ny2)
        self.adb.shell(["input", "draganddrop", str(x1), str(y1), str(x2), str(y2), "1000"])

    def input_text(self, text: str, clear_first: bool = True) -> None:
        value = str(text or "")
        if any(ord(char) > 0x7F for char in value):
            raise ValueError("adb input text 只支持 ASCII；中文需改用 IME 方案")
        if clear_first:
            self.adb.shell(["input", "keyevent", "KEYCODE_MOVE_END"])
            self.adb.shell(["input", "keyevent", "KEYCODE_CLEAR"])
        self.adb.shell(["input", "text", _quoted_input_text(value)])

    def press_key(self, key: str = "back") -> None:
        self.adb.shell(["input", "keyevent", str(key or "back").upper()])

    def screenshot_bytes(self) -> bytes:
        png = self.adb.exec_out(["screencap", "-p"])
        if not png.startswith(b"\x89PNG"):
            raise RuntimeError("screencap 返回的不是 PNG")
        return png

    def launcher_component(self, package: str) -> str:
        try:
            output = self.adb.shell(
                [
                    "cmd",
                    "package",
                    "resolve-activity",
                    "--brief",
                    "-c",
                    "android.intent.category.LAUNCHER",
                    str(package),
                ]
            )
        except RuntimeError:
            return ""
        for line in reversed(str(output or "").splitlines()):
            text = line.strip()
            if "/" in text and not text.startswith(("priority=", "No activity")):
                return text
        return ""

    def is_installed(self, package: str) -> bool:
        try:
            output = self.adb.shell(["pm", "list", "packages", str(package)])
        except RuntimeError:
            return False
        expected = f"package:{package}"
        return any(line.strip() == expected for line in str(output or "").splitlines())

    def _install_hint(self, package: str) -> str:
        segments = [part for part in str(package or "").split(".") if part]
        keyword = max(segments, key=len) if segments else ""
        if not keyword:
            return ""
        try:
            output = self.adb.shell(["pm", "list", "packages"])
        except RuntimeError:
            return ""
        near = [
            line.strip().removeprefix("package:")
            for line in str(output or "").splitlines()
            if keyword in line
        ]
        return f"；设备上包含 {keyword!r} 的包：{', '.join(near[:5])}" if near else ""

    def app_start(self, package: str) -> None:
        pkg = str(package or "").strip()
        component = self.launcher_component(pkg)
        if component:
            try:
                self.adb.shell(["am", "start", "-W", "-n", component])
                return
            except RuntimeError:
                pass  # silent-except
        try:
            self.adb.shell(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
            return
        except RuntimeError as exc:
            raise RuntimeError(
                f"启动应用失败：包名 {pkg!r} 未安装或没有 LAUNCHER 入口"
                f"{self._install_hint(pkg)}；monkey 输出：{exc}"
            ) from exc

    def app_stop(self, package: str) -> None:
        pkg = str(package or "").strip()
        if not self.is_installed(pkg):
            raise RuntimeError(f"停止应用失败：包名 {pkg!r} 未安装{self._install_hint(pkg)}")
        self.adb.shell(["am", "force-stop", pkg])

    def screen_size(self) -> tuple[int, int]:
        return self.info.screen_size()

    def _to_pixel(self, nx: float, ny: float) -> tuple[int, int]:
        width, height = self.info.screen_size()
        if width <= 0 or height <= 0:
            raise RuntimeError("屏幕尺寸无效，无法换算归一化坐标")
        x = min(width - 1, max(0, int(float(nx) * width)))
        y = min(height - 1, max(0, int(float(ny) * height)))
        return x, y


class AndroidControl(AdbControl):
    def __init__(self, serial: str) -> None:
        super().__init__(serial)
        self._u2_device = None

    @property
    def device(self):
        if self._u2_device is None:
            _tune_u2_http_timeout()
            try:
                self._u2_device = u2.connect(self.adb.serial)
            except Exception as exc:  # noqa: BLE001 - u2 各类异常统一转可读失败
                raise RuntimeError(f"uiautomator2 连接失败：{exc}") from exc
        return self._u2_device

    def find_xpath(self, xpath: str) -> list[dict]:
        device = self.device
        try:
            elements = device.xpath(str(xpath)).all()
        except Exception as exc:  # noqa: BLE001 - 查询失败按「没查到」处理，但要留痕
            self.log.debug("xpath 查询失败，按空结果处理: %s", exc)
            return []
        found: list[dict] = []
        for el in elements or []:
            attrib = getattr(el, "attrib", None) or {}
            x, y = _bounds_center(str(attrib.get("bounds") or ""))
            found.append({"text": str(attrib.get("text") or ""), "x": x, "y": y})
        return found

    def input_text(self, text: str, clear_first: bool = True) -> None:
        device = self.device
        if clear_first:
            try:
                device.shell("input keyevent KEYCODE_MOVE_END")
                device.shell("input keyevent KEYCODE_CLEAR")
                time.sleep(0.1)
            except Exception:
                self.log.debug("Shell keyevent failed, continuing")
        try:
            device.send_keys(text)
        except Exception:
            device.shell(f"input text {_quoted_input_text(text)}")
