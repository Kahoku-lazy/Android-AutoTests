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
    try:
        task = Task.objects.get(id=task_id)
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
        )
    except Exception as exc:
        backend_log.exception("async task failed id=%s", task_id)
        try:
            api.finalize_task(
                Task.objects.get(id=task_id), status=TaskStatus.FAILED, result=f"执行异常: {exc}"
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
        close_old_connections()


def _run_case_authoring(task: Task, cancel_event=None) -> dict:
    """跑一次模块化家电测试用例编写，返回可写入 Task.result 的结果字典。

    Args:
        task: 用例编写任务。
        cancel_event: 任务的取消信号；已置位时不再开跑。

    Returns:
        status / summary / phase / passed / document / verdicts / modules / reason。
    """
    from engines.agents.workflow.case_authoring_workflow import run_case_authoring_modules

    if cancel_event is not None and cancel_event.is_set():
        return _case_failed("用户关闭", status="cancelled")
    requirement = api.build_case_requirement(task)
    if not requirement.strip():
        return _case_failed("任务没有可解析的需求文档")

    try:
        result = asyncio.run(
            _await_case_run(
                run_case_authoring_modules(
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
    modules = [
        {
            "key": module.key,
            "name": module.name,
            "start_line": module.start_line,
            "end_line": module.end_line,
            "passed": module.passed,
            "truncated": module.truncated,
            "document_length": module.document_length,
            "message": module.message,
        }
        for module in result.modules
    ]
    passed = bool(result.passed)
    reason = ""
    if not passed and verdicts:
        reason = str(verdicts[-1].get("message") or "")
    if result.truncated and not reason:
        reason = "输出超过单次上限且无法继续拆分（OUTPUT_TRUNCATED）"
    case_import = (
        _import_case_document(task, result.document)
        if passed and result.document
        else _skipped_import("验收未通过或文档为空，未写入用例库")
    )
    module_count = len(modules) or 1
    return {
        "status": "success" if passed else "fail",
        "summary": (
            f"测试用例已生成并通过验收（{module_count} 个模块）"
            if passed
            else f"测试用例验收未通过（{module_count} 个模块）"
        ),
        "phase": result.phase,
        "passed": passed,
        "truncated": result.truncated,
        "max_output_tokens": result.max_output_tokens,
        "document": result.document,
        "verdicts": verdicts,
        "modules": modules,
        "case_import": case_import,
        "reason": reason,
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


def _import_case_document(task: Task, document: str) -> dict:
    """把验收通过的 Markdown 文档解析并写入用例库；失败只降级为结果字段。"""
    from backend.apps.case_manager.api import import_case_rows
    from engines.agents.workflow.case_document_check import case_step_pairs, parse_case_document

    owner = str(task.created_by or getattr(task.agent, "owner_id", "") or "")
    if not owner:
        return _skipped_import("任务缺少发起人，未写入用例库")
    try:
        parsed = parse_case_document(document)
        rows = [
            {
                "source_case_id": case.case_id,
                "title": case.fields.get("测试标题", ""),
                "priority": case.priority,
                "module": case.module,
                "precondition": case.fields.get("前置条件", ""),
                "steps": [
                    {"action": action, "assertion": assertion}
                    for action, assertion in case_step_pairs(case)
                ],
            }
            for case in parsed.cases
        ]
        return import_case_rows(
            user_id=owner,
            task_id=task.id,
            task_title=task.title or "",
            rows=rows,
        )
    except Exception as exc:  # noqa: BLE001 - 导入失败不能改变任务验收结论
        backend_log.exception("import case authoring result failed task=%s", task.id)
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
        "truncated": False,
        "max_output_tokens": 0,
        "document": "",
        "verdicts": [],
        "modules": [],
        "case_import": _skipped_import(reason),
        "reason": reason,
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
    """启动 daemon 线程执行任务。"""
    threading.Thread(
        target=run_task_async,
        args=(task_id, agent_id),
        daemon=True,
        name=f"ai-task-{task_id}",
    ).start()
