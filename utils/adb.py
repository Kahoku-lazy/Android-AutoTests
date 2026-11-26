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
    pass


def _usable(path: Path) -> bool:
    if not path.is_file():
        return False
    return _IS_WINDOWS or os.access(path, os.X_OK)


def _platform_adb() -> Path:
    return _PLATFORM_TOOLS_DIR / _ADB_NAME


def _bundled_adb() -> Path | None:
    try:
        import adbutils
    except Exception:  # noqa: BLE001 - 依赖缺失只是这一档不可用，不影响其它来源
        return None
    candidate = Path(adbutils.__file__).resolve().parent / "binaries" / _ADB_NAME
    return candidate if _usable(candidate) else None


def _resolve() -> tuple[str, str]:
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
    _, path = _resolve()
    os.environ["ADBUTILS_ADB_PATH"] = path
    if _IS_WINDOWS:
        os.environ.setdefault("ANDROID_ADB_LOG_PATH", os.devnull)
    return path


def adb_status() -> dict:
    try:
        source, path = _resolve()
    except AdbUnavailableError:
        return {"source": "missing", "path": None}
    return {"source": source, "path": path}


def reset_cache() -> None:
    global _resolved
    _resolved = None
