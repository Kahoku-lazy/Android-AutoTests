"""
python -m 调试路径: engines.agents.workflow.platform_run

本模块的业务功能如下：
1. run_platform_sop: 平台启动 SOP。校验 YAML，按序跑用例，不接收工具清单。
2. request_cancel: 取消正在跑的 SOP 事件流。
"""

from __future__ import annotations

import asyncio
import inspect
import threading

from collections.abc import Callable
from pathlib import Path

from engines.agents.event_log import write_line
from engines.agents.event_sink import (
    MAX_MODEL_CALLS,
    MAX_RUN_SECONDS,
    budget_exceeded,
    set_case_title,
    set_step_context,
)
from engines.agents.role.agents import build_executor, build_verifier
from engines.agents.workflow.case_file import LOAD_FAIL, LOAD_OK, validate_platform_yaml
from engines.agents.workflow.handover_guard import IncompleteHandoverGuard
from engines.agents.workflow.ui_auto_workflow import AgentSOPWorkflow

_cancel_events: dict[int, threading.Event] = {}
_inflight: dict[int, tuple[asyncio.AbstractEventLoop, asyncio.Task]] = {}

CaseRunner = Callable[[str, list[tuple[str, str]], str], str]
AppCloser = Callable[[str], None]


def bind_cancel(task_id: int) -> threading.Event:
    """为一次平台任务登记取消信号。"""
    event = threading.Event()
    _cancel_events[task_id] = event
    return event


def request_cancel(task_id: int) -> None:
    """取消正在跑的 SOP 事件流。不调用角色基类的中断方法。"""
    event = _cancel_events.get(task_id)
    if event is not None:
        event.set()
    pair = _inflight.get(task_id)
    if pair is None:
        return
    loop, task = pair
    if loop.is_running():
        loop.call_soon_threadsafe(task.cancel)


def clear_cancel(task_id: int) -> None:
    """任务结束后丢掉取消登记。"""
    _cancel_events.pop(task_id, None)
    _inflight.pop(task_id, None)


def run_platform_sop(
    yaml_path: str,
    opening: str,
    *,
    task_id: int = 0,
    case_title: str = "",
    run_case: CaseRunner | None = None,
    device_serial: str = "",
    close_recent_apps: AppCloser | None = None,
) -> dict:
    """按 YAML 跑 SOP。工具与模型都由引擎代码写死装配，本函数不接收工具清单与模型。

    Args:
        yaml_path: YAML 文件路径。
        opening: 开场说明。
        task_id: 平台任务 id。0 表示不登记取消。
        case_title: 只跑该标题的用例；空串表示按文件顺序跑全部。
        run_case: 替身。省略时用代码里写死的模型与工具包跑真 SOP。
        device_serial: 收尾时要关闭应用的设备。空串则跳过收尾。
        close_recent_apps: 收尾替身。省略时由引擎连设备关闭最近任务。

    Returns:
        load_message、reason、status、completed、failed。单条用例失败只记入 failed，
        其余用例继续执行。
    """
    path = Path(yaml_path)
    if not path.is_file():
        return _fail("YAML 文件不存在")
    cases, reason = validate_platform_yaml(path.read_text(encoding="utf-8"))
    if reason:
        return _fail(reason)
    wanted = str(case_title or "").strip()
    if wanted:
        cases = [case for case in cases if case.title == wanted]
        if not cases:
            return {
                "load_message": LOAD_OK,
                "reason": f"用例「{wanted}」不存在",
                "status": "fail",
                "completed": [],
            }
    cancel_event = _cancel_events.get(task_id)
    if run_case is not None:
        return _drive_stub(cases, opening, run_case, cancel_event, device_serial, close_recent_apps)
    return asyncio.run(
        _drive_real(
            cases,
            opening,
            task_id,
            cancel_event,
            device_serial,
            close_recent_apps,
        )
    )


def _drive_stub(
    cases,
    opening: str,
    run_case: CaseRunner,
    cancel_event,
    device_serial: str,
    closer: AppCloser | None,
) -> dict:
    completed: list[str] = []
    failed: list[str] = []
    try:
        for case in cases:
            if cancel_event is not None and cancel_event.is_set():
                return _cancelled(completed, failed)
            set_case_title(case.title)
            set_step_context(None, None)
            steps = [(step.action, step.expected) for step in case.steps]
            try:
                phase = run_case(case.title, steps, opening)
            finally:
                _close_after_case(device_serial, closer)
            if phase == "cancelled":
                return _cancelled(completed, failed)
            if phase != "completed":
                failed.append(case.title)
                continue
            completed.append(case.title)
        return _finished(completed, failed)
    except asyncio.CancelledError:
        return _cancelled(completed, failed)


