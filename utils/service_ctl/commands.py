"""
模块功能：➡️ run.py 的命令实现：服务名解析、启停/重启/状态/日志/检查/setup 与 adb 处理 🏁
Python 调试：➡️ python -m utils.service_ctl.commands 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_run_startup_orchestration.py: 启动编排与数据库预检
🏁
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request

import utils.service_ctl.db as db

from .config import (
    LOG_DIR,
    RESTART_SETTLE_SECONDS,
    RETIRED_SERVICES,
    ROOT,
    SERVICE_ORDER,
    STOP_SETTLE_SECONDS,
    build_registry,
    env_flag,
)
from .services import start_service, stop_service


def resolve_services(names: list[str]) -> list[str]:
    """解析服务名：空 / `all` 取全部；退役服务提示后剔除；非法服务打印清单并退出 1。"""
    registry = build_registry()
    if not names or "all" in names:
        return list(SERVICE_ORDER)
    for name in names:
        if name in RETIRED_SERVICES:
            print(f"  Note: {RETIRED_SERVICES[name]}")
    names = [name for name in names if name not in RETIRED_SERVICES]
    invalid = [name for name in names if name not in registry]
    if invalid:
        print(f"Unknown services: {', '.join(invalid)}")
        print(f"Available: {', '.join(SERVICE_ORDER)}")
        sys.exit(1)
    return names


def adb_status_line() -> str:
    """`status` 命令里的 ADB 描述：来源 + 版本；缺失时给出修复命令。"""
    from utils import adb as adb_tools

    info = adb_tools.adb_status()
    if not info["path"]:
        return "MISSING  (run: python -m run setup)"
    version = ""
    try:
        result = subprocess.run(
            [info["path"], "version"], capture_output=True, text=True, timeout=5
        )
        lines = (result.stdout or result.stderr or "").strip().splitlines()
        if lines:
            version = lines[0].replace("Android Debug Bridge version", "").strip()
    except Exception:  # noqa: BLE001 - 版本行只是附加信息，失败不影响状态输出
        version = ""
    label = {"env": "ADB_PATH", "platform": "platform", "bundled": "bundled"}
    return f"{label.get(info['source'], info['source'])}  {version}".strip()


def ensure_adb() -> None:
    """启动后端前检查 adb：缺失时提示；`AUTO_SETUP=1` 时自动安装。"""
    from utils import adb as adb_tools

    try:
        adb_tools.adb_binary()
        return
    except adb_tools.AdbUnavailableError as exc:
        print(f"  ADB: {exc}")
    if not env_flag("AUTO_SETUP", False):
        return
    from utils import platform_tools

    print("  ADB: AUTO_SETUP=1，开始安装 platform-tools ...")
    platform_tools.install()
    adb_tools.reset_cache()


def cmd_setup(check_only: bool = False, force: bool = False, from_file: str | None = None) -> None:
    """检测 / 安装项目内 platform-tools；唯一会联网的命令。"""
    from utils import adb as adb_tools
    from utils import platform_tools

    if check_only:
        info = platform_tools.status()
        if info["installed"]:
            print(f"  ADB: platform 已安装（{info['version']}）{info['path']}")
            sys.exit(0)
        print(f"  ADB: 未安装（当前来源：{info['source']}）。运行 python -m run setup 安装。")
        sys.exit(1)

    platform_tools.install(force=force, archive=from_file)
    adb_tools.reset_cache()
    print(f"  ADB: {adb_tools.adb_binary()}")


def cmd_start(services: list[str], skip_db: bool = False) -> None:
    """启动：数据库预检（可跳过）→ adb 检查 → 先停后起 → 成功横幅。"""
    names = resolve_services(services)
    registry = build_registry()
    if "backend" in names and not skip_db and env_flag("DB_CHECK", True):
        autostart = env_flag("DB_AUTOSTART", True)
        if not db.ensure(db.DbConfig.from_env(), allow_autostart=autostart):
            print("\n  Aborted: 数据库不可用，未启动任何服务（可用 --no-db 跳过检查）。")
            return
    if "backend" in names:
        ensure_adb()
    for name in names:
        stop_service(registry[name])
    time.sleep(STOP_SETTLE_SECONDS)

    order = [name for name in SERVICE_ORDER if name in names]
    # 现状语义：任一服务启动失败即停止后续尝试（all() 短路），与拆分前一致
    ok = all(start_service(registry[name]) for name in order)
    if not ok:
        print("\n  Some services failed to start. Check logs/")
        return

    print()
    print("=" * 54)
    print("  Android-AutoTests Platform")
    if "frontend" in order:
        print(f"  Frontend    : http://localhost:{registry['frontend'].port}")
    if "backend" in order:
        print(f"  API (Django): http://localhost:{registry['backend'].port}")
        print("  AI (Agent)  : in-process (runs inside Django)")
    print(f"  Admin       : http://localhost:{registry['backend'].port}/admin/  (admin/admin123)")
    print("=" * 54)


def cmd_stop(services: list[str]) -> None:
    """停止指定服务（默认全部）。"""
    registry = build_registry()
    for name in resolve_services(services):
        stop_service(registry[name])
    print("Done.")


def cmd_restart(services: list[str], skip_db: bool = False) -> None:
    """重启：先停全部，稳定等待后再按启动流程走一遍。"""
    registry = build_registry()
    names = resolve_services(services)
    for name in names:
        stop_service(registry[name])
    time.sleep(RESTART_SETTLE_SECONDS)
    cmd_start(names, skip_db=skip_db)


def cmd_status() -> None:
    """状态：前后端可达性、数据库与 ADB 各一行。"""
    registry = build_registry()

    def http_ok(url: str) -> str:
        try:
            urllib.request.urlopen(url, timeout=2)
            return "ONLINE"
        except Exception:  # noqa: BLE001 - 状态查询失败就是 OFFLINE，不抛错
            return "OFFLINE"

    back_port = registry["backend"].port
    front_port = registry["frontend"].port
    print(f"  Django backend   (:{back_port})  {http_ok(f'http://127.0.0.1:{back_port}/')}")
    print(f"  Vue frontend     (:{front_port})  {http_ok(f'http://127.0.0.1:{front_port}/')}")
    print(f"  Database         : {db.status_line()}")
    print(f"  ADB              : {adb_status_line()}")


def cmd_logs(services: list[str]) -> None:
    """日志：按服务打印日志文件尾部 20 行。"""
    registry = build_registry()
    for name in resolve_services(services):
        log_name = registry[name].log
        path = LOG_DIR / log_name
        print(f"\n=== {log_name} (last 20 lines) ===")
        if path.exists():
            lines = path.read_text(encoding="utf-8", errors="replace").strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        else:
            print("  (empty)")


def cmd_check() -> None:
    """跑本地质量门禁；检查内容与 CI 一一对应，见 utils/check_gates.py。"""
    result = subprocess.run([sys.executable, "-m", "utils.check_gates"], cwd=str(ROOT))
    sys.exit(result.returncode)
