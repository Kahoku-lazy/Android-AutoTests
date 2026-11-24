"""
模块功能：➡️ 平台服务注册表与启动开关：run.py 系列命令的唯一配置来源 🏁
Python 调试：➡️ python -m utils.service_ctl.config 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_platform_config.py: ServiceSpec / build_registry / env_flag 口径
2. tests/arch/unit/test_platform_services.py: 注册表被启停编排消费
🏁
"""

from __future__ import annotations

import os
import sys

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "logs"
IS_WIN = sys.platform == "win32"

# 服务启动顺序即注册顺序：backend 先于 frontend。
SERVICE_ORDER = ("backend", "frontend")
# 已退役服务：仍给提示而不是报未知服务（提示用英文，避免 Windows 管道/CI 编码歧义）。
RETIRED_SERVICES = {
    "redis": "Redis is retired (OpenSpec: retire-redis); the platform no longer uses it.",
}

# 先停后起、重启时的稳定等待秒数（沿用原 run.py 的取值）。
STOP_SETTLE_SECONDS = 1
RESTART_SETTLE_SECONDS = 2

_TRUE_VALUES = frozenset({"1", "true", "yes"})
_FALSE_VALUES = frozenset({"0", "false", "no"})


@dataclass(frozen=True)
class ServiceSpec:
    """一个可启停服务的全部声明式信息；新增服务只改 `build_registry` 一处。"""

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
    """把环境变量解析成开关：truthy 集返回 True，falsy 集返回 False，其余取 default。"""
    value = os.environ.get(name, "").strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def backend_port() -> int:
    """后端监听端口（`SERVER_PORT`，默认 8766）。"""
    return int(os.environ.get("SERVER_PORT", "8766"))


def build_registry() -> dict[str, ServiceSpec]:
    """按当前环境构造服务注册表；在命令执行时调用，避免导入期读环境。"""
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
    """子进程的基础环境变量（在 `os.environ` 之上补齐默认值，不覆盖已有取值）。"""
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
    """停机排空的最长等待秒数（`STOP_DRAIN_TIMEOUT`，默认 180）。"""
    return int(os.environ.get("STOP_DRAIN_TIMEOUT", "180"))
