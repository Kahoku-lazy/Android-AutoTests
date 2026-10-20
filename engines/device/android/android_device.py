"""
调试运行入口：python -m engines.device.android.android_device

模块说明：
Android 设备控制模块，实现 Android 设备连接、信息查询、控制功能。

类功能简介：
1. AndroidConnection: 设备连接类 —— 无线 / USB 双栈连接、存活探测与重连。
2. AdbChannel: adb 命令通道 —— 只执行命令、取回结果，不做解析。
3. AdbInfo: 设备信息查询（纯 adb）—— 分辨率 / 前台应用 / 包名 / 已连接设备 / 层级 XML。
4. AdbControl: 设备控制（纯 adb）—— 点击 / 长按 / 滑动 / 拖动 / 输入 / 按键 / 截图 / 应用启停。
5. AndroidControl: 在 AdbControl 之上补 u2 的两项能力 —— xpath 元素查找、非 ASCII 输入；u2 会话按需连接。

"""

from __future__ import annotations

import re
import subprocess
import time

from dataclasses import dataclass

import uiautomator2 as u2

from engines.device.action import DeviceConnection, DeviceControl, DeviceInfo, EngineConnectError
from utils.logs import device_log

# u2 单操作 HTTP 超时上限（秒）。u2 默认 HTTP_TIMEOUT=300，设备冻结会永久阻塞。
U2_OP_TIMEOUT = 20

_CONNECTED_KEYWORDS = ("connected", "already", "已连接", "已经连接", "成功")


@dataclass(frozen=True)
class AndroidConnectionConfig:
    # USB 连接 设备UUID
    uuid: str | None = None

    # 无线连接 设备地址与端口号
    address: str | None = None
    address_port: int | None = None

    # 无线配对码 设备地址与端口号、配对码
    pair_port: int | None = None
    pair_code: str | None = None


