"""AI 任务后台线程：装配引擎、落进度与终态。

与 views_drf 解耦，供 api.dispatch_device / 提交入口共用。
"""

from __future__ import annotations

import asyncio
import threading

from pathlib import Path

from django.db import close_old_connections

from backend.models.constants import TaskKind, TaskStatus
from utils.logs import backend_log

from . import api
from .models import Task

# 引擎终态 → 任务终态。收尾映射集中一处，供回归测试校验状态常量完整。
RESULT_STATUS_MAP = {
    "success": TaskStatus.COMPLETED,
    "cancelled": TaskStatus.CANCELLED,
}

# 取消兜底：工作线程超时仍未退出时强制放行设备，避免线程挂死把设备永久占住。
CANCEL_RELEASE_SECONDS = 60

# 正在跑任务的工作线程与取消兜底计时器，都按任务 id 登记。
_workers: dict[int, threading.Thread] = {}
_release_timers: dict[int, threading.Timer] = {}


def schedule_cancel_release(
    task_id: int,
    serial: str,
    agent_id: int,
    *,
    timeout: float = CANCEL_RELEASE_SECONDS,
) -> None:
    """关闭任务后登记兜底放行：工作线程超时未退出时强制放行并留痕。

    Args:
        task_id: 被关闭的任务 id。
        serial: 该任务的设备 serial；空串表示不占设备，直接跳过。
        agent_id: 任务所属智能体 id，写告警事件时使用。
        timeout: 兜底等待秒数。

    Returns:
        None。计时器为 daemon 线程，不阻塞调用方。
    """
    if not (serial or "").strip():
        return
    timer = threading.Timer(timeout, _force_release_device, args=(task_id, serial, agent_id))
    timer.daemon = True
    _release_timers[task_id] = timer
    timer.start()


def release_device_now(task_id: int, serial: str) -> None:
    """工作线程退出时放行设备槽：撤掉兜底计时器并拉起同设备下一条任务。

    Args:
        task_id: 刚结束的任务 id。
        serial: 该任务的设备 serial；空串表示不占设备。

    Returns:
        None。
    """
    timer = _release_timers.pop(task_id, None)
    if timer is not None:
        timer.cancel()
    _workers.pop(task_id, None)
    serial = (serial or "").strip()
    if serial:
        api.dispatch_device(serial)


def _force_release_device(task_id: int, serial: str, agent_id: int) -> None:
    """兜底计时器回调：工作线程仍存活时写告警事件，然后强制放行设备。

    Args:
        task_id: 被关闭的任务 id。
        serial: 该任务的设备 serial。
        agent_id: 任务所属智能体 id。

    Returns:
        None。任何异常只记日志，不影响设备放行。
    """
    try:
        close_old_connections()
        thread = _workers.get(task_id)
        if thread is not None and thread.is_alive():
            _record_cancel_timeout(task_id, agent_id)
        api.dispatch_device(serial)
        _release_timers.pop(task_id, None)
    except Exception:  # noqa: BLE001 - 兜底放行失败只记日志，不能让计时器线程崩掉
        backend_log.exception("取消兜底放行失败 task_id=%s", task_id)
    finally:
        close_old_connections()


def _record_cancel_timeout(task_id: int, agent_id: int) -> None:
    """把「关闭后工作线程超时未退出」写成一条任务事件，供详情页与排障查看。

    Args:
        task_id: 被关闭的任务 id。
        agent_id: 任务所属智能体 id。

    Returns:
        None。落库失败只记日志。
    """
    from datetime import datetime

    from engines.agents.event_sink import (
        bind_run_context,
        bind_sink,
        reset_run_context,
        reset_sink,
    )
    from engines.agents.messaging.record import EventRecord

    from .event_store import TaskEventSink

    now = datetime.now()
    record = EventRecord(
        event_type="TaskCancelTimeoutEvent",
        phase="结束",
        block_type="interrupt",
        payload={
            "reason": f"关闭后 {CANCEL_RELEASE_SECONDS} 秒工作线程仍未退出，已强制放行设备",
            "task_id": task_id,
        },
        started_at=now,
        ended_at=now,
        duration_ms=0,
    )
    sink = TaskEventSink()
    sink_token = bind_sink(sink)
    run_token = bind_run_context(task_id, agent_id, "")
    try:
        sink.emit(record)
    except Exception:  # noqa: BLE001 - 告警事件写不进去也不影响放行
        backend_log.exception("记录取消超时事件失败 task_id=%s", task_id)
    finally:
        sink.close()
        reset_sink(sink_token)
        reset_run_context(run_token)


