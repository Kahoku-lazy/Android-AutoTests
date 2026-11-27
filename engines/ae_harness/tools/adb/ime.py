from __future__ import annotations

import base64
import logging
import re
import threading
import time

from collections.abc import Iterator
from contextlib import contextmanager

from .core import AdbError, run_adb

__all__ = [
    "CHUNK_CHARS",
    "IME_ID",
    "PACKAGE",
    "SHA256",
    "SIZE",
    "URL",
    "VERSION",
    "broadcast",
    "encode_text",
    "ensure_ime",
    "input_unicode",
    "installed",
    "restore_ime",
    "split_chunks",
]

VERSION = "2.4-dev"
PACKAGE = "com.android.adbkeyboard"
IME_ID = "com.android.adbkeyboard/.AdbIME"
URL = "https://github.com/senzhk/ADBKeyBoard/releases/download/v2.4-dev/keyboardservice-debug.apk"
SIZE = 18595
SHA256 = "e0d0cf276b710cb34c46121f58720f5285a83ed410b0d45f57a0677b67dc2852"
CHUNK_CHARS = 800
IME_SWITCH_WAIT = 3.0

log = logging.getLogger(__name__)

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


@contextmanager
def _serial_lock(serial: str) -> Iterator[None]:
    key = str(serial or "")
    with _locks_guard:
        lock = _locks.setdefault(key, threading.Lock())
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def installed(serial: str) -> bool:
    output = run_adb(["shell", "pm", "list", "packages", PACKAGE], serial=serial, timeout=10)
    return f"package:{PACKAGE}" in output


def _current_ime(serial: str) -> str:
    return run_adb(
        ["shell", "settings", "get", "secure", "default_input_method"],
        serial=serial,
        timeout=10,
    )


def _set_ime(serial: str, ime_id: str) -> None:
    run_adb(["shell", "ime", "set", ime_id], serial=serial, timeout=15)


def _wait_ime(serial: str, expected: str, timeout: float = IME_SWITCH_WAIT) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _current_ime(serial) == expected:
            return True
        time.sleep(0.1)
    return False


def ensure_ime(serial: str) -> str:
    if not installed(serial):
        raise AdbError(
            f"设备 {serial} 未安装 ADBKeyboard；请先运行 "
            f"python -m utils.adb_keyboard install --serial {serial}"
        )
    run_adb(["shell", "ime", "enable", IME_ID], serial=serial, timeout=15)
    previous = _current_ime(serial)
    if previous != IME_ID:
        _set_ime(serial, IME_ID)
        if not _wait_ime(serial, IME_ID):
            raise AdbError(f"输入法切换失败：{IME_ID}（设备 {serial}）")
    return previous


def restore_ime(serial: str, previous: str) -> str:
    if not previous or previous == IME_ID:
        return ""
    try:
        _set_ime(serial, previous)
        if _wait_ime(serial, previous):
            return ""
        return f"输入法未在超时内恢复：{previous}（设备 {serial}）"
    except AdbError as exc:
        return f"输入法恢复失败：{exc}"


def broadcast(serial: str, action: str, extras: dict[str, str | int] | None = None) -> str:
    args = ["shell", "am", "broadcast", "-a", action]
    for key, value in (extras or {}).items():
        args += ["--ei" if isinstance(value, int) else "--es", key, str(value)]
    output = run_adb(args, serial=serial)
    match = re.search(r"result=(-?\d+)", output)
    if not match or int(match.group(1)) != 0:
        raise AdbError(f"输入法广播失败：{action}；{output[-200:]}")
    return output


def encode_text(text: str) -> str:
    return base64.b64encode(str(text or "").encode("utf-8")).decode("ascii")


def split_chunks(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    value = str(text or "")
    size = max(1, int(limit))
    return [value[index : index + size] for index in range(0, len(value), size)]


def input_unicode(serial: str, text: str, clear_first: bool = True) -> None:
    value = str(text or "")
    with _serial_lock(serial):
        previous = ensure_ime(serial)
        try:
            if clear_first:
                broadcast(serial, "ADB_CLEAR_TEXT")
            for chunk in split_chunks(value):
                broadcast(serial, "ADB_INPUT_B64", {"msg": encode_text(chunk)})
        finally:
            warning = restore_ime(serial, previous)
            if warning:
                log.warning(warning)
