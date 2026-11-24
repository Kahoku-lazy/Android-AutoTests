"""
模块功能：➡️ 按注册表启停服务：拉起并等待就绪、停机排空、空闲连接清理与超时名单 🏁
Python 调试：➡️ python -m utils.service_ctl.services 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_platform_services.py: 启停与排空
2. tests/task/unit/test_task_sweep.py: 停机超时名单与启动清扫
🏁
"""

from __future__ import annotations

import json
import time
import urllib.request

from . import db
from .config import ROOT, ServiceSpec, stop_drain_timeout
from .proc import kill_port, make_env, spawn, wait_http

# 停机等满后留下的任务编号：后端启动清扫据此把任务标成 stop_timeout
STOP_TIMEOUT_MARK = ROOT / "temps" / "stop-timeout-tasks.json"
DRAIN_REPORT_SECONDS = 10


def start_service(spec: ServiceSpec) -> bool:
    """拉起一个服务并等待就绪；就绪返回 True，超时给出日志位置并返回 False。"""
    print(f"[{spec.label}] Starting {spec.runtime} on port {spec.port}...")
    spawn(list(spec.command), spec.log, cwd=spec.cwd, env=make_env(spec.extra_env))
    if wait_http(f"http://127.0.0.1:{spec.port}/", spec.ready_timeout):
        print(f"  {spec.label:<17}ready http://localhost:{spec.port}")
        return True
    print(f"  FAILED: {spec.name} did not start (check logs/{spec.log})")
    return False


def stop_service(spec: ServiceSpec) -> None:
    """停一个服务：需要排空的服务先等任务归零，再杀端口。"""
    print(f"[{spec.label}] Stopping port {spec.port}...")
    if spec.drain:
        drain_backend(spec.port)
        db.cleanup_idle_connections(db.DbConfig.from_env())
    kill_port(spec.port)


def drain_backend(port: int) -> None:
    """停机前停止派发并等待 running 归零；后端不可达时直接返回。"""
    base = f"http://127.0.0.1:{port}/api/system/drain/"
    try:
        request = urllib.request.Request(base, method="POST", data=b"")
        with urllib.request.urlopen(request, timeout=3) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - 后端没起/已停：没有可排空的任务，直接进入下一步
        return
    running = int((payload.get("data") or {}).get("running") or 0)
    if running <= 0:
        return

    timeout = stop_drain_timeout()
    deadline = time.time() + timeout
    print(f"  Waiting for {running} running task(s), up to {timeout}s...")
    last_report = time.time()
    while time.time() < deadline:
        time.sleep(2)
        try:
            with urllib.request.urlopen(base, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data") or {}
        except Exception:  # noqa: BLE001 - 后端中途退出：视为已无可排空任务
            return
        running = int(data.get("running") or 0)
        if running <= 0:
            print("  All tasks finished — stopping backend.")
            return
        if time.time() - last_report >= DRAIN_REPORT_SECONDS:
            left = max(int(deadline - time.time()), 0)
            print(f"  Still {running} running task(s), {left}s left...")
            last_report = time.time()
    print("  Drain timeout reached — forcing stop.")
    write_stop_timeout_mark(running_ids_from_drain(base))


def running_ids_from_drain(base: str) -> list[int]:
    """再问一次仍在跑的编号。后端不可达时返回空列表，不阻止停机。"""
    try:
        with urllib.request.urlopen(base, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data") or {}
    except Exception:  # noqa: BLE001 - 停机路径：查询失败不阻止杀进程
        return []
    raw = data.get("running_ids") or []
    found = []
    for item in raw:
        try:
            found.append(int(item))
        except (TypeError, ValueError):
            continue
    return found


def write_stop_timeout_mark(ids: list[int]) -> None:
    """停机等满后留下编号。写失败只打印，不阻止杀进程。"""
    if not ids:
        return
    try:
        STOP_TIMEOUT_MARK.parent.mkdir(parents=True, exist_ok=True)
        STOP_TIMEOUT_MARK.write_text(
            json.dumps(
                {"ids": ids, "written_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"  Could not write stop-timeout mark: {exc}")