def run_task_async(task_id: int, agent_id: int) -> None:
    """后台线程入口：启动平台 SOP，并把加载结论与终态写回任务。"""
    from backend.apps.task_list.event_store import TaskEventSink
    from engines.agents.event_sink import bind_run_context, bind_sink, reset_run_context, reset_sink
    from engines.agents.workflow.platform_run import bind_cancel, run_platform_sop

    close_old_connections()
    ephemeral = False
    yaml_path = ""
    sink = None
    sink_token = None
    run_token = None
    serial = ""
    try:
        task = Task.objects.get(id=task_id)
        serial = task.device_serial or ""
        cancel_event = bind_cancel(task_id)
        sink = TaskEventSink()
        sink_token = bind_sink(sink)
        run_token = bind_run_context(task_id, agent_id, task.case_title or "")

        if task.task_kind == TaskKind.CASE_AUTHORING:
            result = _run_case_authoring(task, cancel_event)
            task.refresh_from_db()
            if task.status != TaskStatus.CANCELLED:
                status = RESULT_STATUS_MAP.get(result.get("status") or "", TaskStatus.FAILED)
                api.finalize_task(
                    task,
                    status=status,
                    result=api.dump_task_run_payload(result),
                    release_device=False,
                )
            return

        yaml_path, ephemeral = api.materialize_config_file(task)
        result = run_platform_sop(
            yaml_path,
            api.build_sop_run_input(task),
            task_id=task_id,
            case_title=task.case_title or "",
            device_serial=task.device_serial or "",
        )
        api.set_config_load_message(task, result.get("load_message") or "")
        # 取消优先：用户在跑的过程中关闭了任务，收尾不能把 cancelled 改写成别的终态
        task.refresh_from_db()
        if task.status == TaskStatus.CANCELLED:
            return
        status = RESULT_STATUS_MAP.get(result.get("status") or "", TaskStatus.FAILED)
        payload = {
            "status": result.get("status") or "fail",
            "summary": result.get("load_message") or "",
            "reason": result.get("reason") or "",
            "completed": result.get("completed") or [],
            "failed": result.get("failed") or [],
        }
        api.finalize_task(
            task,
            status=status,
            result=api.dump_task_run_payload(payload),
            release_device=False,
        )
    except Exception as exc:
        backend_log.exception("async task failed id=%s", task_id)
        try:
            api.finalize_task(
                Task.objects.get(id=task_id),
                status=TaskStatus.FAILED,
                result=f"执行异常: {exc}",
                release_device=False,
            )
        except Exception:
            backend_log.exception("finalize async task failed id=%s", task_id)
    finally:
        if sink is not None:
            try:
                sink.close()
            except Exception:
                backend_log.exception("flush task events failed id=%s", task_id)
        if sink_token is not None:
            reset_sink(sink_token)
        if run_token is not None:
            reset_run_context(run_token)
        if ephemeral and yaml_path:
            Path(yaml_path).unlink(missing_ok=True)
        from engines.agents.workflow.platform_run import clear_cancel

        clear_cancel(task_id)
        # 设备槽只在这里放行：取消路径不提前放行，避免两条任务抢同一台手机
        release_device_now(task_id, serial)
        close_old_connections()


def _run_case_authoring(task: Task, cancel_event=None) -> dict:
    """跑一次状态机三段式用例编写，返回可写入 Task.result 的结果字典。

    Args:
        task: 用例编写任务。
        cancel_event: 任务的取消信号；已置位时不再开跑。

    Returns:
        status / summary / phase / passed / artifact / facts / verdicts / document / reason。
    """
    from engines.agents.workflow.case_goal_workflow import run_case_authoring_artifact

    if cancel_event is not None and cancel_event.is_set():
        return _case_failed("用户关闭", status="cancelled")
    requirement = api.build_case_requirement(task)
    if not requirement.strip():
        return _case_failed("任务没有可解析的需求文档")

    try:
        result = asyncio.run(
            _await_case_run(
                run_case_authoring_artifact(
                    requirement,
                    project_code=api.case_project_code(task),
                    version="V1",
                ),
                cancel_event,
            )
        )
    except asyncio.CancelledError:
        return _case_failed("用户关闭", status="cancelled")
    if result is None:
        return _case_failed("用户关闭", status="cancelled")
    verdicts = [
        {"passed": passed, "message": message, "verifier": verifier}
        for passed, message, verifier in result.verdicts
    ]
    passed = bool(result.passed)
    reason = "" if passed else (result.reason or "未通过验收")
    case_import = (
        _import_case_artifact(task, result)
        if passed
        else _skipped_import("验收未通过或产物为空，未写入用例库")
    )
    counts = result.artifact.counts
    return {
        "status": "success" if passed else "fail",
        "summary": (
            f"用例已生成并通过验收（状态 {counts['states']} 个 / 迁移 {counts['transitions']} 条"
            f" / 场景 {counts['scenarios']} 条 / 用例 {counts['cases']} 条）"
            if passed
            else f"用例验收未通过（用例 {counts['cases']} 条）"
        ),
        "phase": result.phase,
        "passed": passed,
        "artifact": result.artifact.payload(),
        "facts": result.facts.payload(),
        "document": result.document,
        "verdicts": verdicts,
        "case_import": case_import,
        "reason": reason,
        "max_output_tokens": result.max_output_tokens,
    }