class AndroidConnection(DeviceConnection):
    """
    Android 设备连接类
    """

    def __init__(self, config: AndroidConnectionConfig) -> None:
        """
        Args:
            config: AndroidConnectionConfig
        """
        self.config = config
        self.log = device_log  # 设备日志

    def _check_ip_address(self) -> str:
        """
        检查 IP 地址是否有效
        args:
            参数来自 self.config 中的 address 和 address_port
                address: 无线连接地址
                address_port: 无线连接端口
        """
        if self.config.address is None or self.config.address_port is None:
            raise EngineConnectError("无线连接地址与端口号不能为空，请检查配置")

        return f"{self.config.address}:{self.config.address_port}"

    def _check_pair_code(self) -> tuple[str, str]:
        """
        检查无线配对码 设备地址与端口号、配对码是否有效。

        返回 (地址:配对端口, 配对码)。两者必须分开传给 ``adb pair``，
        拼成一个参数时 adb 会把整串当成地址，并在终端等待输入配对码。
        """
        if (
            self.config.pair_code is None
            or self.config.address is None
            or self.config.pair_port is None
        ):
            raise EngineConnectError("配对码不能为空，请检查配置")

        return f"{self.config.address}:{self.config.pair_port}", self.config.pair_code

    def _run_adb(self, *args: str, stdin=None) -> str:
        """执行 adb 子命令并记录命令与结果。失败或超时抛 EngineConnectError，成功返回拼接文本。"""
        shown = " ".join(args)
        self.log.info(f"执行命令: adb {shown}")
        try:
            result = subprocess.run(
                ["adb", *args],
                capture_output=True,
                text=True,
                timeout=10,
                stdin=stdin,
            )
        except subprocess.TimeoutExpired:
            raise EngineConnectError(f"ADB {shown} timed out (10s). Check network.") from None
        output = f"{result.stdout} + {result.stderr}".strip()
        self.log.info(f"adb {args[0]} 命令的执行结果是: {output}")
        if result.returncode != 0:
            raise EngineConnectError(f"ADB {args[0]} failed. {output}")
        return output

    def _adb_connect(self) -> str:
        """
        无线设备 adb connect（关键词判定）；USB 跳过。失败抛 EngineConnectError。

        adb connect 失败时退出码仍是 0（只有终端文本不同），所以不能靠 returncode
        判成败，只能匹配返回文本里的关键词。

        args:
            参数来自 self.config 中的 address 和 address_port
                address: 无线连接地址
                address_port: 无线连接端口
        Raises:
            EngineConnectError: 连接失败
        """

        ip_address = self._check_ip_address()
        self.log.info(f"待连接的设备地址与端口号是: {ip_address}")
        output = self._run_adb("connect", ip_address)
        if not any(word in output for word in _CONNECTED_KEYWORDS):
            raise EngineConnectError(f"ADB connect 失败: {output}")
        return output

    def _adb_disconnect(self) -> None:
        """
        无线设备 adb disconnect（关键词判定）；USB 跳过。失败抛 EngineConnectError。

        args:
            参数来自 self.config 中的 address 和 address_port
                address: 无线连接地址
                address_port: 无线连接端口
        Raises:
            EngineConnectError: 断开连接失败
        """
        ip_address = self._check_ip_address()
        self.log.info(f"待断开的设备地址与端口号是:{ip_address}")
        self._run_adb("disconnect", ip_address)

    def _adb_pair(self) -> None:
        """
        无线设备 adb pair（关键词判定）；USB 跳过。失败抛 EngineConnectError。

        args:
            参数来自 self.config 中的 addr 和 addr_port，pair_code
                addr: 无线连接地址
                addr_port: 无线连接端口
                pair_code: 配对码
        Raises:
            EngineConnectError: 配对失败
        """

        endpoint, code = self._check_pair_code()
        self.log.info(f"待配对的设备地址信息是（地址、端口号、配对码）: {endpoint} {code}")
        self._run_adb("pair", endpoint, code, stdin=subprocess.DEVNULL)

    def disconnect(self) -> None:
        """断开无线设备连接。USB 没有地址，直接返回。"""
        if self.config.address is None:
            return
        self._adb_disconnect()

    def connect(self) -> None:
        """
        连接设备，先配对设备，再连接设备；如果已经配对，则直接连接设备。
        USB 只保留序列号，不走 adb connect。

        args:
            参数来自 self.config 中的 pair_code
                pair_code: 配对码
        Raises:
            EngineConnectError: 连接失败
        """
        if self.config.pair_code is not None:
            self._adb_pair()
        if self.config.address is not None:
            self._adb_connect()

    def adb_devices(self) -> str:
        """返回 ``adb devices`` 原文。已连接行形如 ``192.168.35.57:44123     device``。"""
        return self._run_adb("devices")


def _bounds_center(bounds: str) -> tuple[int, int]:
    """把 `[left,top][right,bottom]` 解成中心点；解析失败返回 (0, 0)。"""
    parts = bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")
    if len(parts) != 4 or not all(part.strip().lstrip("-").isdigit() for part in parts):
        return 0, 0
    left, top, right, bottom = (int(part) for part in parts)
    return (left + right) // 2, (top + bottom) // 2


# ══════════════════════════════════════════════════════════════════════
# 纯 adb 实现：只用 adb 命令，不依赖 uiautomator2 服务
#
# System.info("android")    -> AdbInfo
# System.control("android") -> AndroidControl（本文件末尾，继承 AdbControl）
# 本文件末尾的 AndroidControl 只额外补 u2 的两项能力：xpath 元素查找与非 ASCII 输入。
# ══════════════════════════════════════════════════════════════════════

from pathlib import Path

ADB = "adb"


