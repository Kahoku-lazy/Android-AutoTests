"""AI 任务后台线程：装配引擎、落进度与终态。

与 views_drf 解耦，供 api.dispatch_device / 提交入口共用。
"""

from __future__ import annotations

import logging
import threading

from django.conf import settings
from django.db import close_old_connections

from engines.ai.registry import get_ai_engine
from models.constants import TaskStatus

from . import api, engine_adapter
from .models import AIAgent, AITask

logger = logging.getLogger("ai_assistant")


def persist_task_progress_safe(task_id: int, payload: dict) -> None:
    """运行中增量写 result。必须可从 asyncio 事件循环线程安全调用。"""
    result_snapshot = api.dump_task_run_payload(payload)
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else None

    def _persist() -> None:
        close_old_connections()
        try:
            api.patch_task_progress(
                AITask.objects.get(id=task_id),
                result=result_snapshot,
                usage=usage,
            )
        except Exception:
            logger.exception("task progress persist failed id=%s", task_id)
        finally:
            close_old_connections()

    t = threading.Thread(target=_persist, daemon=True)
    t.start()
    t.join(timeout=30)
    if t.is_alive():
        logger.error("task progress persist timed out id=%s", task_id)


def run_task_async(task_id: int, agent_id: int) -> None:
    """后台线程入口：经引擎工厂执行并落终态（completed/failed + result + usage）。"""
    close_old_connections()

    def _on_progress(payload: dict) -> None:
        persist_task_progress_safe(task_id, payload)

    try:
        agent = AIAgent.objects.get(id=agent_id)
        task = AITask.objects.get(id=task_id)
        req = engine_adapter.build_request(task, agent)
        req.on_progress = _on_progress
        result = get_ai_engine(settings.AI_ENGINE).run(req)
        status = TaskStatus.COMPLETED if result.status == "success" else TaskStatus.FAILED
        payload = {
            "status": result.status,
            "summary": result.summary,
            "reason": result.reason,
            "completed": result.completed or [],
            "failed": result.failed or [],
            "plans": result.plans or [],
            "log": result.log or [],
            "usage": result.usage or {},
            "models": result.models
            or {role: getattr(spec, "model_name", "") for role, spec in (req.models or {}).items()},
            "max_loops": req.max_loops,
        }
        api.finalize_task(
            task,
            status=status,
            result=api.dump_task_run_payload(payload),
            usage=result.usage,
        )
    except Exception as exc:
        logger.exception("async task failed id=%s", task_id)
        try:
            api.finalize_task(
                AITask.objects.get(id=task_id), status=TaskStatus.FAILED, result=f"执行异常: {exc}"
            )
        except Exception:
            logger.exception("finalize async task failed id=%s", task_id)
    finally:
        close_old_connections()


def spawn_task_thread(task_id: int, agent_id: int) -> None:
    """启动 daemon 线程执行任务。"""
    threading.Thread(
        target=run_task_async,
        args=(task_id, agent_id),
        daemon=True,
        name=f"ai-task-{task_id}",
    ).start()
