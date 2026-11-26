from __future__ import annotations

import os
import sys

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "logs"
IS_WIN = sys.platform == "win32"

SERVICE_ORDER = ("backend", "frontend")
RETIRED_SERVICES = {
    "redis": "Redis is retired (OpenSpec: retire-redis); the platform no longer uses it.",
}

STOP_SETTLE_SECONDS = 1
RESTART_SETTLE_SECONDS = 2

_TRUE_VALUES = frozenset({"1", "true", "yes"})
_FALSE_VALUES = frozenset({"0", "false", "no"})


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    label: str
    runtime: str
    port: int
    log: str
    cwd: Path
    ready_timeout: int
    command: tuple[str, ...]
    extra_env: dict[str, str] = field(default_factory=dict)
    drain: bool = False


def env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def backend_port() -> int:
    return int(os.environ.get("SERVER_PORT", "8766"))


def build_registry() -> dict[str, ServiceSpec]:
    port = backend_port()
    npx = "npx.cmd" if IS_WIN else "npx"
    return {
        "backend": ServiceSpec(
            name="backend",
            label="Backend",
            runtime="Django",
            port=port,
            log="backend.log",
            cwd=ROOT,
            ready_timeout=20,
            command=(
                sys.executable,
                str(ROOT / "run_daphne.py"),
                "-p",
                str(port),
                "-b",
                "0.0.0.0",
                "backend.config.asgi:application",
            ),
            extra_env={"DJANGO_ASGI_SERVER": "1"},
            drain=True,
        ),
        "frontend": ServiceSpec(
            name="frontend",
            label="Frontend",
            runtime="Vite",
            port=5173,
            log="frontend.log",
            cwd=ROOT / "frontend",
            ready_timeout=30,
            command=(npx, "vite", "--host"),
        ),
    }


def base_env() -> dict[str, str]:
    return {
        "DB_ENGINE": os.environ.get("DB_ENGINE", "mysql"),
        "DB_NAME": os.environ.get("DB_NAME", "android_autotests"),
        "DB_HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "DB_PORT": os.environ.get("DB_PORT", "3306"),
        "PYTHONUTF8": "1",
        "DJANGO_SETTINGS_MODULE": "backend.config.settings",
        "SERVER_PORT": str(backend_port()),
    }


def stop_drain_timeout() -> int:
    return int(os.environ.get("STOP_DRAIN_TIMEOUT", "180"))