def _skipped_import(message: str) -> dict:
    """构造「未写入用例库」的结论，字段与导入服务保持一致。"""
    return {
        "status": "skipped",
        "project_id": None,
        "file_id": None,
        "path": "",
        "case_count": 0,
        "skipped_count": 0,
        "skipped": [],
        "message": message,
    }


def _import_case_artifact(task: Task, result) -> dict:
    """把验收通过的三段式产物写入用例库；失败只降级为结果字段。

    Args:
        task: 用例编写任务。
        result: 目标流水线结果，含 `artifact`。

    Returns:
        导入结论；失败时 status 为 failed 并带原因。
    """
    from backend.apps.case_manager.api import import_case_rows

    owner = str(task.created_by or getattr(task.agent, "owner_id", "") or "")
    if not owner:
        return _skipped_import("任务缺少发起人，未写入用例库")
    artifact = result.artifact
    state_names = {state.id: state.name for state in artifact.states}
    scenario_titles = {scenario.id: scenario.title for scenario in artifact.scenarios}
    fallback_module = artifact.states[0].name if artifact.states else ""
    rows = [
        {
            "source_case_id": case.id,
            "title": case.title,
            "priority": case.priority,
            "module": scenario_titles.get(case.scenario_id) or fallback_module,
            "precondition": state_names.get(case.pre_state, case.pre_state),
            "steps": [
                {
                    "action": step.action,
                    "assertion": state_names.get(step.expect_state, step.expect_state),
                }
                for step in case.steps
            ],
        }
        for case in artifact.cases
    ]
    if not rows:
        return _skipped_import("产物里没有用例，未写入用例库")
    try:
        return import_case_rows(
            user_id=owner,
            task_id=task.id,
            task_title=task.title or "",
            rows=rows,
        )
    except Exception as exc:  # noqa: BLE001 - 导入失败不能改变任务验收结论
        backend_log.exception("import case authoring artifact failed task=%s", task.id)
        return {
            **_skipped_import(f"写入用例库失败：{exc}"),
            "status": "failed",
        }


def _case_failed(reason: str, *, status: str = "fail") -> dict:
    """用例编写任务在开跑前终止时的结果。"""
    return {
        "status": status,
        "summary": reason,
        "phase": status,
        "passed": False,
        "artifact": {
            "states": [],
            "transitions": [],
            "scenarios": [],
            "cases": [],
            "diagram": "",
            "report": "",
            "counts": {},
        },
        "facts": {"blocking": [], "warnings": []},
        "document": "",
        "verdicts": [],
        "case_import": _skipped_import(reason),
        "reason": reason,
        "max_output_tokens": 0,
    }


async def _await_case_run(run, cancel_event):
    """跑模块化用例编写；取消信号置位时中断 asyncio 任务并返回 None。

    Args:
        run: `run_case_authoring_modules(...)` 返回的协程。
        cancel_event: `threading.Event` 取消信号；None 表示不监听。

    Returns:
        工作流结果；被取消时返回 None。

    Raises:
        asyncio.CancelledError: 工作流自身被取消时由调用方接住。
    """
    if cancel_event is None:
        return await run
    job = asyncio.create_task(run)
    while not job.done():
        if cancel_event.is_set():
            job.cancel()
            try:
                await job
            except asyncio.CancelledError:
                return None
            return None
        await asyncio.sleep(0.2)
    return job.result()


def spawn_task_thread(task_id: int, agent_id: int) -> None:
    """启动 daemon 线程执行任务，并登记线程供取消兜底判断是否已退出。"""
    thread = threading.Thread(
        target=run_task_async,
        args=(task_id, agent_id),
        daemon=True,
        name=f"ai-task-{task_id}",
    )
    _workers[task_id] = thread
    thread.start()
