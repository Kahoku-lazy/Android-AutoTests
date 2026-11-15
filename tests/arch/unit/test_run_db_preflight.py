"""run.py 数据库前置检查：探测、本机服务启动、失败中止与开关。

只测 run.py 的启动编排，不真连数据库：MySQLdb 与 subprocess 都用替身。
"""

from __future__ import annotations

import sys

import pytest

import run


class _FakeConn:
    """MySQLdb 连接替身。"""

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _quiet(monkeypatch):
    """避免测试期间真的 sleep / 起服务。"""
    monkeypatch.setattr(run.time, "sleep", lambda *_: None)


def _cfg(**over):
    base = {
        "engine": "mysql",
        "host": "127.0.0.1",
        "port": 3306,
        "user": "u",
        "password": "p",
        "name": "db",
        "service": "MySQL" if sys.platform == "win32" else "mysql",
    }
    base.update(over)
    return base


def test_sqlite_skips_connection():
    """sqlite 不连服务，直接视为可用。"""
    assert run._db_reachable(_cfg(engine="sqlite"))[0] is True


def test_mysql_connect_success(monkeypatch):
    """连通时返回 True。"""
    import MySQLdb

    monkeypatch.setattr(MySQLdb, "connect", lambda **_: _FakeConn())
    assert run._db_reachable(_cfg()) == (True, "")


def test_mysql_connect_failure(monkeypatch):
    """连接异常转成可读摘要，不抛出。"""
    import MySQLdb

    def _boom(**_):
        raise RuntimeError("Access denied for user")

    monkeypatch.setattr(MySQLdb, "connect", _boom)
    ok, detail = run._db_reachable(_cfg())
    assert ok is False
    assert "Access denied" in detail


@pytest.mark.parametrize(
    ("host", "expected"),
    [("127.0.0.1", True), ("localhost", True), ("::1", True), ("10.0.0.5", False)],
)
def test_is_loopback(host, expected):
    assert run._is_loopback(host) is expected


def test_status_line_states(monkeypatch):
    """status 行覆盖 ONLINE / OFFLINE / SQLite。"""
    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (True, ""))
    assert "ONLINE" in run._db_status_line()

    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (False, "down"))
    assert "OFFLINE" in run._db_status_line()

    monkeypatch.setattr(run, "_db_config", lambda: _cfg(engine="sqlite"))
    assert "SQLite" in run._db_status_line()


def test_start_local_service_command(monkeypatch):
    """按平台选启动命令；成功返回 True。"""
    captured = {}

    class _Proc:
        returncode = 0
        stdout = "started"
        stderr = ""

    def _run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _Proc()

    monkeypatch.setattr(run.subprocess, "run", _run)
    ok, _ = run._start_local_db_service(_cfg())
    assert ok is True
    if sys.platform == "win32":
        assert captured["cmd"][:2] == ["sc.exe", "start"]
    elif sys.platform == "darwin":
        assert captured["cmd"][:3] == ["brew", "services", "start"]
    else:
        assert captured["cmd"][:2] == ["systemctl", "start"]


def test_ensure_db_reachable(monkeypatch):
    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (True, ""))
    assert run._ensure_db(_cfg(), allow_autostart=True) is True


def test_ensure_db_remote_never_starts(monkeypatch, capsys):
    """远程库不可达只报错，不尝试启动服务。"""
    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (False, "refused"))
    called = {"start": False}
    monkeypatch.setattr(
        run, "_start_local_db_service", lambda cfg: called.update(start=True) or (True, "")
    )

    assert run._ensure_db(_cfg(host="10.0.0.5"), allow_autostart=True) is False
    assert called["start"] is False
    assert "远程" in capsys.readouterr().out


def test_ensure_db_autostart_disabled(monkeypatch, capsys):
    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (False, "down"))
    assert run._ensure_db(_cfg(), allow_autostart=False) is False
    out = capsys.readouterr().out
    assert "DB_AUTOSTART=0" in out
    assert "net start" in out or "systemctl" in out or "brew" in out


def test_ensure_db_start_succeeds(monkeypatch):
    """先失败一次、启动后复检成功。"""
    calls = {"n": 0}

    def _reachable(cfg):
        calls["n"] += 1
        return (calls["n"] > 1, "" if calls["n"] > 1 else "down")

    monkeypatch.setattr(run, "_db_reachable", _reachable)
    monkeypatch.setattr(run, "_start_local_db_service", lambda cfg: (True, ""))
    assert run._ensure_db(_cfg(), allow_autostart=True) is True


def test_ensure_db_start_denied(monkeypatch, capsys):
    """启动失败时输出原始原因 + 提权命令。"""
    monkeypatch.setattr(run, "_db_reachable", lambda cfg: (False, "down"))
    monkeypatch.setattr(run, "_start_local_db_service", lambda cfg: (False, "Access is denied."))
    assert run._ensure_db(_cfg(), allow_autostart=True) is False
    out = capsys.readouterr().out
    assert "Access is denied." in out
    assert "net start" in out or "systemctl" in out or "brew" in out


def test_cmd_start_aborts_when_db_unavailable(monkeypatch, capsys):
    """数据库不可用时一个服务都不启动。"""
    started = []
    monkeypatch.setattr(run, "resolve_services", lambda names: ["backend"])
    monkeypatch.setattr(run, "_ensure_db", lambda cfg, allow_autostart: False)
    monkeypatch.setattr(run, "_STOP", {"backend": lambda: None})
    monkeypatch.setattr(run, "_START", {"backend": lambda: started.append("backend") or True})

    run.cmd_start(["backend"])

    assert started == []
    assert "Aborted" in capsys.readouterr().out


def test_cmd_start_no_db_skips_check(monkeypatch):
    """--no-db 跳过检查，仍正常启动。"""
    started = []
    monkeypatch.setattr(run, "resolve_services", lambda names: ["backend"])
    monkeypatch.setattr(run, "_ensure_db", lambda *a, **k: pytest.fail("不应检查数据库"))
    monkeypatch.setattr(run, "_ensure_adb", lambda: None)
    monkeypatch.setattr(run, "_STOP", {"backend": lambda: None})
    monkeypatch.setattr(run, "_START", {"backend": lambda: started.append("backend") or True})

    run.cmd_start(["backend"], skip_db=True)

    assert started == ["backend"]


def test_cleanup_mysql_skips_sqlite(monkeypatch):
    """sqlite 不清理 MySQL 连接。"""
    import MySQLdb

    monkeypatch.setenv("DB_ENGINE", "sqlite")
    monkeypatch.setattr(MySQLdb, "connect", lambda **_: pytest.fail("sqlite 不应连接 MySQL"))
    run.cleanup_mysql_connections()


def test_cleanup_mysql_passes_password(monkeypatch):
    """清理连接时必须带 DB_PASSWORD（此前漏传导致 Access denied）。"""
    import MySQLdb

    captured = {}

    class _Cursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return []

        def close(self):
            pass

    class _Conn:
        def cursor(self):
            return _Cursor()

        def close(self):
            pass

    def _connect(**kwargs):
        captured.update(kwargs)
        return _Conn()

    monkeypatch.setenv("DB_ENGINE", "mysql")
    monkeypatch.setenv("DB_PASSWORD", "secret-pw")
    monkeypatch.setattr(MySQLdb, "connect", _connect)

    run.cleanup_mysql_connections()

    assert captured["passwd"] == "secret-pw"
