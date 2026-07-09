"""
Android-AutoTests platform manager — start / stop / restart / status.
Usage:
    python run.py start
    python run.py stop
    python run.py restart
    python run.py status
    python run.py logs
"""

import sys
import os
import time
import socket
import signal
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).parent


# ── Load .env file ──
def _load_dotenv():
    """Load .env file into os.environ. No dependency on python-dotenv."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:  # 不覆盖已有的环境变量
                os.environ[key] = value


_load_dotenv()
BACKEND_PORT = 8765
FRONTEND_PORT = 5173
AGENTSCOPE_PORT = 8000
REDIS_PORT = 6379
LOG_DIR = ROOT / "logs"

# ── 数据库配置（settings.py 默认使用 MySQL）──
MYSQL_ENV = {
    "DB_ENGINE": "mysql",
    "DB_NAME": "android_autotests",
    "DB_USER": "root",
    "DB_PASSWORD": os.environ.get("DB_PASSWORD", ""),
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "3306",
    "PYTHONUTF8": "1",
    "DJANGO_SETTINGS_MODULE": "config.settings",
}


def port_in_use(port):
    """检查端口是否被占用（用 connect 探测，比 bind 在 Windows 上更可靠）。

    Windows 上 socket.bind() 对已在监听的端口可能不抛异常
    （取决于原 socket 绑定地址 0.0.0.0 vs 127.0.0.1），
    所以改用 connect_ex 探测是否可连接。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0  # 0 = 连接成功 = 端口在用
    except OSError:
        return False


def kill_port(port):
    """按平台释放端口占用进程（Windows 用 netstat+taskkill，*nix 用 lsof+kill）。"""
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
            # macOS / Linux：lsof 查监听该端口的 PID，逐个 kill
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for pid in result.stdout.split():
                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
                print(f"  Killed PID {pid} (port {port})")
                killed = True
    except Exception as e:
        print(f"  Error killing port {port}: {e}")
    return killed


def wait_http(url, timeout=20):
    """Wait for HTTP server to respond with 2xx/3xx on given URL."""
    import urllib.request

    for i in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def make_env(extra=None):
    """构建子进程环境变量，注入 MySQL + UTF-8 配置。"""
    env = os.environ.copy()
    # 只在用户未设置时注入默认 MySQL 配置（允许用户通过环境变量覆盖）
    for k, v in MYSQL_ENV.items():
        env.setdefault(k, v)
    if extra:
        env.update(extra)
    return env


