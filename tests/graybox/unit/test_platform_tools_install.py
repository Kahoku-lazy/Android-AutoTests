"""platform-tools 安装器：校验、解压、幂等与失败不落位。

用本地假 zip 代替网络下载，自检与 chmod 用替身，测试不联网、不执行真实 adb。
"""

from __future__ import annotations

import hashlib
import zipfile

from pathlib import Path

import pytest

from utils import platform_tools

pytestmark = [pytest.mark.unit]


def _make_zip(path: Path, entries: dict[str, bytes]) -> Path:
    """生成一个指定条目内容的 zip。"""
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


def _info_for(zip_path: Path) -> dict:
    """按假 zip 的真实大小/校验和生成归档元数据。"""
    data = zip_path.read_bytes()
    return {
        "file": zip_path.name,
        "size": len(data),
        "sha1": hashlib.sha1(data).hexdigest(),
        "url": "file://" + str(zip_path),
    }


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    """把安装目录/缓存目录挪到临时目录，自检用替身。"""
    monkeypatch.setattr(platform_tools, "INSTALL_DIR", tmp_path / "tools" / "platform-tools")
    monkeypatch.setattr(platform_tools, "CACHE_DIR", tmp_path / "tools" / ".cache")
    monkeypatch.setattr(
        platform_tools,
        "_self_check",
        lambda adb_path: "Android Debug Bridge version 9.9.9-test",
    )
    return tmp_path


def _payload() -> dict[str, bytes]:
    """一份最小可用的 platform-tools 归档内容。"""
    return {
        f"platform-tools/{platform_tools._ADB_NAME}": b"fake-adb",
        "platform-tools/fastboot": b"fake-fastboot",
    }


def test_install_from_file_creates_meta(sandbox, monkeypatch):
    """离线 zip 安装成功：adb 落位、元数据记录版本与校验值。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", _payload())
    info = _info_for(zip_path)
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: info)

    result = platform_tools.install(archive=zip_path, log=lambda *_: None)

    adb = platform_tools.installed_adb()
    assert result["result"] == "installed"
    assert adb is not None and adb.is_file()
    meta = platform_tools.read_meta()
    assert meta["version"] == platform_tools.ARCHIVE_VERSION
    assert meta["sha1"] == info["sha1"]
    assert meta["sha256"] == hashlib.sha256(zip_path.read_bytes()).hexdigest()
    assert platform_tools.status()["installed"] is True


def test_install_is_idempotent(sandbox, monkeypatch):
    """已安装且校验一致时不重复安装。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", _payload())
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: _info_for(zip_path))

    platform_tools.install(archive=zip_path, log=lambda *_: None)
    second = platform_tools.install(archive=zip_path, log=lambda *_: None)

    assert second["result"] == "already"


def test_force_reinstalls(sandbox, monkeypatch):
    """--force 时即使已安装也重新解压。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", _payload())
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: _info_for(zip_path))

    platform_tools.install(archive=zip_path, log=lambda *_: None)
    again = platform_tools.install(archive=zip_path, force=True, log=lambda *_: None)

    assert again["result"] == "installed"


def test_size_mismatch_rejects(sandbox, monkeypatch):
    """大小不符直接失败，不落位。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", _payload())
    info = _info_for(zip_path)
    info["size"] = info["size"] + 1
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: info)

    with pytest.raises(platform_tools.PlatformToolsError, match="大小不符"):
        platform_tools.install(archive=zip_path, log=lambda *_: None)

    assert platform_tools.installed_adb() is None


def test_sha1_mismatch_rejects(sandbox, monkeypatch):
    """校验和不符直接失败，不落位。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", _payload())
    info = _info_for(zip_path)
    info["sha1"] = "0" * 40
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: info)

    with pytest.raises(platform_tools.PlatformToolsError, match="校验和不符"):
        platform_tools.install(archive=zip_path, log=lambda *_: None)

    assert platform_tools.installed_adb() is None


def test_zip_slip_rejected(sandbox, monkeypatch):
    """含 `..` 的条目被拒绝，安装目录不产生。"""
    zip_path = _make_zip(
        sandbox / "platform-tools.zip",
        {f"platform-tools/{platform_tools._ADB_NAME}": b"fake-adb", "../evil.txt": b"x"},
    )
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: _info_for(zip_path))

    with pytest.raises(platform_tools.PlatformToolsError, match="非法路径"):
        platform_tools.install(archive=zip_path, log=lambda *_: None)

    assert platform_tools.installed_adb() is None


def test_missing_adb_inside_archive_rejected(sandbox, monkeypatch):
    """归档里没有 adb 时报错，不落位。"""
    zip_path = _make_zip(sandbox / "platform-tools.zip", {"platform-tools/fastboot": b"x"})
    monkeypatch.setattr(platform_tools, "_archive_info", lambda: _info_for(zip_path))

    with pytest.raises(platform_tools.PlatformToolsError, match="没有"):
        platform_tools.install(archive=zip_path, log=lambda *_: None)

    assert platform_tools.installed_adb() is None
