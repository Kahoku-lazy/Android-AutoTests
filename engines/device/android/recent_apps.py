from __future__ import annotations

import re

from engines.device.action import System, open_device
from utils.logs import device_log

SYSTEM_UI = "com.android.systemui"
FALLBACK_LAUNCHERS = frozenset(
    {
        "com.android.launcher3",
        "com.google.android.apps.nexuslauncher",
        "com.sec.android.app.launcher",
        "com.miui.home",
        "com.huawei.android.launcher",
    }
)
_PACKAGE_IN_RECENTS = re.compile(r"(?:realActivity=|cmp=)([\w.]+)/")
_HOME_CMD = [
    "cmd",
    "package",
    "resolve-activity",
    "--brief",
    "-a",
    "android.intent.action.MAIN",
    "-c",
    "android.intent.category.HOME",
]


def _write_line(action: str) -> None:
    device_log.info(" ".join(str(action or "").split()) or "-")


def parse_recent_packages(text: str) -> list[str]:
    found: list[str] = []
    for match in _PACKAGE_IN_RECENTS.finditer(text or ""):
        name = match.group(1)
        if name and name not in found:
            found.append(name)
    return found


def parse_home_package(text: str) -> str:
    for line in reversed((text or "").splitlines()):
        item = line.strip()
        if "/" not in item or "=" in item:
            continue
        return item.split("/", 1)[0].strip()
    return ""


def packages_to_stop(packages: list[str], home_package: str) -> list[str]:
    skip = {SYSTEM_UI}
    home = str(home_package or "").strip()
    if home:
        skip.add(home)
    else:
        skip.update(FALLBACK_LAUNCHERS)
    return [name for name in packages if name and name not in skip]


def close_recent_apps(serial: str, *, opener=None) -> None:
    target = str(serial or "").strip()
    if not target:
        _write_line("收尾跳过：设备序列号为空")
        return
    open_target = opener or _open_android
    connection = None
    try:
        connection, info, control = open_target(target)
        recent = parse_recent_packages(info.adb.shell(["dumpsys", "activity", "recents"]))
        home = parse_home_package(_read_home(info))
        names = packages_to_stop(recent, home)
        for package in names:
            control.app_stop(package)
        control.press_key("home")
        shown = "、".join(names) if names else "无"
        _write_line(f"收尾关闭应用：{shown}")
    except Exception as exc:
        _write_line(f"收尾关闭应用失败：{exc}")
    finally:
        if connection is not None:
            connection.disconnect()


def _read_home(info) -> str:
    try:
        return str(info.adb.shell(_HOME_CMD) or "")
    except Exception:
        return ""


def _open_android(serial: str):
    return open_device(System.ANDROID, serial)