def _run(args: list[str], timeout: float = 30.0) -> tuple[int, bytes, bytes]:
    """跑一条 adb 命令, 返回 (退出码, stdout 字节, stderr 字节)。
    stdout 必须是字节: screencap 是二进制, 一旦按文本解码就会被换行转换破坏。
    """
    proc = subprocess.run([ADB, *args], capture_output=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def capture_png(serial: str, file_path: str) -> bytes:
    """adb exec-out screencap -p -> PNG 原始字节。

    args:
        serial: 设备序列号

    return: PNG 原始字节

    """
    code, out, err = _run(["-s", serial, "exec-out", "screencap", "-p"])
    if code != 0:
        raise RuntimeError(f"screencap 失败: {err.decode('utf-8', 'ignore').strip()}")
    if not out.startswith(b"\x89PNG"):
        raise RuntimeError(f"返回的不是 PNG, 前 8 字节 = {out[:8]!r}")

    Path(file_path).write_bytes(out)
    return out


_ADB_EXE = "adb"
_UIDUMP_PATH = "/data/local/tmp/window_dump.xml"
_FAIL_DETAIL_LIMIT = 200


def _failure_detail(stdout: bytes, stderr: bytes) -> str:
    """把失败的 stdout / stderr 收成一行可读详情。

    stderr 优先；为空时退回 stdout——设备侧的报错通常走 stdout，不退回会只剩「未知错误」。

    Args:
        stdout: 子进程标准输出字节。
        stderr: 子进程标准错误字节。

    Returns:
        压成单行并截断的详情；两者都为空时返回「未知错误」。
    """
    for raw in (stderr, stdout):
        text = " ".join((raw or b"").decode("utf-8", "replace").split())
        if not text:
            continue
        if len(text) > _FAIL_DETAIL_LIMIT:
            return text[:_FAIL_DETAIL_LIMIT] + "…"
        return text
    return "未知错误"


class AdbChannel:
    """adb 命令通道：只负责执行命令并取回结果，不做任何解析。"""

    def __init__(self, serial: str, executable: str = _ADB_EXE) -> None:
        self.serial = serial
        self.executable = executable

    def shell(self, args: list[str], timeout: float = 30.0) -> str:
        """跑一条 adb shell 命令，返回解码后的文本。

        Args:
            args: 命令及其参数，例如 ["wm", "size"]。
            timeout: 命令超时秒数。

        Returns:
            标准输出文本。

        Raises:
            RuntimeError: 命令退出码非 0。
        """
        return self.shell_bytes(args, timeout).decode("utf-8", "replace")

    def shell_bytes(self, args: list[str], timeout: float = 30.0) -> bytes:
        """跑一条 adb shell 命令，返回原始字节。

        Args:
            args: 命令及其参数。
            timeout: 命令超时秒数。

        Returns:
            标准输出字节。

        Raises:
            RuntimeError: 命令退出码非 0。
        """
        return self._exec(["shell", *args], timeout)

    def exec_out(self, args: list[str], timeout: float = 30.0) -> bytes:
        """跑一条 adb exec-out 命令，返回原始字节。

        exec-out 不经 PTY，二进制安全；抓图必须用它而不是 shell。

        Args:
            args: 命令及其参数。
            timeout: 命令超时秒数。

        Returns:
            标准输出字节。

        Raises:
            RuntimeError: 命令退出码非 0。
        """
        return self._exec(["exec-out", *args], timeout)

    def host(self, args: list[str], timeout: float = 10.0) -> str:
        """跑一条不带 -s 的主机侧 adb 命令（如 devices），返回文本。

        Args:
            args: 命令及其参数。
            timeout: 命令超时秒数。

        Returns:
            标准输出文本。

        Raises:
            RuntimeError: 命令退出码非 0。
        """
        return self._exec(args, timeout, with_serial=False).decode("utf-8", "replace")

    def _exec(self, args: list[str], timeout: float, with_serial: bool = True) -> bytes:
        """执行 adb 进程并返回标准输出字节。

        Args:
            args: 命令及其参数。
            timeout: 命令超时秒数。
            with_serial: 是否带上 -s <serial>。

        Returns:
            标准输出字节。

        Raises:
            RuntimeError: 命令退出码非 0。
        """
        command = [self.executable]
        if with_serial:
            command += ["-s", self.serial]
        proc = subprocess.run(command + args, capture_output=True, timeout=timeout)
        if proc.returncode != 0:
            detail = _failure_detail(proc.stdout, proc.stderr)
            raise RuntimeError(f"adb {' '.join(args)} 失败：{detail}")
        return proc.stdout


def _parse_wm_size(text: str) -> tuple[int, int]:
    """从 `wm size` 输出取分辨率，Override 优先于 Physical。

    Args:
        text: `wm size` 的原始输出。

    Returns:
        (宽, 高)。

    Raises:
        RuntimeError: 两种尺寸都解析不到。
    """
    for pattern in (r"Override size:\s*(\d+)x(\d+)", r"Physical size:\s*(\d+)x(\d+)"):
        match = re.search(pattern, text or "")
        if match:
            return int(match.group(1)), int(match.group(2))
    raise RuntimeError(f"wm size 输出无法解析：{(text or '').strip()}")


def _parse_current_app(text: str) -> dict:
    """从 `dumpsys window` 输出取当前前台应用。

    Args:
        text: `dumpsys window` 的原始输出。

    Returns:
        {"package": 包名, "activity": Activity}；取不到时两者为空串。
    """
    match = re.search(r"mCurrentFocus=.*?\s([\w.]+)/([\w.$]+)", text or "")
    if not match:
        return {"package": "", "activity": ""}
    return {"package": match.group(1), "activity": match.group(2)}


def _parse_packages(text: str, query: str = "") -> list[str]:
    """从 `pm list packages` 输出取包名，可按关键词过滤。

    Args:
        text: `pm list packages` 的原始输出。
        query: 关键词（忽略大小写子串匹配），空串返回全部。

    Returns:
        包名列表。
    """
    names = [
        line.split(":", 1)[1].strip()
        for line in (text or "").splitlines()
        if line.startswith("package:") and ":" in line
    ]
    keyword = str(query or "").strip().casefold()
    return [name for name in names if keyword in name.casefold()]


def _parse_devices(text: str) -> list[str]:
    """从 `adb devices` 输出取已连接序列号。

    Args:
        text: `adb devices` 的原始输出。

    Returns:
        状态为 device 的序列号列表。
    """
    serials: list[str] = []
    for line in (text or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


class AdbInfo(DeviceInfo):
    """设备信息查询（纯 adb）。不需要 uiautomator2 服务。"""

    def __init__(self, serial: str) -> None:
        self.log = device_log
        self.adb = AdbChannel(serial)

    def screen_size(self) -> tuple[int, int]:
        """屏幕分辨率 (宽, 高)，Override 尺寸优先。

        Returns:
            (宽, 高)。

        Raises:
            RuntimeError: wm size 输出无法解析。
        """
        return _parse_wm_size(self.adb.shell(["wm", "size"]))

    def current_app(self) -> dict:
        """当前前台应用。

        Returns:
            {"package": 包名, "activity": Activity}。
        """
        return _parse_current_app(self.adb.shell(["dumpsys", "window"]))

    def packages(self, query: str = "") -> list[str]:
        """已安装包名列表。

        Args:
            query: 关键词，空串返回全部。

        Returns:
            包名列表。
        """
        return _parse_packages(self.adb.shell(["pm", "list", "packages"]), query)

    def connected_devices(self) -> list[str]:
        """当前已连接的设备序列号。

        Returns:
            序列号列表。

        Raises:
            RuntimeError: adb devices 失败。
        """
        return _parse_devices(self.adb.host(["devices"]))

    def hierarchy_xml(self) -> str:
        """页面层级原始 XML（系统 uiautomator dump，不需要 u2 服务）。

        Returns:
            XML 文本。

        Raises:
            RuntimeError: dump 或读取失败。
        """
        self.adb.shell(["uiautomator", "dump", _UIDUMP_PATH])
        return self.adb.shell(["cat", _UIDUMP_PATH])


class AdbControl(DeviceControl):
    """设备控制（纯 adb）。只覆盖 adb 能做的动作，xpath 相关方法不在本类。"""

    # 本实现的截图是 PNG（无损、原尺寸），由 Screenshot.save 读取该属性决定 media_type。
    screenshot_media_type = "image/png"

    def __init__(self, serial: str) -> None:
        self.log = device_log
        self.adb = AdbChannel(serial)
        self.info = AdbInfo(serial)

    # ── 点击 ──
    def click_coord(self, x: int, y: int) -> None:
        """按设备像素坐标点击。

        Args:
            x: 横坐标像素。
            y: 纵坐标像素。
        """
        self.adb.shell(["input", "tap", str(int(x)), str(int(y))])

    def click_img(self, nx: float, ny: float) -> tuple[int, int]:
        """按归一化坐标点击。

        Args:
            nx: 横向相对位置 0~1。
            ny: 纵向相对位置 0~1。

        Returns:
            实际点击的像素坐标 (x, y)。

        Raises:
            RuntimeError: 屏幕尺寸无效。
        """
        x, y = self._to_pixel(nx, ny)
        self.click_coord(x, y)
        return x, y

    # ── 长按 ──
    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        """按像素坐标长按（原地 swipe 模拟）。

        Args:
            x: 横坐标像素。
            y: 纵坐标像素。
            duration: 按住时长秒数。
        """
        ms = str(int(float(duration) * 1000))
        self.adb.shell(["input", "swipe", str(int(x)), str(int(y)), str(int(x)), str(int(y)), ms])

    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> tuple[int, int]:
        """按归一化坐标长按。

        Args:
            nx: 横向相对位置 0~1。
            ny: 纵向相对位置 0~1。
            duration: 按住时长秒数。

        Returns:
            实际按下的像素坐标 (x, y)。

        Raises:
            RuntimeError: 屏幕尺寸无效。
        """
        x, y = self._to_pixel(nx, ny)
        self.long_click_coord(x, y, duration=duration)
        return x, y

    # ── 滑动 / 拖动 ──
    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        """按方向滑动。

        Args:
            direction: up / down / left / right。
            distance: 滑动距离像素。

        Raises:
            RuntimeError: 屏幕尺寸无效。
        """
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
        """按像素起终点滑动。

        Args:
            x1: 起点横坐标像素。
            y1: 起点纵坐标像素。
            x2: 终点横坐标像素。
            y2: 终点纵坐标像素。
            duration: 滑动时长秒数。
        """
        points = [str(int(v)) for v in (x1, y1, x2, y2)]
        ms = str(int(float(duration) * 1000))
        self.adb.shell(["input", "swipe", *points, ms])

    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        """按归一化起终点拖动（长按后拖动，不是滑动）。

        Args:
            nx1: 起点横向 0~1。
            ny1: 起点纵向 0~1。
            nx2: 终点横向 0~1。
            ny2: 终点纵向 0~1。

        Raises:
            RuntimeError: 屏幕尺寸无效。
        """
        x1, y1 = self._to_pixel(nx1, ny1)
        x2, y2 = self._to_pixel(nx2, ny2)
        self.adb.shell(["input", "draganddrop", str(x1), str(y1), str(x2), str(y2), "1000"])

    # ── 输入 / 按键 ──
    def input_text(self, text: str, clear_first: bool = True) -> None:
        """向当前输入框输入文本（仅 ASCII）。

        Args:
            text: 要输入的文本。
            clear_first: 输入前是否清空。

        Raises:
            ValueError: 文本含非 ASCII 字符（adb input text 的硬限制）。
        """
        value = str(text or "")
        if any(ord(char) > 0x7F for char in value):
            raise ValueError("adb input text 只支持 ASCII；中文需改用 IME 方案")
        if clear_first:
            self.adb.shell(["input", "keyevent", "KEYCODE_MOVE_END"])
            self.adb.shell(["input", "keyevent", "KEYCODE_CLEAR"])
        self.adb.shell(["input", "text", value.replace(" ", "%s")])

    def press_key(self, key: str = "back") -> None:
        """按系统按键。

        Args:
            key: 按键名，如 back / home / enter。
        """
        self.adb.shell(["input", "keyevent", str(key or "back").upper()])

    # ── 截图 / 应用 ──
    def screenshot_bytes(self) -> bytes:
        """截屏并返回原始 PNG 字节（无损、原尺寸）。

        Returns:
            PNG 字节。

        Raises:
            RuntimeError: 截屏失败或返回的不是 PNG。
        """
        png = self.adb.exec_out(["screencap", "-p"])
        if not png.startswith(b"\x89PNG"):
            raise RuntimeError("screencap 返回的不是 PNG")
        return png

    def app_start(self, package: str) -> None:
        """启动应用（monkey 拉起 LAUNCHER，无需知道 Activity 名）。

        Args:
            package: 包名。
        """
        self.adb.shell(
            ["monkey", "-p", str(package), "-c", "android.intent.category.LAUNCHER", "1"]
        )

    def app_stop(self, package: str) -> None:
        """停止应用。

        Args:
            package: 包名。
        """
        self.adb.shell(["am", "force-stop", str(package)])

    def screen_size(self) -> tuple[int, int]:
        """屏幕分辨率，转发给 AdbInfo。

        Returns:
            (宽, 高)。

        Raises:
            RuntimeError: wm size 输出无法解析。
        """
        return self.info.screen_size()

    # ── 内部辅助 ──
    def _to_pixel(self, nx: float, ny: float) -> tuple[int, int]:
        """归一化坐标换算成像素坐标，并夹在屏幕范围内。

        Args:
            nx: 横向相对位置 0~1。
            ny: 纵向相对位置 0~1。

        Returns:
            (x, y) 像素坐标。

        Raises:
            RuntimeError: 屏幕尺寸无效。
        """
        width, height = self.info.screen_size()
        if width <= 0 or height <= 0:
            raise RuntimeError("屏幕尺寸无效，无法换算归一化坐标")
        x = min(width - 1, max(0, int(float(nx) * width)))
        y = min(height - 1, max(0, int(float(ny) * height)))
        return x, y


class AndroidControl(AdbControl):
    """设备控制：动作全部走纯 adb；u2 只在 xpath 查找与非 ASCII 输入时按需连接。"""

    def __init__(self, serial: str) -> None:
        super().__init__(serial)
        # 惰性 u2 会话：截图 / 点击 / 滑动 / dump 等纯 adb 动作永远不碰它
        self._u2_device = None

    @property
    def device(self):
        """uiautomator2 会话：首次访问才连接，之后复用同一实例。

        Returns:
            已连接的 u2 设备对象。

        Raises:
            RuntimeError: u2 服务不可用或设备掉线，连接失败。
        """
        if self._u2_device is None:
            try:
                self._u2_device = u2.connect(self.adb.serial)
            except Exception as exc:  # noqa: BLE001 - u2 各类异常统一转可读失败
                raise RuntimeError(f"uiautomator2 连接失败：{exc}") from exc
        return self._u2_device

    def find_xpath(self, xpath: str) -> list[dict]:
        """按传入的 xpath 查找元素，返回元素文本与中心点坐标；查不到返回空列表。

        Args:
            xpath: 元素 xpath 表达式。

        Returns:
            [{"text", "x", "y"}]；text 取元素文本，没有则为空串；
            x / y 是元素 bounds 的中心点，可直接交给 click_coord 点击，
            bounds 解析失败时为 (0, 0)。

        Raises:
            RuntimeError: uiautomator2 连接失败（不当作「查不到元素」）。
        """
        # 连接失败在这里抛：不能被下面「查询本身失败」的兜底吞成空列表
        device = self.device
        try:
            elements = device.xpath(str(xpath)).all()
        except Exception:
            return []
        found: list[dict] = []
        for el in elements or []:
            attrib = getattr(el, "attrib", None) or {}
            x, y = _bounds_center(str(attrib.get("bounds") or ""))
            found.append({"text": str(attrib.get("text") or ""), "x": x, "y": y})
        return found

    def input_text(self, text: str, clear_first: bool = True) -> None:
        """向当前输入框输入文本；走 u2 的 send_keys，支持中文等非 ASCII。

        Args:
            text: 要输入的文本。
            clear_first: 输入前是否清空输入框。

        Raises:
            RuntimeError: uiautomator2 连接失败。
        """
        # 连接失败在这里抛：不能落进下面的输入兜底，否则错误会被掩盖
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
            safe = text.replace(" ", "%s").replace("'", "\\'")
            device.shell(f"input text '{safe}'")
