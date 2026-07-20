"""
Android-AutoTests platform manager — start / stop / restart / status / logs.

Usage:
    python run.py start                            # 启动全部服务
    python run.py start backend agentscope          # 只启动指定服务
    python run.py stop                              # 停止全部
    python run.py stop frontend                     # 只停止指定服务
    python run.py restart                           # 重启全部
    python run.py restart backend                   # 只重启指定服务
    python run.py status                            # 查看全部状态
    python run.py logs                              # 查看全部日志（各 20 行）
    python run.py logs backend                      # 查看指定服务日志

可用服务名: redis  backend  agentscope  frontend
"""

import sys
import os
import time
import socket
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"

SERVICES = {
    "redis":      6379,
    "backend":    8766,
    "agentscope": 8088,
    "frontend":   5174,
}

# ── 基础环境变量 ──
BASE_ENV = {
    "DB_ENGINE": "mysql",
    "DB_NAME": "android_autotests",
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "3306",
    "PYTHONUTF8": "1",
    "DJANGO_SETTINGS_MODULE": "config.settings",
}


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def port_in_use(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except OSError:
        return False


def kill_port(port):
    killed = False
    try:
        if sys.platform == "win32":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)
                    print(f"  Killed PID {pid} (port {port})")
                    killed = True
        else:
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=5,
            )
            for pid in result.stdout.split():
                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
                print(f"  Killed PID {pid} (port {port})")
                killed = True
    except Exception as e:
        print(f"  Error killing port {port}: {e}")
    return killed


def wait_http(url, timeout=20):
    import urllib.request
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def make_env(extra=None):
    env = os.environ.copy()
    for k, v in BASE_ENV.items():
        env.setdefault(k, v)
    if extra:
        env.update(extra)
    return env


