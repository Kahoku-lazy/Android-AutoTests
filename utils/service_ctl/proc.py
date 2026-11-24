from __future__ import annotations

import os
import subprocess
import time
import urllib.request

from pathlib import Path

from .config import IS_WIN, LOG_DIR, ROOT, base_env

PROCESS_QUERY_TIMEOUT = 5
GRACEFUL_POLL_SECONDS = 0.5
GRACEFUL_POLL_TIMES = 6


def _run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, capture_output=True, text=True, timeout=PROCESS_QUERY_TIMEOUT, **kwargs
    )


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
    except Exception:  # noqa: BLE001 - 查询命令缺失/超时一律按“查不到”处理
        return None
    return None


def pid_alive(pid: str) -> bool:
    try:
        if IS_WIN:
            out = _run(["tasklist", "/FI", f"PID eq {pid}", "/NH"]).stdout
            return pid in out
        os.kill(int(pid), 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill(pid: str, force: bool = False) -> None:
    if IS_WIN:
        command = ["taskkill", "/PID", pid] + (["/F"] if force else [])
    else:
        command = ["kill", "-9", pid] if force else ["kill", pid]
    try:
        _run(command)
    except Exception:  # noqa: BLE001 - 进程可能已自行退出，属预期；调用方用 pid_alive 复核
        pass


def graceful_kill(pid: str) -> bool:
    kill(pid, force=False)
    for _ in range(GRACEFUL_POLL_TIMES):
        time.sleep(GRACEFUL_POLL_SECONDS)
        if not pid_alive(pid):
            return True
    return False


def kill_port(port: int) -> bool:
    pid = find_listening_pid(port)
    if not pid:
        return False
    if graceful_kill(pid):
        print(f"  Killed PID {pid} (port {port}) — graceful")
        return True
    kill(pid, force=True)
    time.sleep(0.5)
    print(f"  Killed PID {pid} (port {port}) — forced")
    return True


def wait_http(url: str, timeout: int = 20) -> bool:
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:  # noqa: BLE001 - 服务尚未就绪的常见形态：连接被拒/超时，继续轮询
            time.sleep(1)
    return False


def make_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in base_env().items():
        env.setdefault(key, value)
    if extra:
        env.update(extra)
    return env


def spawn(
    command: list[str],
    log_name: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.Popen:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = (LOG_DIR / log_name).open("a")
    try:
        kwargs: dict = {
            "cwd": str(cwd or ROOT),
            "stdin": subprocess.DEVNULL,
            "stdout": log_file,
            "stderr": subprocess.STDOUT,
            "env": env or make_env(),
        }
        if IS_WIN:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return subprocess.Popen(command, **kwargs)
    finally:
        log_file.close()
