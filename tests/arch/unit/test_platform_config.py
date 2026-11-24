"""`utils.service_ctl.config` 的行为契约：开关解析口径、服务注册表与环境默认值。"""

from __future__ import annotations

import pytest

from utils.service_ctl import config as cfg

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """隔离本机环境：所有断言只依赖测试自己设置的值。"""
    for key in ("SERVER_PORT", "STOP_DRAIN_TIMEOUT", "DB_ENGINE", "DB_NAME", "DB_HOST", "DB_PORT"):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", False),
        ("false", False),
        ("no", False),
        (" No ", False),
        ("1", True),
        ("true", True),
        ("yes", True),
        ("2", True),
        ("", True),
        (None, True),
    ],
)
def test_env_flag_default_on_flags(monkeypatch, value, expected):
    """默认开启的开关（DB_CHECK / DB_AUTOSTART）：只有 falsy 集才关。"""
    if value is None:
        monkeypatch.delenv("DB_CHECK", raising=False)
    else:
        monkeypatch.setenv("DB_CHECK", value)
    assert cfg.env_flag("DB_CHECK", True) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        (" YES ", True),
        ("0", False),
        ("no", False),
        ("2", False),
        ("", False),
        (None, False),
    ],
)
def test_env_flag_default_off_flags(monkeypatch, value, expected):
    """默认关闭的开关（AUTO_SETUP）：只有 truthy 集才开。"""
    if value is None:
        monkeypatch.delenv("AUTO_SETUP", raising=False)
    else:
        monkeypatch.setenv("AUTO_SETUP", value)
    assert cfg.env_flag("AUTO_SETUP", False) is expected


def test_registry_ports_and_logs():
    """注册表：backend 默认 8766、frontend 固定 5173，日志名与旧实现一致。"""
    registry = cfg.build_registry()
    assert set(registry) == set(cfg.SERVICE_ORDER)
    assert registry["backend"].port == 8766
    assert registry["frontend"].port == 5173
    assert registry["backend"].log == "backend.log"
    assert registry["frontend"].log == "frontend.log"


def test_registry_reads_server_port_lazily(monkeypatch):
    """`SERVER_PORT` 在 build_registry 调用时读取：import 之后改环境也生效。"""
    monkeypatch.setenv("SERVER_PORT", "9999")
    registry = cfg.build_registry()
    assert registry["backend"].port == 9999
    assert "9999" in registry["backend"].command


def test_registry_commands_and_cwd():
    """启动命令与工作目录：backend 走 run_daphne.py + asgi 应用，frontend 在 frontend/ 跑 vite。"""
    registry = cfg.build_registry()
    backend = registry["backend"]
    assert any("run_daphne.py" in part for part in backend.command)
    assert "backend.config.asgi:application" in backend.command
    assert backend.extra_env == {"DJANGO_ASGI_SERVER": "1"}
    assert backend.cwd == cfg.ROOT
    assert registry["frontend"].cwd == cfg.ROOT / "frontend"
    assert registry["frontend"].command[1:] == ("vite", "--host")


def test_base_env_defaults_and_override(monkeypatch):
    """基础环境变量：未设置时给默认值，已设置时保留。"""
    monkeypatch.setenv("DB_NAME", "custom_db")
    env = cfg.base_env()
    assert env["DB_NAME"] == "custom_db"
    assert env["DB_ENGINE"] == "mysql"
    assert env["DB_HOST"] == "127.0.0.1"
    assert env["DB_PORT"] == "3306"
    assert env["PYTHONUTF8"] == "1"
    assert env["DJANGO_SETTINGS_MODULE"] == "backend.config.settings"
    assert env["SERVER_PORT"] == "8766"


def test_stop_drain_timeout(monkeypatch):
    """排空超时：默认 180 秒，可由 `STOP_DRAIN_TIMEOUT` 覆盖。"""
    assert cfg.stop_drain_timeout() == 180
    monkeypatch.setenv("STOP_DRAIN_TIMEOUT", "5")
    assert cfg.stop_drain_timeout() == 5


def test_retired_services_note():
    """退役服务表保留 redis 提示文案。"""
    assert "redis" in cfg.RETIRED_SERVICES
    assert "Redis is retired" in cfg.RETIRED_SERVICES["redis"]
