"""
文件名: ➡️ core.py 🏁
路径: ➡️ engines/ae_harness/tools/adb/core.py 🏁
模块功能：➡️ adb 命令执行与设备选择 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.adb.core 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. AdbError: adb 执行失败或设备不满足条件。
2. run_adb: 执行一条 adb 命令并返回文本输出。
3. run_adb_bytes: 执行一条 adb 命令并返回二进制输出（截图用）。
4. list_devices: 解析 adb devices -l，列出已连接设备。
5. resolve_serial: 没指定设备时，按当前连接情况挑唯一在线设备。
6. adb_binary: 取实际使用的 adb 路径；项目内 tools/platform-tools 优先。
7. screen_size: 读取屏幕分辨率，供归一化坐标换算。
🏁
关联模块：➡️
1. 无本地依赖：只用标准库 subprocess。
🏁
测试：➡️
1. 见 engines.ae_harness.tools.adb.tools。
🏁
"""

from __future__ import annotations

import os
import subprocess

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = [
    "AdbError",
    "DeviceInfo",
    "adb_binary",
    "list_devices",
    "resolve_serial",
    "run_adb",
    "run_adb_bytes",
    "screen_size",
]

# 项目自带的 platform-tools 优先；路径相对仓库根。
_ADB_NAME = "adb.exe" if os.name == "nt" else "adb"
_REPO_ROOT = Path(__file__).resolve().parents[4]
_BUNDLED_ADB = _REPO_ROOT / "tools" / "platform-tools" / _ADB_NAME


@lru_cache(maxsize=1)
def adb_binary() -> str:
    """
    取实际使用的 adb 路径。

    项目内 tools/platform-tools 存在时优先用它，否则退回 PATH 里的 adb。

    Returns:
        可直接执行的 adb 路径或命令名。
    """
    if _BUNDLED_ADB.is_file():
        return str(_BUNDLED_ADB)
    return "adb"


class AdbError(RuntimeError):
    """
    adb 执行失败或设备不满足条件。

    消息面向调用方：说明是没装 adb、超时、命令失败还是设备不对。

    Attributes:
        无。
    """


@dataclass(frozen=True)
class DeviceInfo:
    """
    一台已连接设备。

    Attributes:
        serial: 设备序列号。
        state: 连接状态，device 表示可用。
        model: 厂商型号。
        product: 产品名。
        transport_id: adb 传输编号。
    """

    serial: str
    state: str
    model: str = ""
    product: str = ""
    transport_id: str = ""


def _build_command(args: list[str], serial: str) -> list[str]:
    """
    拼出完整命令。

    Args:
        args: adb 子命令与参数。
        serial: 设备序列号；空串表示用 adb 默认设备。

    Returns:
        可直接交给 subprocess 的参数列表。
    """
    command = [adb_binary()]
    if serial:
        command += ["-s", serial]
    return command + args


def run_adb(args: list[str], *, serial: str = "", timeout: int = 30) -> str:
    """
    执行一条 adb 命令并返回文本输出。

    Args:
        args: adb 子命令与参数，如 ["shell", "input", "tap", "100", "200"]。
        serial: 设备序列号；空串表示用默认设备。
        timeout: 超时秒数。

    Returns:
        stdout 去掉首尾空白；stderr 只在失败时使用。

    Raises:
        AdbError: 找不到 adb、超时，或命令返回非零。
    """
    command = _build_command(args, serial)
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AdbError(
            f"找不到 adb（{adb_binary()}），请确认 tools/platform-tools 存在或 PATH 里有 adb"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb 超时（{timeout}s）：{' '.join(command)}") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise AdbError(f"adb 执行失败（{proc.returncode}）：{detail or ' '.join(command)}")
    return (proc.stdout or "").strip()


def run_adb_bytes(args: list[str], *, serial: str = "", timeout: int = 30) -> bytes:
    """
    执行一条 adb 命令并返回二进制输出。

    Args:
        args: adb 子命令与参数。
        serial: 设备序列号；空串表示用默认设备。
        timeout: 超时秒数。

    Returns:
        stdout 原始字节。

    Raises:
        AdbError: 找不到 adb、超时，或命令返回非零。
    """
    command = _build_command(args, serial)
    try:
        proc = subprocess.run(command, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise AdbError(
            f"找不到 adb（{adb_binary()}），请确认 tools/platform-tools 存在或 PATH 里有 adb"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb 超时（{timeout}s）：{' '.join(command)}") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or b"").decode("utf-8", "replace").strip()
        raise AdbError(f"adb 执行失败（{proc.returncode}）：{detail or ' '.join(command)}")
    return proc.stdout or b""


def list_devices() -> list[DeviceInfo]:
    """
    列出已连接设备。

    Returns:
        设备列表；没连设备时为空列表。

    Raises:
        AdbError: adb 不可用或命令失败。
    """
    text = run_adb(["devices", "-l"])
    devices: list[DeviceInfo] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("List of") or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        extra: dict[str, str] = {}
        for token in parts[2:]:
            if ":" in token:
                key, value = token.split(":", 1)
                extra[key] = value
        devices.append(
            DeviceInfo(
                serial=serial,
                state=state,
                model=extra.get("model", ""),
                product=extra.get("product", ""),
                transport_id=extra.get("transport_id", ""),
            )
        )
    return devices


def resolve_serial(serial: str = "") -> str:
    """
    确定这次操作要用哪台设备。

    Args:
        serial: 调用方指定的序列号；空串表示自动选。

    Returns:
        可用的设备序列号。

    Raises:
        AdbError: 指定的设备不在线、没有在线设备，或有多台却没指定。
    """
    online = [device for device in list_devices() if device.state == "device"]
    if serial:
        if any(device.serial == serial for device in online):
            return serial
        names = ", ".join(device.serial for device in online) or "无"
        raise AdbError(f"设备 {serial} 不在线；当前在线：{names}")
    if not online:
        raise AdbError("没有已连接的设备；请先执行 adb connect 或插上 USB")
    if len(online) > 1:
        names = ", ".join(device.serial for device in online)
        raise AdbError(f"连接了多台设备，请指定 serial：{names}")
    return online[0].serial


def screen_size(serial: str = "") -> tuple[int, int]:
    """
    读取当前屏幕分辨率。

    优先用 Override size（实际生效值），没有则用 Physical size。

    Args:
        serial: 设备序列号；空串表示用默认设备。

    Returns:
        (宽, 高)，单位为像素。

    Raises:
        AdbError: 读不到分辨率，或返回格式不认识。
    """
    target = resolve_serial(serial)
    text = run_adb(["shell", "wm", "size"], serial=target, timeout=15)
    override = ""
    physical = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Override size:"):
            override = line.split(":", 1)[1].strip()
        elif line.startswith("Physical size:"):
            physical = line.split(":", 1)[1].strip()
    raw = override or physical
    if not raw or "x" not in raw.lower():
        raise AdbError(f"无法解析屏幕分辨率：{raw or text or '空'}")
    width_text, height_text = raw.lower().split("x", 1)
    try:
        return int(width_text), int(height_text)
    except ValueError as exc:
        raise AdbError(f"无法解析屏幕分辨率：{raw}") from exc