def spawn(cmd, log_name, cwd=None, env=None):
    """启动子进程，输出写入日志文件。"""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / log_name
    return subprocess.Popen(
        cmd,
        cwd=str(cwd or ROOT),
        stdin=subprocess.DEVNULL,
        stdout=open(str(log_file), "a"),
        stderr=subprocess.STDOUT,
        env=env or make_env(),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def resolve_services(names):
    """解析服务名列表，空或 'all' 返回全部。"""
    if not names or "all" in names:
        return list(SERVICES.keys())
    invalid = [n for n in names if n not in SERVICES]
    if invalid:
        print(f"Unknown services: {', '.join(invalid)}")
        print(f"Available: {', '.join(SERVICES.keys())}")
        sys.exit(1)
    return names


# ═══════════════════════════════════════════════════════════════
# 各服务启停
# ═══════════════════════════════════════════════════════════════

def start_redis():
    port = SERVICES["redis"]
    if port_in_use(port):
        print(f"  Redis            already running on :{port}")
        return True
    print(f"[Redis] Starting on port {port}...")
    redis_cmd = "redis-server.cmd" if sys.platform == "win32" else "redis-server"
    try:
        spawn([redis_cmd, "--port", str(port)], "redis.log")
    except FileNotFoundError:
        print("  FAILED: redis-server not found")
        return False
    for _ in range(10):
        if port_in_use(port):
            print(f"  Redis            ready :{port}")
            return True
        time.sleep(0.5)
    print("  FAILED: Redis did not start")
    return False


def start_backend():
    port = SERVICES["backend"]
    print(f"[Backend] Starting Django on port {port}...")
    env = make_env({"DJANGO_ASGI_SERVER": "1"})
    spawn(
        [sys.executable, "-m", "daphne", "-p", str(port), "-b", "0.0.0.0", "config.asgi:application"],
        "backend.log", env=env,
    )
    if wait_http(f"http://127.0.0.1:{port}/", 20):
        print(f"  Backend          ready http://localhost:{port}")
        return True
    print("  FAILED: backend did not start (check logs/backend.log)")
    return False


def start_agentscope():
    port = SERVICES["agentscope"]
    print(f"[AgentScope] Starting FastAPI on port {port}...")

    # Write inline launch script to temp file (avoids shell escaping issues)
    launcher = LOG_DIR / "_agentscope_launcher.py"
    LOG_DIR.mkdir(exist_ok=True)
    launcher.write_text(f'''
import sys; sys.path.insert(0, r"D:/Github/Android-AutoTests")
import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
import uvicorn
from agentscope_service.app import create_agentscope_app, RedisUnavailableError
from config.agentscope_config import TITLE, VERSION
try:
    app = create_agentscope_app()
except RedisUnavailableError:
    print("AgentScope startup failed: Redis unavailable")
    import sys; sys.exit(1)
print(f"  {{TITLE}} v{{VERSION}}")
uvicorn.run(app, host="0.0.0.0", port={port}, log_level="info")
'''.strip())

    spawn(
        [sys.executable, str(launcher)],
        "agentscope.log",
    )
    if wait_http(f"http://127.0.0.1:{port}/docs", 30):
        print(f"  AgentScope       ready http://localhost:{port}/docs")
        return True
    print("  FAILED: AgentScope did not start (check logs/agentscope.log)")
    return False


def start_frontend():
    port = SERVICES["frontend"]
    print(f"[Frontend] Starting Vite on port {port}...")
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    spawn(
        [npx_cmd, "vite", "--host"],
        "frontend.log", cwd=ROOT / "frontend",
    )
    if wait_http(f"http://127.0.0.1:{port}/", 30):
        print(f"  Frontend         ready http://localhost:{port}")
        return True
    print("  FAILED: frontend did not start (check logs/frontend.log)")
    return False


def stop_redis():
    print("[Redis] Skipped (keep running for other services)")

def stop_backend():
    port = SERVICES["backend"]
    print(f"[Backend] Stopping port {port}...")
    kill_port(port)

def stop_agentscope():
    port = SERVICES["agentscope"]
    print(f"[AgentScope] Stopping port {port}...")
    kill_port(port)

def stop_frontend():
    port = SERVICES["frontend"]
    print(f"[Frontend] Stopping port {port}...")
    kill_port(port)


_START = {"redis": start_redis, "backend": start_backend, "agentscope": start_agentscope, "frontend": start_frontend}
_STOP  = {"redis": stop_redis,  "backend": stop_backend,  "agentscope": stop_agentscope,  "frontend": stop_frontend}


# ═══════════════════════════════════════════════════════════════
# 命令实现
# ═══════════════════════════════════════════════════════════════

def cmd_start(services):
    names = resolve_services(services)

    # 先停再启（避免端口冲突）
    for s in names:
        if s != "redis":
            _STOP[s]()
    time.sleep(1)

    # 依赖顺序：redis → backend → agentscope → frontend
    order = [s for s in ["redis", "backend", "agentscope", "frontend"] if s in names]
    ok = True
    for s in order:
        if not _START[s]():
            ok = False
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
    if "agentscope" in order:
        print(f"  AI (AgentS) : http://localhost:{SERVICES['agentscope']}/docs")
    if "redis" in order:
        print(f"  Redis       : redis://localhost:{SERVICES['redis']}")
    print("  Admin       : http://localhost:8766/admin/  (admin/admin123)")
    print("=" * 54)


def cmd_stop(services):
    names = resolve_services(services)
    for s in names:
        _STOP[s]()
    print("Done.")


def cmd_restart(services):
    names = resolve_services(services)
    for s in names:
        if s != "redis":
            _STOP[s]()
    time.sleep(2)
    cmd_start(names)


def cmd_status():
    import urllib.request
    def check(url):
        try:
            urllib.request.urlopen(url, timeout=2)
            return "ONLINE"
        except Exception:
            return "OFFLINE"

    redis_ok = "ONLINE" if port_in_use(6379) else "OFFLINE"
    be_ok = check("http://127.0.0.1:8766/")
    as_ok = check("http://127.0.0.1:8088/docs")
    fe_ok = check("http://127.0.0.1:5174/")
    print(f"  Redis            (:6379)  {redis_ok}")
    print(f"  Django backend   (:8766)  {be_ok}")
    print(f"  AgentScope AI    (:8088)  {as_ok}")
    print(f"  Vue frontend     (:5174)  {fe_ok}")


def cmd_logs(services):
    log_map = {
        "redis":      "redis.log",
        "backend":    "backend.log",
        "agentscope": "agentscope.log",
        "frontend":   "frontend.log",
    }
    names = resolve_services(services)
    for s in names:
        f = LOG_DIR / log_map[s]
        print(f"\n=== {log_map[s]} (last 20 lines) ===")
        if f.exists():
            lines = f.read_text(encoding="utf-8", errors="replace").strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        else:
            print("  (empty)")


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Android-AutoTests platform manager")
    p.add_argument("cmd", choices=["start", "stop", "restart", "status", "logs"],
                   help="Action to perform")
    p.add_argument("services", nargs="*", default=[],
                   help="Services: redis backend agentscope frontend (default: all)")
    args = p.parse_args()

    if args.cmd == "start":
        cmd_start(args.services)
    elif args.cmd == "stop":
        cmd_stop(args.services)
    elif args.cmd == "restart":
        cmd_restart(args.services)
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "logs":
        cmd_logs(args.services)
