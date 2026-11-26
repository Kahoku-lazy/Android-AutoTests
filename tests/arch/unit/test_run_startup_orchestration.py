from __future__ import annotations

import pytest

from utils.service_ctl import commands as cli
from utils.service_ctl.config import SERVICE_ORDER, build_registry

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _hermetic(monkeypatch):
    for key in ("DB_CHECK", "DB_AUTOSTART", "AUTO_SETUP", "STOP_DRAIN_TIMEOUT"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(cli.time, "sleep", lambda *_: None)


def _stub_orchestration(monkeypatch, *, db_ok=True, start_results=None):
    events: list[str] = []
    started = {"backend": True, "frontend": True}
    if start_results:
        started.update(start_results)

    def _stop(spec):
        events.append(f"stop:{spec.name}")

    def _start(spec) -> bool:
        events.append(f"start:{spec.name}")
        return started[spec.name]

    monkeypatch.setattr(cli, "resolve_services", lambda names: list(SERVICE_ORDER))
    monkeypatch.setattr(cli.db, "ensure", lambda cfg, allow_autostart: db_ok)
    monkeypatch.setattr(cli, "ensure_adb", lambda: None)
    monkeypatch.setattr(cli, "stop_service", _stop)
    monkeypatch.setattr(cli, "start_service", _start)
    return events


def test_start_stops_then_starts_backend_before_frontend(monkeypatch):
    events = _stub_orchestration(monkeypatch)

    cli.cmd_start([])

    assert events == ["stop:backend", "stop:frontend", "start:backend", "start:frontend"]


def test_start_aborts_without_touching_services_when_db_unavailable(monkeypatch, capsys):
    events = _stub_orchestration(monkeypatch, db_ok=False)

    cli.cmd_start([])

    assert events == []
    assert "Aborted" in capsys.readouterr().out


def test_start_no_db_flag_skips_preflight(monkeypatch):
    events = _stub_orchestration(monkeypatch)
    monkeypatch.setattr(cli.db, "ensure", lambda *a, **k: pytest.fail("不应检查数据库"))

    cli.cmd_start([], skip_db=True)

    assert events[-2:] == ["start:backend", "start:frontend"]


def test_backend_failure_short_circuits_frontend(monkeypatch, capsys):
    events = _stub_orchestration(monkeypatch, start_results={"backend": False})

    cli.cmd_start([])

    assert "start:frontend" not in events
    assert "Some services failed to start" in capsys.readouterr().out


def test_success_banner_lists_urls(monkeypatch, capsys):
    _stub_orchestration(monkeypatch)

    cli.cmd_start([])

    out = capsys.readouterr().out
    registry = build_registry()
    backend = registry["backend"].port
    frontend = registry["frontend"].port
    assert "Android-AutoTests Platform" in out
    assert f"Frontend    : http://localhost:{frontend}" in out
    assert f"API (Django): http://localhost:{backend}" in out
    assert f"Admin       : http://localhost:{backend}/admin/" in out


def test_restart_stops_before_starting(monkeypatch):
    events = _stub_orchestration(monkeypatch)

    cli.cmd_restart([])

    first_start = min(index for index, item in enumerate(events) if item.startswith("start:"))
    assert all(item.startswith("stop:") for item in events[:first_start])
    assert events[first_start:] == ["start:backend", "start:frontend"]


def test_resolve_services_defaults_to_all_in_registry_order():
    assert cli.resolve_services([]) == list(SERVICE_ORDER)
    assert cli.resolve_services(["all"]) == list(SERVICE_ORDER)


def test_resolve_services_retired_redis_is_note_not_error(capsys):
    assert cli.resolve_services(["redis"]) == []
    assert "Redis is retired" in capsys.readouterr().out


def test_resolve_services_unknown_exits_one(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.resolve_services(["bogus"])

    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "Unknown services: bogus" in out
    assert "Available: backend, frontend" in out