def start_redis():
    """启动 Redis（如已运行则跳过）。"""
    if port_in_use(REDIS_PORT):
        print(f"[Redis] Already running on port {REDIS_PORT}")
        return True
    print(f"[Redis] Starting on port {REDIS_PORT}...")
    redis_cmd = "redis-server.cmd" if sys.platform == "win32" else "redis-server"
    try:
        subprocess.Popen(
            [redis_cmd, "--port", str(REDIS_PORT)],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=open(str(LOG_DIR / "redis.log"), "a"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except FileNotFoundError:
        print("  FAILED: redis-server not found. Install via: scoop install redis")
        return False
    # Redis 启动很快，用 socket 探测
    for i in range(10):
        if port_in_use(REDIS_PORT):
            print(f"  Ready: redis://localhost:{REDIS_PORT}")
            return True
        time.sleep(0.5)
    print("  FAILED: Redis did not start")
    return False


def start_backend():
    print("[Backend] Starting Django on port 8765...")
    log_file = LOG_DIR / "backend.log"
    LOG_DIR.mkdir(exist_ok=True)
    # 标记本进程为 ASGI 服务进程 —— test_runner 的启动恢复只在此进程执行
    env = make_env({"DJANGO_ASGI_SERVER": "1"})
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "daphne",
            "-p",
            str(BACKEND_PORT),
            "-b",
            "0.0.0.0",
            "config.asgi:application",
        ],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=open(str(log_file), "a"),
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if wait_http(f"http://127.0.0.1:{BACKEND_PORT}/", 20):
        print("  Ready: http://localhost:8765")
        return True
    else:
        print("  FAILED: backend did not start (check logs/backend.log)")
        return False


def start_agentscope():
    print(f"[AgentScope] Starting FastAPI on port {AGENTSCOPE_PORT}...")
    log_file = LOG_DIR / "agentscope.log"
    LOG_DIR.mkdir(exist_ok=True)
    env = make_env()
    subprocess.Popen(
        [sys.executable, "run_agentscope.py", "--port", str(AGENTSCOPE_PORT)],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=open(str(log_file), "a"),
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    # 注意：AgentScope 的根路径 / 返回 404，必须检查 /docs 或 /openapi.json
    if wait_http(f"http://127.0.0.1:{AGENTSCOPE_PORT}/docs", 30):
        print(f"  Ready: http://localhost:{AGENTSCOPE_PORT}/docs")
        return True
    else:
        print("  FAILED: AgentScope did not start (check logs/agentscope.log)")
        return False


def start_frontend():
    print("[Frontend] Starting Vite on port 5173...")
    log_file = LOG_DIR / "frontend.log"
    LOG_DIR.mkdir(exist_ok=True)
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    subprocess.Popen(
        [npx_cmd, "vite", "--host"],
        cwd=str(ROOT / "frontend"),
        stdin=subprocess.DEVNULL,
        stdout=open(str(log_file), "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if wait_http(f"http://127.0.0.1:{FRONTEND_PORT}/", 30):
        print("  Ready: http://localhost:5173")
        return True
    else:
        print("  FAILED: frontend did not start (check logs/frontend.log)")
        return False


def cmd_start():
    print("Stopping existing processes...")
    kill_port(BACKEND_PORT)
    kill_port(AGENTSCOPE_PORT)
    kill_port(FRONTEND_PORT)
    time.sleep(2)

    print()
    # Redis 必须先启动（Django Channels + AgentScope 都依赖）
    if not start_redis():
        print("  [WARN] Redis failed to start — WebSocket/streaming will be unavailable")
    if not start_backend():
        return
    if not start_agentscope():
        print("  [WARN] AgentScope failed to start — continuing without AI tools")
    if not start_frontend():
        return

    print()
    print("=" * 54)
    print("  Android-AutoTests Platform")
    print("  Frontend    : http://localhost:5173")
    print("  API (Django): http://localhost:8765")
    print("  AI (AgentS) : http://localhost:8000/docs")
    print("  Redis       : redis://localhost:6379")
    print("  Admin       : http://localhost:8765/admin/  (admin/admin123)")
    print("  DB          : MySQL android_autotests")
    print(
        "  Logs        : logs/backend.log  logs/frontend.log  logs/agentscope.log  logs/redis.log"
    )
    print("=" * 54)


def cmd_stop():
    print("Stopping platform...")
    kill_port(BACKEND_PORT)
    kill_port(AGENTSCOPE_PORT)
    kill_port(FRONTEND_PORT)
    # Redis 不主动停止（其他服务可能也在用）
    print("Done. (Redis left running on :6379)")


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    cmd_start()


def cmd_status():
    import urllib.request

    def check(url):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            return False

    redis_on = port_in_use(REDIS_PORT)
    backend_on = check(f"http://127.0.0.1:{BACKEND_PORT}/")
    agentscope_on = check(f"http://127.0.0.1:{AGENTSCOPE_PORT}/docs")
    frontend_on = check(f"http://127.0.0.1:{FRONTEND_PORT}/")
    print(f"  Redis            (:6379)  {'ONLINE' if redis_on else 'OFFLINE'}")
    print(f"  Django backend   (:8765)  {'ONLINE' if backend_on else 'OFFLINE'}")
    print(f"  AgentScope AI    (:8000)  {'ONLINE' if agentscope_on else 'OFFLINE'}")
    print(f"  Vue frontend     (:5173)  {'ONLINE' if frontend_on else 'OFFLINE'}")


def cmd_logs():
    for name in ["redis.log", "backend.log", "agentscope.log", "frontend.log"]:
        f = LOG_DIR / name
        print(f"\n=== {name} (last 20 lines) ===")
        if f.exists():
            lines = f.read_text(encoding="utf-8", errors="replace").strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        else:
            print("  (empty)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Android-AutoTests platform manager")
    p.add_argument("cmd", choices=["start", "stop", "restart", "status", "logs"])
    args = p.parse_args()

    {
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "logs": cmd_logs,
    }[args.cmd]()
