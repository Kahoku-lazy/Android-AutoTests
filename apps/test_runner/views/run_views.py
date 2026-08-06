"""Run management endpoints — stop / cancel / list / status."""

import json

from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .. import state_machine as sm
from ..models import TaskCard, TestResult, TestRunRecord
from ..runner import (
    _active_runs,
    get_active_run,
    is_device_busy,
    list_active_runs,
    stop_run,
)
from .helpers import (
    _bg_log,
    _device_queue,
    _enqueue,
    _preflight_runs,
    _queue_size,
    _run_client_task,
    require_auth,
)


@require_auth
@csrf_exempt
def stop_test_run(request, run_id):
    """POST /api/runner/run/{run_id}/stop."""
    # 活跃 run:走优雅停止(设置 is_running=False,执行循环到检查点自然收尾)
    if stop_run(run_id):
        return JsonResponse({"status": True, "message": "stop requested"})
    # 预检阶段(锁了手机但还没真正执行):打停止标记,
    # delayed_execute 会在预检检查点释放设备 + 标记停止,避免设备锁泄漏
    pf = _preflight_runs.get(run_id)
    if pf is not None:
        pf["stopped"] = True
        return JsonResponse({"status": True, "message": "stopping (pre-flight)"})
    return JsonResponse({"status": False, "message": "run not found or already finished"})


@require_auth
@csrf_exempt
def cancel_queued_task(request):
    """POST /api/runner/queue/cancel — Remove a queued task from the device queue."""
    data = json.loads(request.body) if request.body else {}
    client_task_id = data.get("client_task_id", "").strip()
    serial = data.get("device_serial", "").strip()

    if not client_task_id or not serial:
        return JsonResponse(
            {
                "status": False,
                "message": "需要提供 client_task_id 和 device_serial",
            },
            status=400,
        )

    q = _device_queue.get(serial, [])
    removed = None
    new_q = []
    for item in q:
        if item.get("client_task_id") == client_task_id:
            removed = item
        else:
            new_q.append(item)

    if removed is not None:
        _device_queue[serial] = new_q
        if not new_q:
            del _device_queue[serial]
        # Reset TaskCard status so it can be re-executed — via state machine.
        try:
            tc = TaskCard.objects.get(task_id=client_task_id)
            sm.cancel(tc)
        except TaskCard.DoesNotExist:
            pass
        except sm.InvalidTransition as e:
            _bg_log.warning("cancel transition %s: %s", client_task_id, e)
        return JsonResponse(
            {
                "status": True,
                "message": f"已取消排队任务（{len(removed.get('case_ids', []))} 个用例）",
            }
        )

    # Fallback: task may be queued in DB but not in memory (e.g. after server restart)
    try:
        tc = TaskCard.objects.get(task_id=client_task_id, status="queued", device_serial=serial)
        sm.cancel(tc)
        return JsonResponse(
            {
                "status": True,
                "message": f"已从数据库中取消排队任务",
            }
        )
    except TaskCard.DoesNotExist:
        pass

    return JsonResponse(
        {
            "status": False,
            "message": "未找到该排队任务，可能已经开始执行",
        },
        status=404,
    )


@require_auth
def list_active(request):
    """GET /api/runner/active — List currently active runs.

    Also triggers lazy recovery: rebuild queues, mark orphan running tasks.
    """
    from ..recovery_helpers import queue_payload_from_taskcard, recover_stale_running_taskcards
    from .execution import _start_next_queued

    recover_stale_running_taskcards()

    # Lazy queue recovery: rebuild from DB and/or kick stalled in-memory queues
    active_runs_empty = not list_active_runs
    if active_runs_empty:
        import asyncio as _asyncio

        devices_to_start: set[str] = set()

        db_queued = TaskCard.objects.filter(status="queued").order_by("created_at")
        for tc in db_queued:
            serial = tc.device_serial
            if not serial:
                continue
            existing = _device_queue.get(serial, [])
            already_enqueued = any(item.get("client_task_id") == tc.task_id for item in existing)
            if not already_enqueued:
                _enqueue(serial, queue_payload_from_taskcard(tc))
            devices_to_start.add(serial)

        for serial, q in _device_queue.items():
            if q:
                devices_to_start.add(serial)

        for serial in devices_to_start:
            if not is_device_busy(serial) and _queue_size(serial) > 0:
                try:
                    _loop = _asyncio.get_event_loop()
                    if _loop.is_running():
                        _asyncio.run_coroutine_threadsafe(_start_next_queued(serial), _loop)
                except RuntimeError:
                    pass

    active = []
    for run_id, state in _active_runs.items():
        if state.is_running:
            active.append(
                {
                    "run_id": run_id,
                    "status": state.run_model.status.value,
                    "selected_cases": state.run_model.selected_cases,
                    "loop_count": state.run_model.loop_count,
                    "started_at": state.run_model.started_at,
                    "device_serial": state.run_model.device_serial,
                    "client_task_id": _run_client_task.get(run_id, ""),
                }
            )
    return JsonResponse({"status": True, "active": active})


def test_run_status(request, run_id):
    """GET /api/runner/run/{run_id}/status."""
    state = get_active_run(run_id)
    if state:
        return JsonResponse(
            {
                "status": True,
                "run_id": run_id,
                "status": state.run_model.status.value,
                "is_running": state.is_running,
                "selected_cases": state.run_model.selected_cases,
                "loop_count": state.run_model.loop_count,
                "started_at": state.run_model.started_at,
            }
        )

    # Fallback: look up completed run from DB
    try:
        run_record = TestRunRecord.objects.get(run_id=run_id)
        results = TestResult.objects.filter(run=run_record)
        agg = results.aggregate(
            total=Count("id"),
            passed=Count("id", filter=Q(result="pass")),
        )
        return JsonResponse(
            {
                "status": True,
                "run_id": run_id,
                "status": run_record.status,
                "total_iterations": agg["total"],
                "passed": agg["passed"],
                "selected_cases": run_record.selected_cases,
                "loop_count": run_record.loop_count,
                "started_at": run_record.started_at,
            }
        )
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"status": False, "message": "run not found"}, status=404)


def list_test_runs(request):
    """GET /api/runner/runs — List run history."""
    rows = TestRunRecord.objects.annotate(
        total=Count("results"),
        passed=Count("results", filter=Q(results__result="pass")),
    ).order_by("-id")[:50]
    return JsonResponse(
        {
            "status": True,
            "runs": [
                {
                    "run_id": r.run_id,
                    "status": r.status,
                    "device_serial": r.device_serial,
                    "loop_count": r.loop_count,
                    "total": r.total,
                    "passed": r.passed,
                    "failed": r.total - r.passed,
                    "started_at": r.started_at,
                    "finished_at": r.finished_at,
                    "selected_cases": r.selected_cases,
                }
                for r in rows
            ],
        }
    )
