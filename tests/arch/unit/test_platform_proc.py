"""
模块功能：➡️ `utils.service_ctl.proc` 的行为契约：端口/进程查找、结束策略、就绪等待、后台拉起 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_platform_proc.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 utils/service_ctl
🏁
"""

from __future__ import annotations

import subprocess

import pytest

from utils.service_ctl import proc

pytestmark = [pytest.mark.unit]


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0, command=None):
    return subprocess.CompletedProcess(command or [], returncode, stdout, stderr)


def test_find_listening_pid_windows(monkeypatch):
    """Windows：从 netstat 输出里取 LISTENING 行的 PID。"""
    monkeypatch.setattr(proc, "IS_WIN", True)
    output = (
        "  TCP    0.0.0.0:8766    0.0.0.0:0    LISTENING    1234\n"
        "  TCP    0.0.0.0:5173    0.0.0.0:0    LISTENING    9876\n"
    )
    monkeypatch.setattr(proc, "_run", lambda *a, **k: _completed(output))
    assert proc.find_listening_pid(8766) == "1234"


def test_find_listening_pid_posix(monkeypatch):
    """POSIX：取 lsof 输出的第一个 PID。"""
    monkeypatch.setattr(proc, "IS_WIN", False)
    monkeypatch.setattr(proc, "_run", lambda *a, **k: _completed(" 4321 \n"))
    assert proc.find_listening_pid(8766) == "4321"


def test_find_listening_pid_none_when_nothing_listens(monkeypatch):
    """没有监听或查询命令失败都返回 None，不抛错。"""
    monkeypatch.setattr(proc, "IS_WIN", False)
    monkeypatch.setattr(proc, "_run", lambda *a, **k: _completed(""))
    assert proc.find_listening_pid(8766) is None

    def _boom(*_a, **_k):
        raise OSError("lsof missing")

    monkeypatch.setattr(proc, "_run", _boom)
    assert proc.find_listening_pid(8766) is None


def test_pid_alive_windows(monkeypatch):
    """Windows：tasklist 输出包含 PID 即存活。"""
    monkeypatch.setattr(proc, "IS_WIN", True)
    monkeypatch.setattr(proc, "_run", lambda *a, **k: _completed("python.exe  1234 Console"))
    assert proc.pid_alive("1234") is True
    monkeypatch.setattr(proc, "_run", lambda *a, **k: _completed("INFO: No tasks"))
    assert proc.pid_alive("1234") is False


def test_kill_port_no_listener(monkeypatch):
    """端口没有监听：返回 False，不杀任何进程。"""
    monkeypatch.setattr(proc, "find_listening_pid", lambda port: None)
    kills: list = []
    monkeypatch.setattr(proc, "kill", lambda *a, **k: kills.append(a))
    assert proc.kill_port(8766) is False
    assert kills == []


def test_kill_port_graceful(monkeypatch, capsys):
    """优雅退出成功：打印 graceful，且不强制杀。"""
    monkeypatch.setattr(proc, "find_listening_pid", lambda port: "42")
    monkeypatch.setattr(proc, "graceful_kill", lambda pid: True)
    forced: list = []
    monkeypatch.setattr(proc, "kill", lambda *a, **k: forced.append(a))

    assert proc.kill_port(8766) is True
    assert "graceful" in capsys.readouterr().out
    assert forced == []


def test_kill_port_forced_when_graceful_times_out(monkeypatch, capsys):
    """优雅超时后强制杀，并打印 forced。"""
    monkeypatch.setattr(proc, "find_listening_pid", lambda port: "42")
    monkeypatch.setattr(proc, "graceful_kill", lambda pid: False)
    forced: list = []

    def _kill(pid, force=False):
        forced.append((pid, force))

    monkeypatch.setattr(proc, "kill", _kill)
    monkeypatch.setattr(proc.time, "sleep", lambda *_: None)

    assert proc.kill_port(8766) is True
    assert forced == [("42", True)]
    assert "forced" in capsys.readouterr().out


def test_wait_http_ready(monkeypatch):
    """一次成功即返回 True，不再轮询。"""
    calls: list = []

    def _urlopen(*_a, **_k):
        calls.append(1)
        return object()

    monkeypatch.setattr(proc.urllib.request, "urlopen", _urlopen)
    assert proc.wait_http("http://127.0.0.1:1/", timeout=5) is True
    assert len(calls) == 1


def test_wait_http_times_out(monkeypatch):
    """一直连不上：按 timeout 轮询后返回 False。"""

    def _boom(*_a, **_k):
        raise OSError("refused")

    monkeypatch.setattr(proc.urllib.request, "urlopen", _boom)
    monkeypatch.setattr(proc.time, "sleep", lambda *_: None)
    assert proc.wait_http("http://127.0.0.1:1/", timeout=3) is False


def test_make_env_defaults_and_extra(monkeypatch):
    """环境：已有取值不覆盖，平台默认值补齐，调用方额外项最终覆盖。"""
    monkeypatch.setenv("DB_NAME", "custom_db")
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.custom_settings")
    env = proc.make_env({"DJANGO_ASGI_SERVER": "1"})
    assert env["DB_NAME"] == "custom_db"
    assert env["DJANGO_SETTINGS_MODULE"] == "tests.custom_settings"
    assert env["DJANGO_ASGI_SERVER"] == "1"


def test_spawn_closes_parent_log_handle(monkeypatch, tmp_path):
    """拉起子进程后父进程不保留日志句柄；stdio 与 cwd 约定不变。"""
    monkeypatch.setattr(proc, "LOG_DIR", tmp_path)
    captured: dict = {}

    class _FakePopen:
        def __init__(self, command, **kwargs):
            captured["command"] = command
            captured.update(kwargs)

    monkeypatch.setattr(proc.subprocess, "Popen", _FakePopen)
    proc.spawn(["echo", "hi"], "backend.log", env={"A": "1"})

    assert captured["command"] == ["echo", "hi"]
    assert captured["stdout"].closed is True
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["stderr"] is subprocess.STDOUT
    assert captured["cwd"] == str(proc.ROOT)
    assert captured["env"] == {"A": "1"}
    assert (tmp_path / "backend.log").exists()
