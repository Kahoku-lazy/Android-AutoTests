"""
模块功能：➡️ `utils.service_ctl.services` 的行为契约：拉起/停机顺序、排空短路、超时名单落盘 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_platform_services.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 utils/service_ctl
🏁
"""

from __future__ import annotations

import json

import pytest

from utils.service_ctl import services as services_mod
from utils.service_ctl.config import build_registry

pytestmark = [pytest.mark.unit]


class _Resp:
    """urllib 响应替身。"""

    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self._payload


def test_start_service_ready(monkeypatch, capsys):
    """就绪：打印启动/就绪行，命令、日志名、工作目录与附加环境变量都按注册表。"""
    spec = build_registry()["backend"]
    captured = {}

    def _spawn(command, log, cwd=None, env=None):
        captured.update(command=command, log=log, cwd=cwd, env=env)

    monkeypatch.setattr(services_mod, "spawn", _spawn)
    monkeypatch.setattr(services_mod, "wait_http", lambda url, timeout: True)

    assert services_mod.start_service(spec) is True
    assert captured["log"] == "backend.log"
    assert captured["cwd"] == spec.cwd
    assert captured["env"]["DJANGO_ASGI_SERVER"] == "1"
    out = capsys.readouterr().out
    assert "[Backend] Starting Django on port 8766..." in out
    assert "ready http://localhost:8766" in out


def test_start_service_timeout(monkeypatch, capsys):
    """超时：返回 False，并指向对应日志文件。"""
    spec = build_registry()["frontend"]
    monkeypatch.setattr(services_mod, "spawn", lambda *a, **k: None)
    monkeypatch.setattr(services_mod, "wait_http", lambda url, timeout: False)

    assert services_mod.start_service(spec) is False
    assert "FAILED: frontend did not start (check logs/frontend.log)" in capsys.readouterr().out


def test_stop_service_drains_backend_then_kills(monkeypatch):
    """backend 停机顺序：排空 → 清理数据库空闲连接 → 杀端口。"""
    spec = build_registry()["backend"]
    events: list[str] = []
    monkeypatch.setattr(services_mod, "drain_backend", lambda port: events.append("drain"))
    monkeypatch.setattr(
        services_mod.db, "cleanup_idle_connections", lambda cfg: events.append("cleanup")
    )
    monkeypatch.setattr(services_mod, "kill_port", lambda port: events.append("kill"))

    services_mod.stop_service(spec)

    assert events == ["drain", "cleanup", "kill"]


def test_stop_service_frontend_skips_drain(monkeypatch):
    """frontend 停机不需要排空，也不清理数据库。"""
    spec = build_registry()["frontend"]
    events: list[str] = []
    monkeypatch.setattr(services_mod, "drain_backend", lambda port: events.append("drain"))
    monkeypatch.setattr(
        services_mod.db, "cleanup_idle_connections", lambda cfg: events.append("cleanup")
    )
    monkeypatch.setattr(services_mod, "kill_port", lambda port: events.append("kill"))

    services_mod.stop_service(spec)

    assert events == ["kill"]


def test_drain_returns_immediately_when_nothing_running(monkeypatch):
    """没有运行中的任务：只发一次查询请求，不进入等待循环。"""
    calls: list[str] = []

    def _urlopen(*_args, **_kwargs):
        calls.append("call")
        return _Resp(b'{"status": true, "data": {"running": 0}}')

    monkeypatch.setattr(services_mod.urllib.request, "urlopen", _urlopen)

    services_mod.drain_backend(8766)

    assert len(calls) == 1


def test_write_stop_timeout_mark(tmp_path, monkeypatch):
    """超时名单落盘：编号与时间戳写入约定文件；空名单不写。"""
    mark = tmp_path / "stop-timeout-tasks.json"
    monkeypatch.setattr(services_mod, "STOP_TIMEOUT_MARK", mark)

    services_mod.write_stop_timeout_mark([])
    assert not mark.exists()

    services_mod.write_stop_timeout_mark([7, 9])
    payload = json.loads(mark.read_text(encoding="utf-8"))
    assert payload["ids"] == [7, 9]
    assert payload["written_at"]
