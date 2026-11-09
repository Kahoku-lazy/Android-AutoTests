"""adb 可执行文件解析：平台自带优先，不回退系统 PATH。

业务功能：
1. adb_binary: 按优先级返回本次进程应使用的 adb 路径，并同步给 adbutils/uiautomator2。
2. adb_status: 只读地报告当前来源（env / platform / bundled / missing），供状态面板与排障使用。
3. reset_cache: 安装器完成安装后强制重新解析。

优先级（命中即可用）：
1. `ADB_PATH` 环境变量（显式覆盖）；
2. 项目内 `tools/platform-tools/adb(.exe)`（`python run.py setup` 安装到这里）；
3. Python 依赖 `adbutils` 包内置的 adb。
系统 PATH 不在候选列表中：版本不可控，且静默使用会掩盖部署配置问题。
"""

from __future__ import annotations

import os

from pathlib import Path

__all__ = ["AdbUnavailableError", "adb_binary", "adb_status", "reset_cache"]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PLATFORM_TOOLS_DIR = _REPO_ROOT / "tools" / "platform-tools"
_IS_WINDOWS = os.name == "nt"
_ADB_NAME = "adb.exe" if _IS_WINDOWS else "adb"

_MISSING_MESSAGE = (
    "未找到可用的 adb：请运行 `python run.py setup` 安装平台自带 platform-tools，"
    "或设置 ADB_PATH 指向已有 adb。"
)

_resolved: tuple[str, str] | None = None


class AdbUnavailableError(RuntimeError):
    """adb 的所有来源都不可用时抛出；message 直接面向用户，包含修复命令。"""


def _usable(path: Path) -> bool:
    """判断候选路径是否是当前系统可执行的 adb。"""
    if not path.is_file():
        return False
    return _IS_WINDOWS or os.access(path, os.X_OK)


def _platform_adb() -> Path:
    """项目内安装目录中的 adb 路径（未必存在）。"""
    return _PLATFORM_TOOLS_DIR / _ADB_NAME


def _bundled_adb() -> Path | None:
    """adbutils 依赖包内置的 adb 路径；未安装或该平台无内置时返回 None。"""
    try:
        import adbutils
    except Exception:  # noqa: BLE001 - 依赖缺失只是这一档不可用，不影响其它来源
        return None
    candidate = Path(adbutils.__file__).resolve().parent / "binaries" / _ADB_NAME
    return candidate if _usable(candidate) else None


def _resolve() -> tuple[str, str]:
    """按优先级解析一次并缓存：返回 (来源标签, 绝对路径)。"""
    global _resolved
    if _resolved is not None:
        return _resolved

    env_path = os.environ.get("ADB_PATH", "").strip()
    if env_path and _usable(Path(env_path)):
        _resolved = ("env", str(Path(env_path).resolve()))
        return _resolved

    platform_path = _platform_adb()
    if _usable(platform_path):
        _resolved = ("platform", str(platform_path.resolve()))
        return _resolved

    bundled = _bundled_adb()
    if bundled is not None:
        _resolved = ("bundled", str(bundled.resolve()))
        return _resolved

    raise AdbUnavailableError(_MISSING_MESSAGE)


def adb_binary() -> str:
    """返回本次进程应使用的 adb 路径，并让 adbutils/uiautomator2 复用它。

    Returns:
        str: adb 可执行文件的绝对路径。

    Raises:
        AdbUnavailableError: `ADB_PATH`、项目内安装、adbutils 内置三者都不可用。
    """
    _, path = _resolve()
    # 覆盖而不是 setdefault：以本解析器为唯一权威，避免进程外残留的旧值让 u2 用错二进制
    os.environ["ADBUTILS_ADB_PATH"] = path
    if _IS_WINDOWS:
        # adb 37 的 daemon 会把日志写到 %TEMP%\adb.log；部分 Windows 策略下该文件打不开，
        # daemon 直接起不来（实测报 main.cpp:54 cannot open ...: Permission denied）。
        # 平台统一把 daemon 日志指向 NUL：客户端 stderr 仍可看到错误，不影响功能。
        os.environ.setdefault("ANDROID_ADB_LOG_PATH", os.devnull)
    return path


def adb_status() -> dict:
    """只读报告当前 adb 来源，不抛异常（供状态面板与排障使用）。

    Returns:
        dict: {"source": "env|platform|bundled|missing", "path": str | None}。
    """
    try:
        source, path = _resolve()
    except AdbUnavailableError:
        return {"source": "missing", "path": None}
    return {"source": source, "path": path}


def reset_cache() -> None:
    """清空解析缓存；安装器写入新 adb 后调用，使下一次解析拿到新路径。"""
    global _resolved
    _resolved = None