async def _drive_real(
    cases,
    opening,
    task_id,
    cancel_event,
    device_serial: str,
    closer: AppCloser | None,
) -> dict:
    current = asyncio.current_task()
    if task_id and current is not None:
        _inflight[task_id] = (asyncio.get_running_loop(), current)
    completed: list[str] = []
    failed: list[str] = []
    try:
        for case in cases:
            if cancel_event is not None and cancel_event.is_set():
                return _cancelled(completed, failed)
            # 用例名与步骤号逐条刷新：一个任务可以按序跑多条用例
            set_case_title(case.title)
            set_step_context(None, None)
            # 每条用例新建角色，避免上一条用例的对话与工具返回污染下一条
            executor = build_executor()
            verifier = build_verifier()
            workflow = AgentSOPWorkflow(IncompleteHandoverGuard(executor.agent), verifier.agent)
            steps = [(step.action, step.expected) for step in case.steps]
            try:
                phase = await workflow.run_workflow(case.title, steps, opening)
            finally:
                _close_after_case(device_serial, closer)
            if phase == "completed":
                completed.append(case.title)
            elif phase == "cancelled":
                return _cancelled(completed, failed)
            else:
                failed.append(case.title)
            if budget_exceeded():
                return _budget_stop(completed, failed)
        return _finished(completed, failed)
    except asyncio.CancelledError:
        return _cancelled(completed, failed)
    finally:
        _inflight.pop(task_id, None)


def _close_after_case(device_serial: str, closer: AppCloser | None) -> None:
    """一条已开始的用例结束后关闭最近任务。空序列号跳过。收尾失败不外抛。"""
    serial = str(device_serial or "").strip()
    if not serial:
        write_line("-", "收尾跳过：设备序列号为空")
        return
    finish = closer
    if finish is None:
        from engines.device.android.recent_apps import close_recent_apps

        finish = close_recent_apps
    try:
        finish(serial)
    except Exception as exc:
        write_line("-", f"收尾关闭应用失败：{exc}")


def _finished(completed: list[str], failed: list[str]) -> dict:
    """整轮结束的结果：有失败用例时状态为 fail，并汇总全部失败标题。"""
    if not failed:
        return _succeeded(completed)
    return {
        "load_message": LOAD_OK,
        "reason": "；".join(f"用例「{title}」未完成" for title in failed),
        "status": "fail",
        "completed": list(completed),
        "failed": list(failed),
    }


def _succeeded(completed: list[str]) -> dict:
    return {
        "load_message": LOAD_OK,
        "reason": "",
        "status": "success",
        "completed": list(completed),
        "failed": [],
    }


def _budget_stop(completed: list[str], failed: list[str]) -> dict:
    """运行预算用尽：停止整轮，已完成的用例保留。

    Args:
        completed: 已完成的用例标题。
        failed: 已判定失败的用例标题。

    Returns:
        status 为 fail 的结果，reason 写明命中的上限。
    """
    return {
        "load_message": LOAD_OK,
        "reason": (
            f"运行预算超限（模型调用上限 {MAX_MODEL_CALLS} 次，"
            f"运行时长上限 {MAX_RUN_SECONDS} 秒），已停止整轮"
        ),
        "status": "fail",
        "completed": list(completed),
        "failed": list(failed),
    }


def _fail(reason: str) -> dict:
    return {
        "load_message": LOAD_FAIL,
        "reason": reason,
        "status": "fail",
        "completed": [],
        "failed": [],
    }


def _cancelled(completed: list[str], failed: list[str] | None = None) -> dict:
    return {
        "load_message": LOAD_OK,
        "reason": "用户关闭",
        "status": "cancelled",
        "completed": list(completed),
        "failed": list(failed or []),
    }


def platform_entry_accepts_tools() -> bool:
    """供测试确认入口参数里没有工具清单。"""
    return "tools" in inspect.signature(run_platform_sop).parameters
