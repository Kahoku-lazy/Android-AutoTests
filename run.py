"""
Android-AutoTests platform manager — start / stop / restart / status / logs / check.

Usage:
    python run.py start [backend|frontend ...] [--no-db]
    python run.py stop  [backend|frontend ...]
    python run.py restart [...] [--no-db]
    python run.py status
    python run.py logs [backend|frontend ...]
    python run.py check          # 本地质量门禁（实现见 utils/check_gates.py）
    python run.py setup          # 安装项目内 platform-tools（唯一会联网的命令）
    python run.py setup --check  # 只检测 adb，缺失时退出码 1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

from pathlib import Path

from backend.config.env import load_dotenv

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
IS_WIN = sys.platform == "win32"
# Redis 已退役（吊销记录落库、channel layer 用内存实现）；旧命令仍给提示而不是报未知服务。
# 提示用英文：run.py 的其它输出同为英文，且避免 Windows 管道/CI 日志里的编码歧义。
RETIRED_SERVICES = {
    "redis": "Redis is retired (OpenSpec: retire-redis); the platform no longer uses it.",
}
SERVICE_ORDER = ("backend", "frontend")


# ── .env（凭据只从这里来，BASE_ENV 不硬编码 DB_USER/DB_PASSWORD）；
# 单一实现在 backend/config/env.py，与 backend.config.settings 共用 ──
load_dotenv()

SERVICES = {
    "backend": int(os.environ.get("SERVER_PORT", "8766")),
    "frontend": 5173,
}

BASE_ENV = {
    "DB_ENGINE": os.environ.get("DB_ENGINE", "mysql"),
    "DB_NAME": os.environ.get("DB_NAME", "android_autotests"),
    "DB_HOST": os.environ.get("DB_HOST", "127.0.0.1"),
    "DB_PORT": os.environ.get("DB_PORT", "3306"),
    "PYTHONUTF8": "1",
    "DJANGO_SETTINGS_MODULE": "backend.config.settings",
    "SERVER_PORT": str(SERVICES["backend"]),
}


# ── 数据库前置检查 ───────────────────────────────────────────

_DB_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def _db_config() -> dict:
    """读取 .env 里的数据库配置（仅用于启动检查，不参与后端运行时配置）。"""
    return {
        "engine": os.environ.get("DB_ENGINE", "mysql").strip().lower(),
        "host": os.environ.get("DB_HOST", "127.0.0.1").strip(),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "name": os.environ.get("DB_NAME", "android_autotests"),
        "service": os.environ.get("DB_SERVICE_NAME", "MySQL" if IS_WIN else "mysql").strip(),
    }


def _db_reachable(cfg: dict) -> tuple[bool, str]:
    """用真实连接验证数据库（网络 + 账号 + 库名一次过）；sqlite 直接视为可用。

    Returns:
        tuple[bool, str]: (是否连通, 失败原因摘要)。
    """
    if cfg["engine"] == "sqlite":
        return True, ""
    try:
        import MySQLdb

        conn = MySQLdb.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            passwd=cfg["password"],
            db=cfg["name"],
            connect_timeout=3,
        )
        conn.close()
        return True, ""
    except Exception as exc:  # noqa: BLE001 - 任何连接失败都转成可读摘要
        return False, " ".join(str(exc).split())[:220]


def _is_loopback(host: str) -> bool:
    """数据库地址是否为本机。"""
    return host.strip().lower() in _DB_LOOPBACK


def _db_status_line() -> str:
    """status 命令里的数据库描述；永不抛异常。"""
    cfg = _db_config()
    if cfg["engine"] == "sqlite":
        return "SQLite  (DB_ENGINE=sqlite)"
    ok, _ = _db_reachable(cfg)
    return f"{cfg['host']}:{cfg['port']}  {'ONLINE' if ok else 'OFFLINE'}"


def _start_local_db_service(cfg: dict) -> tuple[bool, str]:
    """按平台启动本机数据库服务；返回 (是否成功, 原始输出)。"""
    service = cfg["service"]
    if IS_WIN:
        cmd = ["sc.exe", "start", service]
    elif sys.platform == "darwin":
        cmd = ["brew", "services", "start", service]
    else:
        cmd = ["systemctl", "start", service]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:  # noqa: BLE001 - 命令不存在/超时都按启动失败处理
        return False, str(exc)
    output = " ".join(((proc.stdout or "") + (proc.stderr or "")).split())
    if proc.returncode == 0 or "already" in output.lower():
        return True, output
    return False, output


def _db_elevation_hint(cfg: dict) -> str:
    """给出当前平台启动数据库服务的提权命令。"""
    service = cfg["service"]
    if IS_WIN:
        return f"net start {service}   （以管理员身份运行）"
    if sys.platform == "darwin":
        return f"brew services start {service}"
    return f"sudo systemctl start {service}"


def _ensure_db(cfg: dict, allow_autostart: bool) -> bool:
    """启动后端前的数据库检查：可达即通过；本机可尝试拉起服务；否则报错中止。"""
    ok, detail = _db_reachable(cfg)
    if ok:
        print(f"  Database         : {cfg['host']}:{cfg['port']}  ONLINE")
        return True

    print(f"  Database         : {cfg['host']}:{cfg['port']}  OFFLINE（{detail or '连接失败'}）")
    if not _is_loopback(cfg["host"]):
        print("  Database         : 远程数据库不可达，请检查网络与服务；不会尝试启动远程库。")
        return False

    hint = _db_elevation_hint(cfg)
    if not allow_autostart:
        print(f"  Database         : 已禁用自动启动（DB_AUTOSTART=0）。请先启动：{hint}")
        return False

    print(f"  Database         : 尝试启动本机服务 {cfg['service']} ...")
    started, output = _start_local_db_service(cfg)
    if started and _db_reachable(cfg)[0]:
        print(f"  Database         : {cfg['host']}:{cfg['port']}  ONLINE（已启动）")
        return True
    if output:
        print(f"  Database         : 启动失败：{output[:200]}")
    print(f"  Database         : 请手动启动后重试：{hint}")
    return False


# ── 进程 / 端口工具 ───────────────────────────────────────────


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=5, **kwargs)


def find_listening_pid(port: int) -> str | None:
    try:
        if IS_WIN:
            result = _run(["netstat", "-ano"])
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    return line.strip().split()[-1]
        else:
            result = _run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"])
            pids = result.stdout.strip().split()
            return pids[0] if pids else None
    except Exception:
        return None
    return None


def _pid_alive(pid: str) -> bool:
    try:
        if IS_WIN:
            out = _run(["tasklist", "/FI", f"PID eq {pid}", "/NH"]).stdout
            return pid in out
        os.kill(int(pid), 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _kill(pid: str, force: bool = False) -> None:
    if IS_WIN:
        cmd = ["taskkill", "/PID", pid] + (["/F"] if force else [])
    else:
        cmd = ["kill", "-9", pid] if force else ["kill", pid]
    try:
        _run(cmd)
    except Exception:
        # 进程可能已自行退出（stop 与自然退出的竞态）→ 杀不到属预期；调用方用 _pid_alive() 复核
        pass


def graceful_kill(pid: str) -> bool:
    _kill(pid, force=False)
    for _ in range(6):
        time.sleep(0.5)
        if not _pid_alive(pid):
            return True
    return False


def kill_port(port: int) -> bool:
    """先优雅退出，超时再强制杀。"""
    pid = find_listening_pid(port)
    if not pid:
        return False
    if graceful_kill(pid):
        print(f"  Killed PID {pid} (port {port}) — graceful")
        return True
    _kill(pid, force=True)
    time.sleep(0.5)
    print(f"  Killed PID {pid} (port {port}) — forced")
    return True


def wait_http(url: str, timeout: int = 20) -> bool:
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def make_env(extra: dict | None = None) -> dict:
    env = os.environ.copy()
    for k, v in BASE_ENV.items():
        env.setdefault(k, v)
    if extra:
        env.update(extra)
    return env


def spawn(cmd: list[str], log_name: str, cwd: Path | None = None, env: dict | None = None):
    LOG_DIR.mkdir(exist_ok=True)
    kwargs = {
        "cwd": str(cwd or ROOT),
        "stdin": subprocess.DEVNULL,
        "stdout": open(LOG_DIR / log_name, "a"),
        "stderr": subprocess.STDOUT,
        "env": env or make_env(),
    }
    if IS_WIN:
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(cmd, **kwargs)


def resolve_services(names: list[str]) -> list[str]:
    if not names or "all" in names:
        return list(SERVICE_ORDER)
    for name in names:
        if name in RETIRED_SERVICES:
            print(f"  Note: {RETIRED_SERVICES[name]}")
    names = [n for n in names if n not in RETIRED_SERVICES]
    invalid = [n for n in names if n not in SERVICES]
    if invalid:
        print(f"Unknown services: {', '.join(invalid)}")
        print(f"Available: {', '.join(SERVICE_ORDER)}")
        sys.exit(1)
    return names


def cleanup_mysql_connections() -> None:
    """Windows 强制杀 Daphne 后清理孤儿 Sleep 连接，避免 max_connections。"""
    if os.environ.get("DB_ENGINE", "mysql").strip().lower() == "sqlite":
        return
    try:
        import MySQLdb

        db_name = BASE_ENV.get("DB_NAME", "android_autotests")
        db_user = os.environ.get("DB_USER", "root")
        db_host = BASE_ENV.get("DB_HOST", "127.0.0.1")
        db_port = int(BASE_ENV.get("DB_PORT", "3306"))
        conn = MySQLdb.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            passwd=os.environ.get("DB_PASSWORD", ""),
            db=db_name,
            connect_timeout=3,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT ID FROM information_schema.PROCESSLIST "
            "WHERE USER = %s AND DB = %s AND COMMAND = 'Sleep' AND TIME > 5",
            (db_user, db_name),
        )
        ids = [row[0] for row in cur.fetchall()]
        for pid in ids:
            try:
                cur.execute(f"KILL {pid}")
            except Exception:
                # 连接可能在 SELECT 与 KILL 之间自行关闭：跳过这一条，不影响其余清理
                pass
        if ids:
            print(f"  MySQL cleanup: closed {len(ids)} idle connection(s)")
        cur.close()
        conn.close()
    except Exception as exc:
        # 清理是 best-effort：MySQL 未启动/凭据不足不该让 stop 失败，但必须留下可诊断线索
        print(f"  MySQL cleanup skipped: {exc}")


# ── 各服务启停 ────────────────────────────────────────────────


def start_backend() -> bool:
    port = SERVICES["backend"]
    print(f"[Backend] Starting Django on port {port}...")
    spawn(
        [
            sys.executable,
            str(ROOT / "run_daphne.py"),
            "-p",
            str(port),
            "-b",
            "0.0.0.0",
            "backend.config.asgi:application",
        ],
        "backend.log",
        env=make_env({"DJANGO_ASGI_SERVER": "1"}),
    )
    if wait_http(f"http://127.0.0.1:{port}/", 20):
        print(f"  Backend          ready http://localhost:{port}")
        return True
    print("  FAILED: backend did not start (check logs/backend.log)")
    return False


def start_frontend() -> bool:
    port = SERVICES["frontend"]
    print(f"[Frontend] Starting Vite on port {port}...")
    npx = "npx.cmd" if IS_WIN else "npx"
    spawn([npx, "vite", "--host"], "frontend.log", cwd=ROOT / "frontend")
    if wait_http(f"http://127.0.0.1:{port}/", 30):
        print(f"  Frontend         ready http://localhost:{port}")
        return True
    print("  FAILED: frontend did not start (check logs/frontend.log)")
    return False


def stop_backend() -> None:
    port = SERVICES["backend"]
    print(f"[Backend] Stopping port {port}...")
    _drain_backend(port)
    cleanup_mysql_connections()
    kill_port(port)


def _drain_backend(port: int) -> None:
    """停机前停止派发并等待 running 归零；后端不可达时直接返回。"""
    base = f"http://127.0.0.1:{port}/api/system/drain/"
    try:
        request = urllib.request.Request(base, method="POST", data=b"")
        with urllib.request.urlopen(request, timeout=3) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return
    running = int((payload.get("data") or {}).get("running") or 0)
    if running <= 0:
        return

    timeout = int(os.environ.get("STOP_DRAIN_TIMEOUT", "180"))
    deadline = time.time() + timeout
    print(f"  Waiting for {running} running task(s), up to {timeout}s...")
    last_report = time.time()
    while time.time() < deadline:
        time.sleep(2)
        try:
            with urllib.request.urlopen(base, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data") or {}
        except Exception:
            return
        running = int(data.get("running") or 0)
        if running <= 0:
            print("  All tasks finished — stopping backend.")
            return
        if time.time() - last_report >= 10:
            left = max(int(deadline - time.time()), 0)
            print(f"  Still {running} running task(s), {left}s left...")
            last_report = time.time()
    print("  Drain timeout reached — forcing stop.")


def stop_frontend() -> None:
    port = SERVICES["frontend"]
    print(f"[Frontend] Stopping port {port}...")
    kill_port(port)


_START = {"backend": start_backend, "frontend": start_frontend}
_STOP = {"backend": stop_backend, "frontend": stop_frontend}
_LOGS = {"backend": "backend.log", "frontend": "frontend.log"}


# ── 命令 ─────────────────────────────────────────────────────


def _adb_status_line() -> str:
    """返回 status 命令里的 ADB 描述：来源 + 版本；缺失时给出修复命令。"""
    from utils import adb as adb_tools

    info = adb_tools.adb_status()
    if not info["path"]:
        return "MISSING  (run: python run.py setup)"
    version = ""
    try:
        proc = subprocess.run([info["path"], "version"], capture_output=True, text=True, timeout=5)
        lines = (proc.stdout or proc.stderr or "").strip().splitlines()
        if lines:
            version = lines[0].replace("Android Debug Bridge version", "").strip()
    except Exception:  # noqa: BLE001 - 版本行只是附加信息，失败不影响状态输出
        version = ""
    label = {"env": "ADB_PATH", "platform": "platform", "bundled": "bundled"}
    return f"{label.get(info['source'], info['source'])}  {version}".strip()


def _ensure_adb() -> None:
    """启动后端前检查 adb：缺失时提示；`AUTO_SETUP=1` 时自动安装。"""
    from utils import adb as adb_tools

    try:
        adb_tools.adb_binary()
        return
    except adb_tools.AdbUnavailableError as exc:
        print(f"  ADB: {exc}")
    if os.environ.get("AUTO_SETUP", "").strip().lower() not in ("1", "true", "yes"):
        return
    from utils import platform_tools

    print("  ADB: AUTO_SETUP=1，开始安装 platform-tools ...")
    platform_tools.install()
    adb_tools.reset_cache()


def cmd_setup(check_only: bool = False, force: bool = False, from_file: str | None = None) -> None:
    """检测/安装项目内 platform-tools；唯一会联网的命令。"""
    from utils import adb as adb_tools
    from utils import platform_tools

    if check_only:
        info = platform_tools.status()
        if info["installed"]:
            print(f"  ADB: platform 已安装（{info['version']}）{info['path']}")
            sys.exit(0)
        print(f"  ADB: 未安装（当前来源：{info['source']}）。运行 python run.py setup 安装。")
        sys.exit(1)

    platform_tools.install(force=force, archive=from_file)
    adb_tools.reset_cache()
    print(f"  ADB: {adb_tools.adb_binary()}")


def cmd_start(services: list[str], skip_db: bool = False) -> None:
    names = resolve_services(services)
    db_disabled = os.environ.get("DB_CHECK", "1").strip().lower() in ("0", "false", "no")
    if "backend" in names and not skip_db and not db_disabled:
        autostart = os.environ.get("DB_AUTOSTART", "1").strip().lower() not in ("0", "false", "no")
        if not _ensure_db(_db_config(), allow_autostart=autostart):
            print("\n  Aborted: 数据库不可用，未启动任何服务（可用 --no-db 跳过检查）。")
            return
    if "backend" in names:
        _ensure_adb()
    for s in names:
        _STOP[s]()
    time.sleep(1)

    order = [s for s in SERVICE_ORDER if s in names]
    ok = all(_START[s]() for s in order)
    if not ok:
        print("\n  Some services failed to start. Check logs/")
        return

    print()
    print("=" * 54)
    print("  Android-AutoTests Platform")
    if "frontend" in order:
        print(f"  Frontend    : http://localhost:{SERVICES['frontend']}")
    if "backend" in order:
        print(f"  API (Django): http://localhost:{SERVICES['backend']}")
        print("  AI (Agent)  : in-process (runs inside Django)")
    print(f"  Admin       : http://localhost:{SERVICES['backend']}/admin/  (admin/admin123)")
    print("=" * 54)


def cmd_stop(services: list[str]) -> None:
    names = resolve_services(services)
    for s in names:
        _STOP[s]()
    print("Done.")


def cmd_restart(services: list[str], skip_db: bool = False) -> None:
    names = resolve_services(services)
    for s in names:
        _STOP[s]()
    time.sleep(2)
    cmd_start(names, skip_db=skip_db)


def cmd_status() -> None:
    def http_ok(url: str) -> str:
        try:
            urllib.request.urlopen(url, timeout=2)
            return "ONLINE"
        except Exception:
            return "OFFLINE"

    be_port = SERVICES["backend"]
    fe_port = SERVICES["frontend"]
    print(f"  Django backend   (:{be_port})  {http_ok(f'http://127.0.0.1:{be_port}/')}")
    print(f"  Vue frontend     (:{fe_port})  {http_ok(f'http://127.0.0.1:{fe_port}/')}")
    print(f"  Database         : {_db_status_line()}")
    print(f"  ADB              : {_adb_status_line()}")


def cmd_logs(services: list[str]) -> None:
    for s in resolve_services(services):
        f = LOG_DIR / _LOGS[s]
        print(f"\n=== {_LOGS[s]} (last 20 lines) ===")
        if f.exists():
            lines = f.read_text(encoding="utf-8", errors="replace").strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        else:
            print("  (empty)")


def cmd_check() -> None:
    """跑本地质量门禁；检查内容与 CI 一一对应，见 utils/check_gates.py。"""
    result = subprocess.run([sys.executable, str(ROOT / "utils" / "check_gates.py")], cwd=str(ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Android-AutoTests platform manager")
    p.add_argument("cmd", choices=["start", "stop", "restart", "status", "logs", "check", "setup"])
    p.add_argument("services", nargs="*", default=[], help="backend frontend (default: all)")
    p.add_argument("--check", action="store_true", help="setup: 只检测，不下载")
    p.add_argument("--force", action="store_true", help="setup: 强制重装 platform-tools")
    p.add_argument("--from-file", default=None, help="setup: 用本地 platform-tools zip 离线安装")
    p.add_argument("--no-db", action="store_true", help="start/restart: 跳过数据库检查")
    args = p.parse_args()

    {
        "start": lambda: cmd_start(args.services, skip_db=args.no_db),
        "stop": lambda: cmd_stop(args.services),
        "restart": lambda: cmd_restart(args.services, skip_db=args.no_db),
        "status": cmd_status,
        "logs": lambda: cmd_logs(args.services),
        "check": cmd_check,
        "setup": lambda: cmd_setup(args.check, args.force, args.from_file),
    }[args.cmd]()
