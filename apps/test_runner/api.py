"""test-runner public API."""

import asyncio
import json
import logging

from apps.case_manager.models import TestDefinition
from apps.device_pool.models import Device as PoolDevice
from models.step_types import CaseType, TestStep
from models.test_models import TestCaseDef

from .models import TaskCard, TestResult, TestRunRecord
from .runner import get_active_runs_info, stop_run

_log = logging.getLogger("test_runner.api")

# Daphne 主循环引用 —— 供 AI 工具（run_test）从 worker 线程投递 async 执行回主循环。
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """缓存 Daphne 主循环（bootstrap，供跨线程投递）。由 AI 助手 chat 流写入。"""
    global _main_loop
    _main_loop = loop


__all__ = [
    "delete_task_card",
    "get_active_runs_info",
    "get_run_results",
    "resolve_creator",
    "save_task_card",
    "set_main_loop",
    "start_run",
    "stop_run",
]


def resolve_creator(creator) -> str:
    """Convert numeric Django user ID to username; real usernames pass through.

    Historical bug: frontend stored JWT ``sub`` (user id) as creator.
    """
    if not creator:
        return ""
    s = str(creator).strip()
    if not s.isdigit():
        return s
    try:
        from django.contrib.auth.models import User

        return User.objects.get(id=int(s)).username
    except Exception:
        return s


# ── Query helpers ──


def get_run_results(run_id: str) -> list[dict]:
    """获取某次执行的所有测试结果。返回 dict 列表，不返回 ORM 对象。"""
    return [
        dict(row)
        for row in TestResult.objects.filter(run__run_id=run_id)
        .order_by("created_at")
        .values(
            "id",
            "case_id",
            "case_type",
            "iteration",
            "result",
            "duration_ms",
            "detail",
            "step_details",
            "created_at",
        )
    ]


# ── TaskCard write helpers ──


def save_task_card(task_data: dict) -> dict:
    """Create or update a TaskCard. Returns dict with task_id.

    Args:
        task_data: Dict with task card fields (uses frontend camelCase keys).

    Returns:
        dict: {"id": task_id}

    Raises:
        ValueError: if task_id is missing or empty.
    """
    task_id = (task_data.get("id") or "").strip()
    if not task_id:
        raise ValueError("task_id is required")

    creator = resolve_creator(task_data.get("creator", ""))
    defaults = {
        "name": task_data.get("name", ""),
        "creator": creator,
        "mode": task_data.get("mode", "immediate"),
        "task_type": task_data.get("taskType", "ui_automation"),
        "device_serial": task_data.get("deviceSerial", ""),
        "case_ids": task_data.get("caseIds", []),
        "loop_count": task_data.get("loopCount", 1),
        "interval_seconds": task_data.get("intervalSeconds", 5),
        "case_items": task_data.get("caseItems", []),
        "step_states": task_data.get("stepStates", []),
        "overall_pass": task_data.get("overallPass", 0),
        "overall_fail": task_data.get("overallFail", 0),
        "logs": (task_data.get("logs") or [])[-200:],
        "outcome": task_data.get("outcome", ""),
        "round": task_data.get("round", 0),
        "conclusion": task_data.get("conclusion", ""),
        "bug_ticket": task_data.get("bugTicket", ""),
        "failed_steps": (task_data.get("failedSteps") or [])[-200:],
        "current_case_title": task_data.get("currentCaseTitle", ""),
        "current_iteration": int(task_data.get("currentIteration") or 0),
        "start_at": task_data.get("startAt") or "",
        "end_at": task_data.get("endAt") or "",
    }

    try:
        task = TaskCard.objects.get(task_id=task_id)
        # ── Protect state-machine-managed fields from frontend auto-save ──
        # When the backend has set status to "done" or "running", the
        # frontend's 3-second auto-save must not overwrite these fields
        # with stale in-memory values.
        _sm_managed = task.status in ("done", "running")
        for k, v in defaults.items():
            if _sm_managed and k in (
                "status",
                "outcome",
                "case_items",
                "overall_pass",
                "overall_fail",
            ):
                continue
            setattr(task, k, v)
        # running flag: only set by state machine, never by frontend save
        if not _sm_managed:
            task.running = task_data.get("running", False)
        task.save()
    except TaskCard.DoesNotExist:
        task = TaskCard(
            task_id=task_id,
            name=task_data.get("name", ""),
            creator=creator,
            mode=task_data.get("mode", "immediate"),
            task_type=task_data.get("taskType", "ui_automation"),
            device_serial=task_data.get("deviceSerial", ""),
            case_ids=task_data.get("caseIds", []),
            loop_count=task_data.get("loopCount", 1),
            interval_seconds=task_data.get("intervalSeconds", 5),
            running=False,
            case_items=task_data.get("caseItems", []),
            step_states=task_data.get("stepStates", []),
            overall_pass=task_data.get("overallPass", 0),
            overall_fail=task_data.get("overallFail", 0),
            logs=(task_data.get("logs") or [])[-200:],
            outcome=task_data.get("outcome", ""),
            round=task_data.get("round", 0),
            conclusion=task_data.get("conclusion", ""),
            bug_ticket=task_data.get("bugTicket", ""),
            failed_steps=(task_data.get("failedSteps") or [])[-200:],
            current_case_title=task_data.get("currentCaseTitle", ""),
            current_iteration=int(task_data.get("currentIteration") or 0),
            start_at=task_data.get("startAt") or "",
            end_at=task_data.get("endAt") or "",
            status="idle",
        )
        task.save()

    return {"id": task_id}


