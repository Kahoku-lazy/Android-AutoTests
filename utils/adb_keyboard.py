from __future__ import annotations

import argparse
import base64
import hashlib
import logging
import os
import re
import subprocess
import sys
import threading
import time

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import requests

from utils.adb import adb_binary

__all__ = [
    "CHUNK_CHARS",
    "IME_ID",
    "PACKAGE",
    "VERSION",
    "apk_path",
    "broadcast",
    "clear_text",
    "current_ime",
    "encode_text",
    "ensure_apk",
    "ensure_ime",
    "ensure_ready",
    "input_text",
    "install_connected",
    "install_on",
    "installed",
    "list_connected",
    "main",
    "restore_ime",
    "serial_lock",
    "split_chunks",
    "verify_apk",
]

VERSION = "2.4-dev"
PACKAGE = "com.android.adbkeyboard"
IME_ID = "com.android.adbkeyboard/.AdbIME"
URL = "https://github.com/senzhk/ADBKeyBoard/releases/download/v2.4-dev/keyboardservice-debug.apk"
SIZE = 18595
SHA256 = "e0d0cf276b710cb34c46121f58720f5285a83ed410b0d45f57a0677b67dc2852"
CHUNK_CHARS = 800
APK_NAME = f"ADBKeyboard-{VERSION}.apk"
CACHE_DIR = Path(__file__).resolve().parents[1] / "tools" / ".cache" / "adbkeyboard"
INSTALL_TIMEOUT = 120.0
DEFAULT_TIMEOUT = 20.0
IME_TIMEOUT = 15.0
IME_SWITCH_WAIT = 3.0

log = logging.getLogger(__name__)

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def apk_path() -> Path:
    return CACHE_DIR / APK_NAME


@contextmanager
def serial_lock(serial: str) -> Iterator[None]:
    key = str(serial or "")
    with _locks_guard:
        lock = _locks.setdefault(key, threading.Lock())
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_apk(path: str | Path) -> Path:
    target = Path(path)
    if not target.is_file():
        raise RuntimeError(f"找不到 ADBKeyboard 安装包：{target}")
    size = target.stat().st_size
    if size != SIZE:
        raise RuntimeError(f"ADBKeyboard 安装包大小不符：期望 {SIZE}，实际 {size}（{target}）")
    digest = _sha256(target)
    if digest.lower() != SHA256.lower():
        raise RuntimeError(f"ADBKeyboard 安装包校验不符：期望 {SHA256}，实际 {digest}（{target}）")
    return target


def _download(target: Path) -> None:
    partial = target.with_name(target.name + ".part")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(URL, stream=True, timeout=(10, 60)) as response:
            response.raise_for_status()
            with partial.open("wb") as handle:
                for block in response.iter_content(64 * 1024):
                    if block:
                        handle.write(block)
        verify_apk(partial)
        os.replace(partial, target)
    except Exception as exc:  # noqa: BLE001 - 下载/校验/落盘任一环节失败都转成可读错误
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            f"下载 ADBKeyboard 失败：{exc}；离线环境请设 ADB_KEYBOARD_APK 指向本地安装包"
        ) from exc


def ensure_apk(archive: str | Path | None = None) -> Path:
    override = archive or os.environ.get("ADB_KEYBOARD_APK", "").strip()
    if override:
        return verify_apk(Path(override))
    cached = apk_path()
    if cached.is_file():
        try:
            return verify_apk(cached)
        except RuntimeError:
            cached.unlink(missing_ok=True)
    _download(cached)
    return cached


def _run(serial: str, args: list[str], timeout: float = DEFAULT_TIMEOUT) -> str:
    command = [adb_binary()]
    if serial:
        command += ["-s", serial]
    command += args
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"adb {' '.join(args)} 超时（{timeout:g}s）") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(f"找不到 adb（{adb_binary()}）") from exc
    if proc.returncode != 0:
        detail = " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())[:300]
        raise RuntimeError(f"adb {' '.join(args)} 失败：{detail or '无输出'}")
    return (proc.stdout or "").strip()


def installed(serial: str) -> bool:
    output = _run(serial, ["shell", "pm", "list", "packages", PACKAGE], timeout=10)
    return f"package:{PACKAGE}" in output


def install_on(serial: str, archive: str | Path | None = None) -> Path:
    apk = ensure_apk(archive)
    output = _run(serial, ["install", "-r", str(apk)], timeout=INSTALL_TIMEOUT)
    if "Success" not in output:
        raise RuntimeError(f"ADBKeyboard 安装失败：{output[:300]}")
    return apk


