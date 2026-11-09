"""adb 解析器契约：平台自带优先，不回退系统 PATH。

对应变更 adb-platform-bootstrap 的「adb 只使用平台自带来源」需求。
"""

from __future__ import annotations

import os

import pytest

from utils import adb as adb_tools

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个用例前后清空解析缓存，避免用例间串味。"""
    adb_tools.reset_cache()
    yield
    adb_tools.reset_cache()


def _make_adb(path, content="fake"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_env_path_wins(monkeypatch, tmp_path):
    """ADB_PATH 存在且可执行时优先。"""
    env_adb = _make_adb(tmp_path / "custom" / adb_tools._ADB_NAME)
    monkeypatch.setenv("ADB_PATH", str(env_adb))
    _make_adb(tmp_path / "platform" / adb_tools._ADB_NAME)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "platform")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: None)

    assert adb_tools.adb_binary() == str(env_adb.resolve())
    assert adb_tools.adb_status()["source"] == "env"


def test_platform_dir_wins_over_bundled(monkeypatch, tmp_path):
    """项目内 tools/platform-tools 优先于 adbutils 内置。"""
    monkeypatch.delenv("ADB_PATH", raising=False)
    platform_adb = _make_adb(tmp_path / "platform" / adb_tools._ADB_NAME)
    bundled_adb = _make_adb(tmp_path / "bundled" / adb_tools._ADB_NAME)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "platform")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: bundled_adb)

    assert adb_tools.adb_binary() == str(platform_adb.resolve())
    assert adb_tools.adb_status()["source"] == "platform"


def test_bundled_used_when_no_platform_copy(monkeypatch, tmp_path):
    """没有项目内副本时使用依赖包内置的 adb。"""
    monkeypatch.delenv("ADB_PATH", raising=False)
    bundled_adb = _make_adb(tmp_path / "bundled" / adb_tools._ADB_NAME)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "empty")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: bundled_adb)

    assert adb_tools.adb_binary() == str(bundled_adb.resolve())
    assert adb_tools.adb_status()["source"] == "bundled"


def test_path_adb_is_ignored(monkeypatch, tmp_path):
    """系统 PATH 上有 adb 也不能被选中。"""
    fake_bin = tmp_path / "fakebin"
    _make_adb(fake_bin / adb_tools._ADB_NAME)
    monkeypatch.setenv("PATH", str(fake_bin))
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "empty")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: None)

    with pytest.raises(adb_tools.AdbUnavailableError) as excinfo:
        adb_tools.adb_binary()

    assert "run.py setup" in str(excinfo.value)


def test_missing_sources_report_actionable_error(monkeypatch, tmp_path):
    """三档都缺失时报错并给出安装命令；状态显示 missing。"""
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "empty")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: None)

    with pytest.raises(adb_tools.AdbUnavailableError):
        adb_tools.adb_binary()
    assert adb_tools.adb_status() == {"source": "missing", "path": None}


def test_resolution_is_synced_to_adbutils(monkeypatch, tmp_path):
    """解析成功后把路径写进 ADBUTILS_ADB_PATH，保证 u2 使用同一份。"""
    bundled_adb = _make_adb(tmp_path / "bundled" / adb_tools._ADB_NAME)
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "empty")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: bundled_adb)
    monkeypatch.delenv("ADBUTILS_ADB_PATH", raising=False)

    resolved = adb_tools.adb_binary()

    assert os.environ["ADBUTILS_ADB_PATH"] == resolved


def test_windows_disables_adb_daemon_log(monkeypatch, tmp_path):
    """Windows 上把 adb daemon 日志指到 NUL（规避 adb 37 写 %TEMP% 被拒的环境问题）。"""
    if os.name != "nt":
        pytest.skip("仅 Windows 需要该规避")

    bundled_adb = _make_adb(tmp_path / "bundled" / adb_tools._ADB_NAME)
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.delenv("ANDROID_ADB_LOG_PATH", raising=False)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "empty")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: bundled_adb)

    adb_tools.adb_binary()

    assert os.environ["ANDROID_ADB_LOG_PATH"] == os.devnull


def test_reset_cache_picks_up_new_install(monkeypatch, tmp_path):
    """安装器落位后 reset_cache 能解析到新路径。"""
    platform_adb = tmp_path / "platform" / adb_tools._ADB_NAME
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(adb_tools, "_PLATFORM_TOOLS_DIR", tmp_path / "platform")
    monkeypatch.setattr(adb_tools, "_bundled_adb", lambda: None)

    first = _make_adb(platform_adb)
    assert adb_tools.adb_binary() == str(first.resolve())

    platform_adb.unlink()
    adb_tools.reset_cache()
    with pytest.raises(adb_tools.AdbUnavailableError):
        adb_tools.adb_binary()

    adb_tools.reset_cache()
    _make_adb(platform_adb)
    assert adb_tools.adb_binary() == str(platform_adb.resolve())
