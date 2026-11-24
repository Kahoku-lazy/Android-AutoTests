"""
模块功能：➡️ `utils.service_ctl.db` 的数据库前置检查：探测、本机服务启动、失败中止与开关 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_run_db_preflight.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 utils/service_ctl
🏁
"""

from __future__ import annotations

import sys

import pytest

from utils.service_ctl import db as dbmod
from utils.service_ctl.db import DbConfig

pytestmark = [pytest.mark.unit]


class _FakeConn:
    """MySQLdb 连接替身。"""

    def close(self) -> None:
        pass


def _cfg(**over) -> DbConfig:
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
    return DbConfig(**base)


def test_from_env_reads_all_fields(monkeypatch):
    """连接参数全部来自环境变量，引擎值统一小写。"""
    monkeypatch.setenv("DB_ENGINE", "MySQL")
    monkeypatch.setenv("DB_HOST", "10.1.2.3")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_USER", "alice")
    monkeypatch.setenv("DB_PASSWORD", "pw")
    monkeypatch.setenv("DB_NAME", "demo")
    monkeypatch.setenv("DB_SERVICE_NAME", "MariaDB")

    cfg = DbConfig.from_env()

    assert cfg.engine == "mysql"
    assert (cfg.host, cfg.port, cfg.user, cfg.password, cfg.name, cfg.service) == (
        "10.1.2.3",
        3307,
        "alice",
        "pw",
        "demo",
        "MariaDB",
    )


def test_sqlite_skips_connection():
    """sqlite 不连服务，直接视为可用。"""
    assert dbmod.reachable(_cfg(engine="sqlite"))[0] is True


def test_mysql_connect_success(monkeypatch):
    """连通时返回 True。"""
    import MySQLdb

    monkeypatch.setattr(MySQLdb, "connect", lambda **_: _FakeConn())
    assert dbmod.reachable(_cfg()) == (True, "")


def test_mysql_connect_failure(monkeypatch):
    """连接异常转成可读摘要，不抛出。"""
    import MySQLdb

    def _boom(**_):
        raise RuntimeError("Access denied for user")

    monkeypatch.setattr(MySQLdb, "connect", _boom)
    ok, detail = dbmod.reachable(_cfg())
    assert ok is False
    assert "Access denied" in detail


@pytest.mark.parametrize(
    ("host", "expected"),
    [("127.0.0.1", True), ("localhost", True), ("::1", True), ("10.0.0.5", False)],
)
def test_is_loopback(host, expected):
    assert dbmod.is_loopback(host) is expected


def test_status_line_states(monkeypatch):
    """status 行覆盖 ONLINE / OFFLINE / SQLite。"""
    monkeypatch.setenv("DB_ENGINE", "mysql")
    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (True, ""))
    assert "ONLINE" in dbmod.status_line()

    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (False, "down"))
    assert "OFFLINE" in dbmod.status_line()

    monkeypatch.setenv("DB_ENGINE", "sqlite")
    assert "SQLite" in dbmod.status_line()


def test_start_local_service_command(monkeypatch):
    """按平台选启动命令；成功返回 True。"""
    captured = {}

    class _Proc:
        returncode = 0
        stdout = "started"
        stderr = ""

    def _run(command, **kwargs):
        captured["cmd"] = command
        return _Proc()

    monkeypatch.setattr(dbmod.subprocess, "run", _run)
    ok, _ = dbmod.start_local_service(_cfg())
    assert ok is True
    if sys.platform == "win32":
        assert captured["cmd"][:2] == ["sc.exe", "start"]
    elif sys.platform == "darwin":
        assert captured["cmd"][:3] == ["brew", "services", "start"]
    else:
        assert captured["cmd"][:2] == ["systemctl", "start"]


def test_ensure_db_reachable(monkeypatch):
    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (True, ""))
    assert dbmod.ensure(_cfg(), allow_autostart=True) is True


def test_ensure_db_remote_never_starts(monkeypatch, capsys):
    """远程库不可达只报错，不尝试启动服务。"""
    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (False, "refused"))
    called = {"start": False}
    monkeypatch.setattr(
        dbmod, "start_local_service", lambda cfg: called.update(start=True) or (True, "")
    )

    assert dbmod.ensure(_cfg(host="10.0.0.5"), allow_autostart=True) is False
    assert called["start"] is False
    assert "远程" in capsys.readouterr().out


def test_ensure_db_autostart_disabled(monkeypatch, capsys):
    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (False, "down"))
    assert dbmod.ensure(_cfg(), allow_autostart=False) is False
    out = capsys.readouterr().out
    assert "DB_AUTOSTART=0" in out
    assert "net start" in out or "systemctl" in out or "brew" in out


def test_ensure_db_start_succeeds(monkeypatch):
    """先失败一次、启动后复检成功。"""
    calls = {"n": 0}

    def _reachable(cfg):
        calls["n"] += 1
        return (calls["n"] > 1, "" if calls["n"] > 1 else "down")

    monkeypatch.setattr(dbmod, "reachable", _reachable)
    monkeypatch.setattr(dbmod, "start_local_service", lambda cfg: (True, ""))
    assert dbmod.ensure(_cfg(), allow_autostart=True) is True


def test_ensure_db_start_denied(monkeypatch, capsys):
    """启动失败时输出原始原因 + 提权命令。"""
    monkeypatch.setattr(dbmod, "reachable", lambda cfg: (False, "down"))
    monkeypatch.setattr(dbmod, "start_local_service", lambda cfg: (False, "Access is denied."))
    assert dbmod.ensure(_cfg(), allow_autostart=True) is False
    out = capsys.readouterr().out
    assert "Access is denied." in out
    assert "net start" in out or "systemctl" in out or "brew" in out


def test_cleanup_mysql_skips_sqlite(monkeypatch):
    """sqlite 不清理 MySQL 连接。"""
    import MySQLdb

    monkeypatch.setenv("DB_ENGINE", "sqlite")
    monkeypatch.setattr(MySQLdb, "connect", lambda **_: pytest.fail("sqlite 不应连接 MySQL"))
    dbmod.cleanup_idle_connections(DbConfig.from_env())


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

    dbmod.cleanup_idle_connections(DbConfig.from_env())

    assert captured["passwd"] == "secret-pw"
