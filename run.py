"""
Android-AutoTests platform manager — start / stop / restart / status / logs.

Usage:
    python run.py start [redis|backend|frontend ...]
    python run.py stop  [redis|backend|frontend ...]
    python run.py restart [...]
    python run.py status
    python run.py logs [redis|backend|frontend ...]
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.request

from pathlib import Path

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
IS_WIN = sys.platform == "win32"
SERVICE_ORDER = ("redis", "backend", "frontend")


# ── .env（凭据只从这里来，BASE_ENV 不硬编码 DB_USER/DB_PASSWORD）──
def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()

SERVICES = {
    "redis": 6379,
    "backend": int(os.environ.get("SERVER_PORT", "8766")),
    "frontend": 5173,
}

BASE_ENV = {
    "DB_ENGINE": os.environ.get("DB_ENGINE", "mysql"),
    "DB_NAME": os.environ.get("DB_NAME", "android_autotests"),
    "DB_HOST": os.environ.get("DB_HOST", "127.0.0.1"),
    "DB_PORT": os.environ.get("DB_PORT", "3306"),
    "PYTHONUTF8": "1",
    "DJANGO_SETTINGS_MODULE": "config.settings",
    "SERVER_PORT": str(SERVICES["backend"]),
}


# ── 进程 / 端口工具 ───────────────────────────────────────────


def port_in_use(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


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
    invalid = [n for n in names if n not in SERVICES]
    if invalid:
        print(f"Unknown services: {', '.join(invalid)}")
        print(f"Available: {', '.join(SERVICE_ORDER)}")
        sys.exit(1)
    return names


def cleanup_mysql_connections() -> None:
    """Windows 强制杀 Daphne 后清理孤儿 Sleep 连接，避免 max_connections。"""
    try:
        import MySQLdb

        db_name = BASE_ENV.get("DB_NAME", "android_autotests")
        db_user = os.environ.get("DB_USER", "root")
        db_host = BASE_ENV.get("DB_HOST", "127.0.0.1")
        db_port = int(BASE_ENV.get("DB_PORT", "3306"))
        conn = MySQLdb.connect(
            host=db_host, port=db_port, user=db_user, db=db_name, connect_timeout=3
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
                pass
        if ids:
            print(f"  MySQL cleanup: closed {len(ids)} idle connection(s)")
        cur.close()
        conn.close()
    except Exception:
        pass


# ── 各服务启停 ────────────────────────────────────────────────


def start_redis() -> bool:
    port = SERVICES["redis"]
    if port_in_use(port):
        print(f"  Redis            already running on :{port}")
        return True
    print(f"[Redis] Starting on port {port}...")
    try:
        spawn(["redis-server", "--port", str(port), "--save", "900", "1"], "redis.log")
    except FileNotFoundError:
        print("  FAILED: redis-server not found (install via scoop or MSI)")
        return False
    for _ in range(10):
        if port_in_use(port):
            print(f"  Redis            ready :{port}")
            return True
        time.sleep(0.5)
    print("  FAILED: Redis did not start")
    return False


def start_backend() -> bool:
    port = SERVICES["backend"]
    print(f"[Backend] Starting Django on port {port}...")
    spawn(
        [
            sys.executable,
            "-m",
            "daphne",
            "-p",
            str(port),
            "-b",
            "0.0.0.0",
            "config.asgi:application",
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


def stop_redis() -> None:
    print("[Redis] Skipped (keep running for other services)")


def stop_backend() -> None:
    port = SERVICES["backend"]
    print(f"[Backend] Stopping port {port}...")
    kill_port(port)


def stop_frontend() -> None:
    port = SERVICES["frontend"]
    print(f"[Frontend] Stopping port {port}...")
    kill_port(port)


_START = {"redis": start_redis, "backend": start_backend, "frontend": start_frontend}
_STOP = {"redis": stop_redis, "backend": stop_backend, "frontend": stop_frontend}
_LOGS = {"redis": "redis.log", "backend": "backend.log", "frontend": "frontend.log"}


# ── 命令 ─────────────────────────────────────────────────────


def cmd_start(services: list[str]) -> None:
    names = resolve_services(services)
    for s in names:
        if s != "redis":
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
    if "redis" in order:
        print(f"  Redis       : redis://localhost:{SERVICES['redis']}")
    print(f"  Admin       : http://localhost:{SERVICES['backend']}/admin/  (admin/admin123)")
    print("=" * 54)


def cmd_stop(services: list[str]) -> None:
    names = resolve_services(services)
    if "backend" in names:
        cleanup_mysql_connections()
    for s in names:
        _STOP[s]()
    print("Done.")


def cmd_restart(services: list[str]) -> None:
    names = resolve_services(services)
    if "backend" in names:
        cleanup_mysql_connections()
    for s in names:
        if s != "redis":
            _STOP[s]()
    time.sleep(2)
    cmd_start(names)


def cmd_status() -> None:
    def http_ok(url: str) -> str:
        try:
            urllib.request.urlopen(url, timeout=2)
            return "ONLINE"
        except Exception:
            return "OFFLINE"

    redis_port = SERVICES["redis"]
    be_port = SERVICES["backend"]
    fe_port = SERVICES["frontend"]
    print(
        f"  Redis            (:{redis_port})  {'ONLINE' if port_in_use(redis_port) else 'OFFLINE'}"
    )
    print(f"  Django backend   (:{be_port})  {http_ok(f'http://127.0.0.1:{be_port}/')}")
    print(f"  Vue frontend     (:{fe_port})  {http_ok(f'http://127.0.0.1:{fe_port}/')}")


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


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Android-AutoTests platform manager")
    p.add_argument("cmd", choices=["start", "stop", "restart", "status", "logs"])
    p.add_argument("services", nargs="*", default=[], help="redis backend frontend (default: all)")
    args = p.parse_args()

    {
        "start": lambda: cmd_start(args.services),
        "stop": lambda: cmd_stop(args.services),
        "restart": lambda: cmd_restart(args.services),
        "status": cmd_status,
        "logs": lambda: cmd_logs(args.services),
    }[args.cmd]()
