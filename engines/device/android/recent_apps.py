"""
python -m 调试路径: engines.device.android.recent_apps

本模块的业务功能如下：
1. parse_recent_packages: 从最近任务原文取出包名。
2. packages_to_stop: 去掉桌面和系统界面。
3. close_recent_apps: 停掉这些应用并回到桌面。
"""

from __future__ import annotations

import re

from engines.agents.event_log import write_line
from engines.device.action import System, open_device

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


def parse_recent_packages(text: str) -> list[str]:
    """从 `dumpsys activity recents` 原文取包名，按出现顺序去重。"""
    found: list[str] = []
    for match in _PACKAGE_IN_RECENTS.finditer(text or ""):
        name = match.group(1)
        if name and name not in found:
            found.append(name)
    return found


def parse_home_package(text: str) -> str:
    """从桌面 Activity 解析结果取包名。取不到时返回空串。"""
    for line in reversed((text or "").splitlines()):
        item = line.strip()
        if "/" not in item or "=" in item:
            continue
        return item.split("/", 1)[0].strip()
    return ""


def packages_to_stop(packages: list[str], home_package: str) -> list[str]:
    """留下要停止的包。系统界面始终跳过；桌面解析到了就跳过它，否则跳过常见桌面。"""
    skip = {SYSTEM_UI}
    home = str(home_package or "").strip()
    if home:
        skip.add(home)
    else:
        skip.update(FALLBACK_LAUNCHERS)
    return [name for name in packages if name and name not in skip]


def close_recent_apps(serial: str, *, opener=None) -> None:
    """停掉最近任务里的非桌面应用，再按 Home。失败只记日志。

    Args:
        serial: 设备序列号。
        opener: 替身。省略时打开真机。返回 (连接, 信息, 控制)。
    """
    target = str(serial or "").strip()
    if not target:
        write_line("-", "收尾跳过：设备序列号为空")
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
        write_line("-", f"收尾关闭应用：{shown}")
    except Exception as exc:
        write_line("-", f"收尾关闭应用失败：{exc}")
    finally:
        if connection is not None:
            connection.disconnect()


def _read_home(info) -> str:
    """读桌面解析结果。命令失败时当作没有解析到。"""
    try:
        return str(info.adb.shell(_HOME_CMD) or "")
    except Exception:
        return ""


def _open_android(serial: str):
    """打开一台安卓设备。"""
    return open_device(System.ANDROID, serial)