def delete_task_card(task_id: str) -> None:
    """Delete a TaskCard by task_id. No-op if not found."""
    TaskCard.objects.filter(task_id=task_id).delete()


def _resolve_loop() -> asyncio.AbstractEventLoop | None:
    """获取 Daphne 主循环：优先缓存引用，兜底 get_event_loop（worker 线程可能抛 RuntimeError）。"""
    if _main_loop is not None and _main_loop.is_running():
        return _main_loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop
    except RuntimeError:
        pass
    return None


def start_run(
    run_id: str,
    serial: str,
    case_ids: list,
    user_id: str = "",
    loop_count: int = 1,
    interval_seconds: int = 5,
    package_name: str = "",
) -> dict:
    """启动一次 UI 测试执行（投递到 Daphne 主循环后台执行，立即返回）。

    供 AI 助手的 run_test 工具调用。返回 {"status": True/False, ...}。
    """
    if not run_id or not serial or not case_ids:
        return {"status": False, "message": "run_id/serial/case_ids 不能为空"}

    if TestRunRecord.objects.filter(run_id=run_id).exists():
        return {"status": False, "message": f"run_id 已存在: {run_id}"}

    # ── 加载 UI 用例定义（同步 ORM）──
    rows = TestDefinition.objects.filter(id__in=case_ids, enabled=True)
    test_cases: list[TestCaseDef] = []
    for r in rows:
        try:
            steps_raw = json.loads(r.steps_json or "[]")
        except (json.JSONDecodeError, TypeError):
            steps_raw = []
        steps_data = [TestStep.from_dict(s) for s in steps_raw]
        test_cases.append(
            TestCaseDef(
                id=r.id,
                title=r.title,
                category=r.category,
                description=r.description,
                steps=getattr(r, "steps", ""),
                enabled=r.enabled,
                steps_data=steps_data,
                is_json=True,
                package_name=getattr(r, "package_name", "") or package_name,
                created_at=str(r.created_at) if hasattr(r, "created_at") else "",
                updated_at=str(r.updated_at) if hasattr(r, "updated_at") else "",
                task_type=CaseType.UI_AUTOMATION.value,
            )
        )
    if not test_cases:
        return {"status": False, "message": "no enabled test cases found"}

    # ── 设备轻校验 ──
    dev = PoolDevice.objects.filter(serial=serial).first()
    if dev is None:
        return {"status": False, "message": "设备未注册"}
    if dev.status in ("OFFLINE", "DISCONNECTED"):
        return {"status": False, "message": "设备离线"}

    # ── 投递到 Daphne 主循环 ──
    loop = _resolve_loop()
    if loop is None:
        return {"status": False, "message": "主事件循环不可用，无法投递测试任务"}

    from .views.ai_execution import _run_ui_for_ai

    coro = _run_ui_for_ai(
        run_id, test_cases, loop_count, interval_seconds, package_name, serial, user_id
    )
    future = asyncio.run_coroutine_threadsafe(coro, loop)

    def _on_done(f):
        if not f.cancelled():
            exc = f.exception()
            if exc is not None:
                _log.error("AI run dispatch %s failed: %s", run_id, exc)

    future.add_done_callback(_on_done)

    return {"status": True, "run_id": run_id, "serial": serial, "case_count": len(test_cases)}
