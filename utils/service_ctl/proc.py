"""
模块功能：➡️ 进程与端口工具：查监听端口、判断存活、优雅/强制结束、后台拉起、HTTP 就绪等待 🏁
Python 调试：➡️ python -m utils.service_ctl.proc 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_platform_proc.py: 端口查找、存活判断、结束流程
🏁
"""

from __future__ import annotations

import os
import subprocess
import time
import urllib.request

from pathlib import Path

from .config import IS_WIN, LOG_DIR, ROOT, base_env

# 进程查询类命令（netstat/tasklist/lsof）的最长等待，避免卡住启动流程。
PROCESS_QUERY_TIMEOUT = 5
# 优雅结束的轮询间隔与次数：6 × 0.5s = 最多等 3 秒。
GRACEFUL_POLL_SECONDS = 0.5
GRACEFUL_POLL_TIMES = 6


def _run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    """执行进程查询命令并捕获输出（超时 5 秒）。"""
    return subprocess.run(
        command, capture_output=True, text=True, timeout=PROCESS_QUERY_TIMEOUT, **kwargs
    )


def find_listening_pid(port: int) -> str | None:
    """返回监听该 TCP 端口的 PID；没有监听或查询失败时返回 None。"""
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
    """PID 是否仍存活（Windows 用 tasklist，其它平台用信号 0 探测）。"""
    try:
        if IS_WIN:
            out = _run(["tasklist", "/FI", f"PID eq {pid}", "/NH"]).stdout
            return pid in out
        os.kill(int(pid), 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill(pid: str, force: bool = False) -> None:
    """结束进程；杀不到不抛错（stop 与自然退出的竞态由调用方用 `pid_alive` 复核）。"""
    if IS_WIN:
        command = ["taskkill", "/PID", pid] + (["/F"] if force else [])
    else:
        command = ["kill", "-9", pid] if force else ["kill", pid]
    try:
        _run(command)
    except Exception:  # noqa: BLE001 - 进程可能已自行退出，属预期；调用方用 pid_alive 复核
        pass


def graceful_kill(pid: str) -> bool:
    """先请求优雅退出并轮询；在限定次数内退出返回 True。"""
    kill(pid, force=False)
    for _ in range(GRACEFUL_POLL_TIMES):
        time.sleep(GRACEFUL_POLL_SECONDS)
        if not pid_alive(pid):
            return True
    return False


def kill_port(port: int) -> bool:
    """先优雅退出，超时再强制杀；端口没有监听时返回 False。"""
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
    """轮询 HTTP 地址（1 秒一次）；timeout 秒内可访问返回 True。"""
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:  # noqa: BLE001 - 服务尚未就绪的常见形态：连接被拒/超时，继续轮询
            time.sleep(1)
    return False


def make_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """子进程环境：复制当前环境，补齐平台默认值，最后叠加调用方额外项。"""
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
    """后台拉起进程：stdin 关闭、输出追加到 `logs/<log_name>`，父进程不保留日志句柄。"""
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
        # 子进程已继承句柄；父进程关掉自己那份，避免句柄泄漏（Windows 上子进程照常写日志）
        log_file.close()
