from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "ARCHIVE_VERSION",
    "PlatformToolsError",
    "install",
    "install_dir",
    "installed_adb",
    "read_meta",
    "status",
]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TOOLS_DIR = _REPO_ROOT / "tools"
INSTALL_DIR = _TOOLS_DIR / "platform-tools"
CACHE_DIR = _TOOLS_DIR / ".cache"
_META_NAME = ".platform-tools.json"
_IS_WINDOWS = os.name == "nt"
_ADB_NAME = "adb.exe" if _IS_WINDOWS else "adb"

ARCHIVE_VERSION = "37.0.2"
_BASE_URL = "https://dl.google.com/android/repository/"
_ARCHIVES = {
    "Windows": {
        "file": f"platform-tools_r{ARCHIVE_VERSION}-win.zip",
        "size": 8239125,
        "sha1": "d7ee482b3874f1e0d6d5dca135f6bd58f5716db0",
    },
    "Darwin": {
        "file": f"platform-tools_r{ARCHIVE_VERSION}-darwin.zip",
        "size": 16516152,
        "sha1": "6f86aa58ba42dd4bfe27477f3f11c09edc3ebe3f",
    },
    "Linux": {
        "file": f"platform-tools_r{ARCHIVE_VERSION}-linux.zip",
        "size": 9541228,
        "sha1": "736a08af10515674e40d8b754fe87390d698da2b",
    },
}


class PlatformToolsError(RuntimeError):
    pass


def install_dir() -> Path:
    return INSTALL_DIR


def platform_key() -> str:
    key = platform.system()
    if key not in _ARCHIVES:
        raise PlatformToolsError(f"当前系统 {key or '未知'} 没有对应的 platform-tools 归档")
    return key


def _archive_info() -> dict:
    info = dict(_ARCHIVES[platform_key()])
    info["url"] = _BASE_URL + info["file"]
    return info


def installed_adb() -> Path | None:
    candidate = INSTALL_DIR / _ADB_NAME
    return candidate if candidate.is_file() else None


def read_meta() -> dict:
    path = INSTALL_DIR / _META_NAME
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _sha1_of(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(zip_path: Path, info: dict | None = None) -> str:
    info = info or _archive_info()
    if not zip_path.is_file():
        raise PlatformToolsError(f"找不到压缩包：{zip_path}")
    size = zip_path.stat().st_size
    if size != info["size"]:
        raise PlatformToolsError(
            f"压缩包大小不符：期望 {info['size']} 字节，实际 {size} 字节（{info['file']}）"
        )
    actual_sha1 = _sha1_of(zip_path)
    if actual_sha1.lower() != info["sha1"].lower():
        raise PlatformToolsError(
            f"压缩包校验和不符：期望 {info['sha1']}，实际 {actual_sha1}（{info['file']}）"
        )
    return _sha256_of(zip_path)


def _download(url: str, dest: Path) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "Android-AutoTests-setup"})
    try:
        with urllib.request.urlopen(request, timeout=180) as resp, part.open("wb") as fh:
            shutil.copyfileobj(resp, fh, length=1024 * 1024)
    except Exception as exc:  # noqa: BLE001 - 网络错误统一转成面向用户的安装错误
        part.unlink(missing_ok=True)
        raise PlatformToolsError(f"下载失败：{url}（{exc}）") from exc
    part.replace(dest)


def _safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = member.filename.replace("\\", "/")
            parts = Path(name).parts
            if name.startswith("/") or ".." in parts:
                raise PlatformToolsError(f"压缩包包含非法路径：{member.filename}")
        zf.extractall(dest)


def _chmod_adb(adb_path: Path) -> None:
    if not _IS_WINDOWS:
        adb_path.chmod(0o755)


def _kill_server(adb_path: Path) -> None:
    try:
        subprocess.run([str(adb_path), "kill-server"], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return


def _self_check(adb_path: Path) -> str:
    try:
        proc = subprocess.run(
            [str(adb_path), "version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PlatformToolsError(f"安装后自检失败：{exc}") from exc
    text = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0 or "Android Debug Bridge" not in text:
        raise PlatformToolsError(f"安装后自检失败：{text[:200] or '无输出'}")
    return text.splitlines()[0].strip()


def _publish(src: Path, meta: dict) -> None:
    INSTALL_DIR.parent.mkdir(parents=True, exist_ok=True)
    backup = INSTALL_DIR.with_name(f"{INSTALL_DIR.name}.old")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    if INSTALL_DIR.exists():
        INSTALL_DIR.rename(backup)
    try:
        shutil.move(str(src), str(INSTALL_DIR))
    except Exception:
        if backup.exists():
            if INSTALL_DIR.exists():
                shutil.rmtree(INSTALL_DIR, ignore_errors=True)
            backup.rename(INSTALL_DIR)
        raise
    shutil.rmtree(backup, ignore_errors=True)
    (INSTALL_DIR / _META_NAME).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def install(force: bool = False, archive: str | Path | None = None, log=print) -> dict:
    info = _archive_info()
    meta = read_meta()
    adb = installed_adb()
    if (
        adb
        and not force
        and meta.get("version") == ARCHIVE_VERSION
        and meta.get("sha1") == info["sha1"]
    ):
        log(f"  platform-tools 已安装：{adb}（{ARCHIVE_VERSION}）")
        return {
            "result": "already",
            "path": str(INSTALL_DIR),
            "version": ARCHIVE_VERSION,
            "adb": str(adb),
        }

    zip_path: Path
    if archive:
        zip_path = Path(archive)
        log(f"  使用离线压缩包：{zip_path}")
    else:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = CACHE_DIR / info["file"]
        if force or not zip_path.is_file():
            log(f"  下载 {info['url']} ...")
            _download(info["url"], zip_path)
        else:
            log(f"  复用缓存压缩包：{zip_path}")

    sha256 = verify_archive(zip_path, info)
    log("  校验通过，开始解压 ...")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="platform-tools-", dir=CACHE_DIR))
    try:
        _safe_extract(zip_path, workdir)
        src = workdir / "platform-tools"
        if not src.is_dir():
            src = workdir
        adb_src = src / _ADB_NAME
        if not adb_src.is_file():
            raise PlatformToolsError(f"压缩包内没有 {_ADB_NAME}：{zip_path}")
        _chmod_adb(adb_src)
        version_line = _self_check(adb_src)
        old_adb = installed_adb()
        if old_adb is not None:
            _kill_server(old_adb)
        meta = {
            "version": ARCHIVE_VERSION,
            "platform": platform_key(),
            "archive": info["file"],
            "size": info["size"],
            "sha1": info["sha1"],
            "sha256": sha256,
            "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        _publish(src, meta)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    from utils import adb as adb_tools

    adb_tools.reset_cache()
    final_adb = installed_adb()
    log(f"  安装完成：{final_adb}")
    log(f"  {version_line}")
    return {
        "result": "installed",
        "path": str(INSTALL_DIR),
        "version": ARCHIVE_VERSION,
        "adb": str(final_adb) if final_adb else "",
    }


def status() -> dict:
    from utils import adb as adb_tools

    adb = installed_adb()
    meta = read_meta()
    return {
        "installed": adb is not None,
        "path": str(INSTALL_DIR) if adb else None,
        "version": meta.get("version"),
        "source": adb_tools.adb_status()["source"],
    }