def ensure_ready(serial: str, archive: str | Path | None = None) -> str:
    try:
        if installed(serial):
            return ""
        install_on(serial, archive)
        return ""
    except RuntimeError as exc:
        return str(exc)


def list_connected() -> list[str]:
    output = _run("", ["devices"])
    serials: list[str] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def current_ime(serial: str) -> str:
    return _run(
        serial,
        ["shell", "settings", "get", "secure", "default_input_method"],
        timeout=10,
    )


def _enable_ime(serial: str) -> None:
    _run(serial, ["shell", "ime", "enable", IME_ID], timeout=IME_TIMEOUT)


def _set_ime(serial: str, ime_id: str) -> None:
    _run(serial, ["shell", "ime", "set", ime_id], timeout=IME_TIMEOUT)


def _wait_ime(serial: str, expected: str, timeout: float = IME_SWITCH_WAIT) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if current_ime(serial) == expected:
            return True
        time.sleep(0.1)
    return False


def ensure_ime(serial: str, archive: str | Path | None = None) -> str:
    if not installed(serial):
        install_on(serial, archive)
    _enable_ime(serial)
    previous = current_ime(serial)
    if previous != IME_ID:
        _set_ime(serial, IME_ID)
        if not _wait_ime(serial, IME_ID):
            raise RuntimeError(f"输入法切换失败：{IME_ID}（设备 {serial}）")
    return previous


def restore_ime(serial: str, previous: str) -> str:
    if not previous or previous == IME_ID:
        return ""
    try:
        _set_ime(serial, previous)
        if _wait_ime(serial, previous):
            return ""
        return f"输入法未在超时内恢复：{previous}（设备 {serial}）"
    except RuntimeError as exc:
        return f"输入法恢复失败：{exc}"


def broadcast(serial: str, action: str, extras: dict[str, str | int] | None = None) -> str:
    args = ["shell", "am", "broadcast", "-a", action]
    for key, value in (extras or {}).items():
        args += ["--ei" if isinstance(value, int) else "--es", key, str(value)]
    output = _run(serial, args)
    match = re.search(r"result=(-?\d+)", output)
    if not match or int(match.group(1)) != 0:
        raise RuntimeError(f"输入法广播失败：{action}；{output[-200:]}")
    return output


def encode_text(text: str) -> str:
    return base64.b64encode(str(text or "").encode("utf-8")).decode("ascii")


def split_chunks(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    value = str(text or "")
    size = max(1, int(limit))
    return [value[index : index + size] for index in range(0, len(value), size)]


def clear_text(serial: str) -> None:
    broadcast(serial, "ADB_CLEAR_TEXT")


def input_text(
    serial: str,
    text: str,
    clear_first: bool = True,
    archive: str | Path | None = None,
) -> None:
    value = str(text or "")
    with serial_lock(serial):
        previous = ensure_ime(serial, archive)
        try:
            if clear_first:
                clear_text(serial)
            for chunk in split_chunks(value):
                broadcast(serial, "ADB_INPUT_B64", {"msg": encode_text(chunk)})
        finally:
            warning = restore_ime(serial, previous)
            if warning:
                log.warning(warning)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m utils.adb_keyboard")
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("install")
    install.add_argument("--serial", default="all")
    install.add_argument("--file", default="")
    status = sub.add_parser("status")
    status.add_argument("--serial", default="all")
    args = parser.parse_args(argv)

    wanted = str(args.serial or "").strip()
    serials = list_connected() if wanted in {"", "all"} else [wanted]
    if not serials:
        print("没有在线设备", file=sys.stderr)  # noqa: T201
        return 1

    code = 0
    for serial in serials:
        if args.action == "install":
            try:
                if installed(serial):
                    print(f"{serial}: 已安装，跳过")  # noqa: T201
                    continue
                apk = install_on(serial, getattr(args, "file", "") or None)
            except RuntimeError as exc:
                print(f"{serial}: 安装失败：{exc}")  # noqa: T201
                code = 1
                continue
            print(f"{serial}: 已安装 {apk.name}")  # noqa: T201
            continue
        ready = installed(serial)
        print(f"{serial}: {'已安装' if ready else '未安装'}")  # noqa: T201
        if not ready:
            code = 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
