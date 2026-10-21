"""AI 任务后台线程：装配引擎、落进度与终态。

与 views_drf 解耦，供 api.dispatch_device / 提交入口共用。
"""

from __future__ import annotations

import threading

from pathlib import Path

from django.db import close_old_connections

from backend.apps.ai_assistant.models import AIAgent
from backend.models.constants import TaskStatus
from utils.logs import backend_log

from . import api, engine_adapter
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
        agent = AIAgent.objects.get(id=agent_id)
        task = Task.objects.get(id=task_id)
        executor_model, verifier_model = engine_adapter.sop_role_models(agent)
        yaml_path, ephemeral = api.materialize_config_file(task)
        bind_cancel(task_id)
        sink = TaskEventSink()
        sink_token = bind_sink(sink)
        run_token = bind_run_context(task_id, agent_id, task.case_title or "")
        result = run_platform_sop(
            yaml_path,
            api.build_sop_run_input(task),
            executor_model=executor_model,
            verifier_model=verifier_model,
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


def spawn_task_thread(task_id: int, agent_id: int) -> None:
    """启动 daemon 线程执行任务。"""
    threading.Thread(
        target=run_task_async,
        args=(task_id, agent_id),
        daemon=True,
        name=f"ai-task-{task_id}",
    ).start()
