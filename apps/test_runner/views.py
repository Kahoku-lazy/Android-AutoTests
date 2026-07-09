"""test-runner HTTP routes — 10 endpoints under /api/runner/*."""

import json
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from asgiref.sync import sync_to_async

from models.step_types import TestStep
from models.test_models import TestCaseDef
from .runner import (
    TestRunner,
    get_active_run,
    stop_run,
    is_device_busy,
    mark_device_busy,
    mark_device_idle,
)
from .runner import _active_runs as list_active_runs
from .runner import _u2_executor
from .callbacks import test_callbacks
from .models import TestResult, TestRunRecord, TaskCard
from apps.device_pool.api import device
from apps.device_pool.api import acquire_device as dp_acquire_device
from apps.device_pool.api import release_device as dp_release_device
from ..device_pool.models import Device as PoolDevice
from ..case_manager.models import TestDefinition


def require_auth(view_func):
    """Decorator: enforce JWT authentication. Returns 401 if no valid token.
    Supports both sync and async view functions."""
    from functools import wraps
    import inspect

    if inspect.iscoroutinefunction(view_func):

        @wraps(view_func)
        async def async_wrapper(request, *args, **kwargs):
            user_id = getattr(request, "user_id", None)
            if not user_id:
                return JsonResponse({"ok": False, "error": "未登录或 token 已过期"}, status=401)
            return await view_func(request, *args, **kwargs)

        return async_wrapper
    else:

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = getattr(request, "user_id", None)
            if not user_id:
                return JsonResponse({"ok": False, "error": "未登录或 token 已过期"}, status=401)
            return view_func(request, *args, **kwargs)

        return wrapper


# Per-device task queue: serial → [request_payload]
_device_queue: dict[str, list] = {}

# Maps run_id → client_task_id so the frontend can discover queued-task execution
_run_client_task: dict[str, str] = {}


def _enqueue(serial: str, payload: dict):
    """Add a test request to the device's queue."""
    _device_queue.setdefault(serial, []).append(payload)


def _dequeue(serial: str) -> dict | None:
    """Pop the next queued request for a device."""
    q = _device_queue.get(serial)
    if q:
        return q.pop(0)
    return None


def _queue_size(serial: str) -> int:
    """Number of tasks waiting for a device."""
    return len(_device_queue.get(serial, []))


def _schedule_next_queued(serial: str):
    """Fire-and-forget: start the next queued task for a device."""
    if serial:
        asyncio.create_task(_start_next_queued(serial))


@require_auth
async def start_test_run(request):
    """POST /api/runner/run — Start async test execution (multi-device + schedule)."""
    data = json.loads(request.body)
    case_ids = data.get("case_ids", [])
    loop_count = data.get("loop_count", 3)
    interval_seconds = max(5, int(data.get("interval_seconds", 5)))
    package_name = data.get("package_name", "")
    start_at = data.get("start_at")  # ISO str or None
    end_at = data.get("end_at")  # ISO str or None
    client_task_id = data.get("client_task_id", "")  # frontend localStorage task id

    # Normalize device list
    serials = data.get("device_serials", [])
    if not serials and data.get("device_serial", "").strip():
        serials = [data["device_serial"].strip()]
    if not serials:
        serials = [device.current_serial]

    if not case_ids:
        return JsonResponse({"ok": False, "error": "case_ids required"})

    @sync_to_async
    def load_definitions():
        rows = TestDefinition.objects.filter(id__in=case_ids, enabled=True)
        test_cases = []
        for r in rows:
            try:
                steps_raw = json.loads(r.steps_json or "[]")
            except Exception:
                steps_raw = []
            steps_data = [TestStep.from_dict(s) for s in steps_raw]
            tc = TestCaseDef(
                id=r.id,
                title=r.title,
                category=r.category,
                description=r.description,
                steps=r.steps,
                enabled=r.enabled,
                steps_data=steps_data,
                is_json=True,
                package_name=r.package_name or package_name,
                created_at=str(r.created_at),
                updated_at=str(r.updated_at),
            )
            test_cases.append(tc)
        return test_cases

    test_cases = await load_definitions()
    if not test_cases:
        return JsonResponse({"ok": False, "error": "no enabled test cases found"})

    effective_pkg = package_name
    if not effective_pkg and test_cases:
        effective_pkg = test_cases[0].package_name or ""

    queued_serials = []
    run_ids = []
    for serial in serials:
        # Validate device
        try:
            dev = await sync_to_async(PoolDevice.objects.get)(serial=serial)
        except PoolDevice.DoesNotExist:
            continue
        if dev.status in ("OFFLINE", "DISCONNECTED"):
            continue

        # Check if device is already executing — cross-process + same-process
        dev_busy_db = dev.status == "BUSY"
        if is_device_busy(serial) or dev_busy_db:
            _enqueue(
                serial,
                {
                    "case_ids": case_ids,
                    "loop_count": loop_count,
                    "interval_seconds": interval_seconds,
                    "package_name": effective_pkg,
                    "start_at": start_at,
                    "end_at": end_at,
                    "client_task_id": client_task_id,
                },
            )
            # Mark TaskCard as queued so it can be recovered on restart
            if client_task_id:
                await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
                    status="queued", running=False
                )
            await test_callbacks.on_log(
                f"queue_{serial}",
                f"⏳ 设备 {serial} 正忙，任务已加入队列（前面有 {_queue_size(serial)} 个任务）",
            )
            queued_serials.append(serial)
            continue

        # Claim device — DB-level first (source of truth), then memory-level
        try:
            await sync_to_async(dp_acquire_device)(serial, user_id=f"runner-{serial}", timeout=3600)
        except ValueError as e:
            # Device occupied by another process — enqueue
            _enqueue(
                serial,
                {
                    "case_ids": case_ids,
                    "loop_count": loop_count,
                    "interval_seconds": interval_seconds,
                    "package_name": effective_pkg,
                    "start_at": start_at,
                    "end_at": end_at,
                    "client_task_id": client_task_id,
                },
            )
            if client_task_id:
                await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
                    status="queued", running=False
                )
            await test_callbacks.on_log(f"queue_{serial}", f"⏳ 设备 {serial} {e}，任务已加入队列")
            queued_serials.append(serial)
            continue
        mark_device_busy(serial)
        if client_task_id:
            await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
                status="running", running=True
            )

        # Create independent u2 connection per device
        def make_connection(s=serial):
            import uiautomator2 as u2

            return u2.connect(s)

        try:
            d = await asyncio.get_event_loop().run_in_executor(_u2_executor, make_connection)
        except Exception as e:
            mark_device_idle(serial)
            await sync_to_async(dp_release_device)(serial, reason="manual")
            if client_task_id:
                await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
                    status="idle", running=False
                )
            _schedule_next_queued(serial)
            await test_callbacks.on_log(f"queue_{serial}", f"❌ 设备 {serial} 连接失败: {e}")
            continue

        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if client_task_id:
            _run_client_task[run_id] = client_task_id
        runner = TestRunner(d, effective_pkg, callback=test_callbacks)

        # Capture serial in default arg to avoid closure-over-loop-variable bug
        async def delayed_execute(rid, r, tcs, lc, interval, st, et, _serial=serial):
            if st:
                try:
                    target = datetime.fromisoformat(st)
                    delay = (target - datetime.now()).total_seconds()
                    if delay > 0:
                        await test_callbacks.on_log(rid, f"⏰ 计划 {delay:.0f}s 后开始执行")
                        await asyncio.sleep(delay)
                except Exception:
                    pass
            if et:

                async def auto_stop():
                    try:
                        target = datetime.fromisoformat(et)
                        delay = (target - datetime.now()).total_seconds()
                        if delay > 0:
                            await asyncio.sleep(delay)
                            stop_run(rid)
                            await test_callbacks.on_log(rid, "⏰ 到达结束时间，自动停止")
                    except Exception:
                        pass

                asyncio.create_task(auto_stop())
            await _execute_tests(rid, r, tcs, lc, interval, _serial)

        asyncio.create_task(
            delayed_execute(
                run_id, runner, test_cases, loop_count, interval_seconds, start_at, end_at
            )
        )
        run_ids.append({"run_id": run_id, "serial": serial})

    if not run_ids and not queued_serials:
        return JsonResponse(
            {
                "ok": False,
                "error": "没有可用设备，请确认设备已连接且状态为在线",
            },
            status=400,
        )

    return JsonResponse(
        {
            "ok": True,
            "runs": run_ids,
            "queued": queued_serials,
            "case_count": len(test_cases),
            "loop_count": loop_count,
            "parallel": len(run_ids),
        }
    )


async def _execute_tests(
    run_id: str,
    runner,
    test_cases: list,
    loop_count: int,
    interval_seconds: int = 5,
    serial: str = "",
):
    run_record = None
    run_completed = False
    effective_serial = serial or (getattr(runner.device, "serial", None) or "")
    try:
        # Persist run record with case snapshot before execution
        @sync_to_async
        def create_run_record():
            snapshots = []
            for tc in test_cases:
                snapshots.append(
                    {
                        "case_id": tc.id,
                        "title": tc.title,
                        "steps_data": [
                            s.to_dict()
                            if hasattr(s, "to_dict")
                            else (s.__dict__ if hasattr(s, "__dict__") else str(s))
                            for s in (tc.steps_data or [])
                        ],
                    }
                )
            ctid = _run_client_task.get(run_id, "")
            return TestRunRecord.objects.create(
                run_id=run_id,
                client_task_id=ctid,
                status="RUNNING",
                device_serial=serial
                or (runner.device.serial if hasattr(runner.device, "serial") else ""),
                selected_cases=snapshots,
                loop_count=loop_count,
                started_at=datetime.now().isoformat(),
            )

        run_record = await create_run_record()

        # 链接 TaskCard 到 TestRunRecord，供前端页面刷新后重连 WebSocket
        client_tid = _run_client_task.get(run_id, "")
        if client_tid:
            await sync_to_async(TaskCard.objects.filter(task_id=client_tid).update)(
                run_id=run_record.id
            )

        # Log device info
        dev_serial = serial or runner.device.serial if hasattr(runner.device, "serial") else "?"
        await test_callbacks.on_log(run_id, f"📱 设备: {dev_serial}")
        try:
            d_info = runner.device.info
            await test_callbacks.on_log(
                run_id,
                f"分辨率: {d_info.get('displayWidth', '?')}x{d_info.get('displayHeight', '?')}",
            )
        except Exception:
            pass
        await test_callbacks.on_log(run_id, f"循环次数: {loop_count}")
        for tc in test_cases:
            step_count = len(tc.steps_data) if tc.steps_data else 0
            await test_callbacks.on_log(run_id, f"用例: [{tc.id}] {tc.title} ({step_count} 步)")
        await test_callbacks.on_log(run_id, "────────────────────")

        run_model = await runner.run(run_id, test_cases, loop_count, interval_seconds)
        run_completed = True
        # Device is free — schedule next queued task before slow DB writes
        _schedule_next_queued(effective_serial)

        @sync_to_async
        def persist():
            results = [
                TestResult(
                    run=run_record,
                    case_id=r.case_id,
                    iteration=r.iteration,
                    result=r.result,
                    duration_ms=r.duration_ms,
                    detail=r.detail,
                )
                for r in run_model.case_results
            ]
            if results:
                TestResult.objects.bulk_create(results)

        await persist()

        # Update run record with final status
        @sync_to_async
        def finalize_run():
            run_record.status = run_model.status.value
            run_record.summary = run_model.summary
            run_record.finished_at = datetime.now().isoformat()
            run_record.save(update_fields=["status", "summary", "finished_at"])

        await finalize_run()

        # Mark TaskCard as done with full execution results
        client_tid = _run_client_task.get(run_id, "")
        if client_tid:

            @sync_to_async
            def _mark_done():
                # Build case_items from run results — single pass
                case_items = []
                by_case = {}
                overall_pass = 0
                overall_fail = 0
                for r in run_model.case_results:
                    if r.case_id not in by_case:
                        by_case[r.case_id] = {"pass": 0, "fail": 0, "total": 0}
                    by_case[r.case_id]["total"] += 1
                    if r.result == "pass":
                        by_case[r.case_id]["pass"] += 1
                        overall_pass += 1
                    elif r.result in ("fail", "stopped"):
                        by_case[r.case_id]["fail"] += 1
                        overall_fail += 1
                for cid, counts in by_case.items():
                    # Try to get title from selected_cases snapshot
                    title = cid
                    for sc in run_record.selected_cases or []:
                        if sc.get("case_id") == cid:
                            title = sc.get("title", cid)
                            break
                    case_items.append(
                        {
                            "id": cid,
                            "title": title,
                            "total": counts["total"],
                            "pass": counts["pass"],
                            "fail": counts["fail"],
                            "rate": round(counts["pass"] / counts["total"] * 100)
                            if counts["total"]
                            else 0,
                            "status": "done",
                        }
                    )
                # Determine outcome based on actual run status (not hardcoded 'completed')
                final_outcome = "completed" if run_model.status.value == "completed" else "stopped"
                TaskCard.objects.filter(task_id=client_tid).update(
                    status="done",
                    running=False,
                    outcome=final_outcome,
                    case_items=case_items,
                    overall_pass=overall_pass,
                    overall_fail=overall_fail,
                )

            await _mark_done()

    except Exception as e:
        print(f"Test run {run_id} error: {e}")
        await test_callbacks.on_device_error(run_id, str(e))
        # Mark run record as failed if it was created
        if run_record:

            @sync_to_async
            def mark_failed():
                run_record.status = "FAILED"
                run_record.finished_at = datetime.now().isoformat()
                run_record.save(update_fields=["status", "finished_at"])

            try:
                await mark_failed()
            except Exception as e:
                print(f"[views] mark_failed({run_id}) failed: {e}")
        # Update TaskCard to reflect error so frontend doesn't hang forever
        client_tid = _run_client_task.get(run_id, "")
        if client_tid:

            @sync_to_async
            def _mark_error():
                TaskCard.objects.filter(task_id=client_tid).update(
                    status="done",
                    running=False,
                    outcome="error",
                )

            try:
                await _mark_error()
            except Exception as e:
                print(f"[views] _mark_error({run_id}, {client_tid}) failed: {e}")
    finally:
        # runner.run() also calls mark_device_idle in its own finally;
        # discard is idempotent. Only schedule dequeue if run never started.
        mark_device_idle(effective_serial)
        # Release DB-level device occupation
        try:
            await sync_to_async(dp_release_device)(effective_serial, reason="manual")
        except Exception as e:
            print(f"[views] dp_release_device({effective_serial}) in finally failed: {e}")
        if not run_completed:
            _schedule_next_queued(effective_serial)


async def _start_next_queued(serial: str):
    """Dequeue and start the next waiting task for a device.

    Called from _execute_tests.finally after a run finishes.
    Must be atomic: mark busy → dequeue → start, to prevent races.
    """
    if not serial:
        return

    # Atomic: claim the device before anything else
    # If somehow already busy again (e.g. direct request beat us), abort
    if is_device_busy(serial):
        return

    next_req = _dequeue(serial)
    if not next_req:
        return  # No queued tasks, device stays idle

    # Mark busy NOW to prevent _start_next_queued or direct requests from racing
    mark_device_busy(serial)
    # DB-level acquire — cross-process protection
    try:
        await sync_to_async(dp_acquire_device)(serial, user_id=f"runner-{serial}", timeout=3600)
    except ValueError as e:
        mark_device_idle(serial)
        await test_callbacks.on_log(
            f"queue_{serial}",
            f"❌ 设备 {serial} 已被占用: {e}（剩余 {_queue_size(serial)} 个排队）",
        )
        _schedule_next_queued(serial)
        return
    # Update TaskCard status to 'running' so it's not re-queued on restart
    client_task_id = next_req.get("client_task_id", "")
    if client_task_id:
        await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
            status="running", running=True
        )

    await test_callbacks.on_log(
        f"queue_{serial}",
        f"📤 设备 {serial} 空闲，从队列取出任务开始执行（剩余 {_queue_size(serial)} 个排队）",
    )

    executed = False  # tracks whether _execute_tests was reached
    try:
        # Load test cases
        @sync_to_async
        def load():
            rows = TestDefinition.objects.filter(id__in=next_req["case_ids"], enabled=True)
            tcs = []
            for r in rows:
                try:
                    steps_raw = json.loads(r.steps_json or "[]")
                except Exception:
                    steps_raw = []
                steps_data = [TestStep.from_dict(s) for s in steps_raw]
                tcs.append(
                    TestCaseDef(
                        id=r.id,
                        title=r.title,
                        category=r.category,
                        description=r.description,
                        steps=r.steps,
                        enabled=r.enabled,
                        steps_data=steps_data,
                        is_json=True,
                        package_name=r.package_name or next_req.get("package_name", ""),
                        created_at=str(r.created_at),
                        updated_at=str(r.updated_at),
                    )
                )
            return tcs

        test_cases = await load()
        if not test_cases:
            mark_device_idle(serial)
            return

        # Create u2 connection and runner
        def make_connection():
            import uiautomator2 as u2

            return u2.connect(serial)

        d = await asyncio.get_event_loop().run_in_executor(_u2_executor, make_connection)
        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        client_task_id = next_req.get("client_task_id", "")
        if client_task_id:
            _run_client_task[run_id] = client_task_id
        runner = TestRunner(d, next_req.get("package_name", ""), callback=test_callbacks)
        executed = True
        # _execute_tests.finally handles cleanup + schedules next dequeue
        await _execute_tests(
            run_id,
            runner,
            test_cases,
            next_req.get("loop_count", 3),
            next_req.get("interval_seconds", 5),
            serial,
        )
    except Exception as e:
        print(f"[queue] Failed to start queued task on {serial}: {e}")
        await test_callbacks.on_log(
            f"queue_{serial}", f"❌ 队列任务启动失败: {e}（剩余 {_queue_size(serial)} 个排队）"
        )
        mark_device_idle(serial)
        try:
            await sync_to_async(dp_release_device)(serial, reason="manual")
        except Exception as release_err:
            print(f"[views] dp_release_device({serial}) in queue handler failed: {release_err}")
        if not executed:
            # Exception happened before _execute_tests was reached
            # (e.g. load() or u2.connect() failed). Retry next queued task.
            _schedule_next_queued(serial)
        # else: _execute_tests already scheduled the next dequeue


@require_auth
@csrf_exempt
def stop_test_run(request, run_id):
    """POST /api/runner/run/{run_id}/stop."""
    if stop_run(run_id):
        return JsonResponse({"ok": True, "message": "stop requested"})
    return JsonResponse({"ok": False, "error": "run not found or already finished"})


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
                "ok": False,
                "error": "需要提供 client_task_id 和 device_serial",
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
        # Reset TaskCard status so it can be re-executed
        TaskCard.objects.filter(task_id=client_task_id).update(status="idle", running=False)
        return JsonResponse(
            {
                "ok": True,
                "message": f"已取消排队任务（{len(removed.get('case_ids', []))} 个用例）",
            }
        )

    # Fallback: task may be queued in DB but not in memory (e.g. after server restart)
    try:
        tc = TaskCard.objects.get(task_id=client_task_id, status="queued", device_serial=serial)
        tc.status = "idle"
        tc.running = False
        tc.save(update_fields=["status", "running"])
        return JsonResponse(
            {
                "ok": True,
                "message": f"已从数据库中取消排队任务",
            }
        )
    except TaskCard.DoesNotExist:
        pass

    return JsonResponse(
        {
            "ok": False,
            "error": "未找到该排队任务，可能已经开始执行",
        },
        status=404,
    )


def list_active(request):
    """GET /api/runner/active — List currently active runs.

    Also triggers lazy recovery: rebuild queues, mark orphan running tasks.
    """
    # Recover orphan running tasks (stuck after server restart)
    if not list_active_runs:
        orphans = TaskCard.objects.filter(status="running")
        if orphans.exists():
            orphans.update(status="done", running=False, outcome="interrupted")

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
                _enqueue(
                    serial,
                    {
                        "case_ids": tc.case_ids,
                        "loop_count": tc.loop_count,
                        "interval_seconds": tc.interval_seconds,
                        "package_name": "",
                        "start_at": None,
                        "end_at": None,
                        "client_task_id": tc.task_id,
                    },
                )
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
    for run_id, state in list_active_runs.items():
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
    # Clean up stale client_task_id mappings for finished runs
    for rid in list(_run_client_task.keys()):
        if rid not in list_active_runs:
            del _run_client_task[rid]
    return JsonResponse({"ok": True, "active": active})


def test_run_status(request, run_id):
    """GET /api/runner/run/{run_id}/status."""
    state = get_active_run(run_id)
    if state:
        return JsonResponse(
            {
                "ok": True,
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
                "ok": True,
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
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)


def list_test_runs(request):
    """GET /api/runner/runs — List run history."""
    rows = TestRunRecord.objects.annotate(
        total=Count("results"),
        passed=Count("results", filter=Q(results__result="pass")),
    ).order_by("-id")[:50]
    return JsonResponse(
        {
            "ok": True,
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


@require_auth
@csrf_exempt
def run_single_step(request):
    """POST /api/runner/run-step — Execute a single step on the current device for debugging."""
    data = json.loads(request.body) if request.body else {}
    step_type = data.get("type", "click")
    xpath = data.get("xpath", "")
    xpath2 = data.get("xpath2", "")
    timeout = data.get("timeout", 10)
    expected_text = data.get("expected_text", "")
    index = data.get("index", 0)
    direction = data.get("direction", "")
    distance = data.get("distance", 500)
    description = data.get("description", step_type)

    if step_type not in (
        "click",
        "long_click",
        "click_indexed",
        "swipe",
        "wait",
        "wait_disappear",
        "wait_any",
        "wait_toast",
        "sleep",
        "verify_text",
        "poll_text",
        "start_app",
        "kill_app",
        "restart_app",
        "retry_click",
        "log",
    ):
        return JsonResponse({"ok": False, "error": f"Unknown step type: {step_type}"})

    try:
        from .adapter import DeviceAdapter
        from .executor import StepExecutor

        target_serial = data.get("device_serial", "").strip()
        if target_serial:
            device.switch_to(target_serial)
        elif not device.current_serial:
            return JsonResponse({"ok": False, "error": "请先在用例编辑页顶部选择调试设备"})

        step = TestStep(
            type=step_type,
            xpath=xpath,
            xpath2=xpath2,
            timeout=timeout,
            expected_text=expected_text,
            index=index,
            direction=direction,
            distance=distance,
            description=description,
        )

        logs: list[str] = []
        adapter = DeviceAdapter(
            device.d,
            package_name=xpath if step_type in ("start_app", "kill_app", "restart_app") else "",
            logger=logs.append,
        )
        executor = StepExecutor(adapter)
        result = executor.execute(step)

        if result == "pass":
            return JsonResponse(
                {
                    "ok": True,
                    "result": result,
                    "message": f"步骤「{description}」执行成功",
                    "logs": logs,
                }
            )
        return JsonResponse(
            {
                "ok": False,
                "result": result,
                "error": f"步骤「{description}」执行失败 ({result})",
                "logs": logs,
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"步骤执行异常: {str(e)}"})


# ═══════════════════════════════════════════════════════
#  TaskCard CRUD — cross-device task card sync
# ═══════════════════════════════════════════════════════


def task_card_list(request):
    """GET /api/runner/tasks — List all task cards."""
    # 恢复孤儿任务（服务重启后残留）：status='running' 或 running=True 双重兜底
    if not list_active_runs:
        orphans = TaskCard.objects.filter(Q(status="running") | Q(running=True))
        if orphans.exists():
            orphans.update(status="done", running=False, outcome="interrupted")

    qs = TaskCard.objects.all().order_by("-created_at")[:200]
    cards = []
    for tc in qs:
        cards.append(
            {
                "id": tc.task_id,
                "name": tc.name,
                "mode": tc.mode,
                "deviceSerial": tc.device_serial,
                "caseIds": tc.case_ids,
                "loopCount": tc.loop_count,
                "intervalSeconds": tc.interval_seconds,
                # running 派生自 status，杜绝 status/running 双源不一致（僵尸"执行中"卡片）
                "running": tc.status == "running",
                "runId": tc.run.run_id if tc.run_id else "",
                "caseItems": tc.case_items,
                "stepStates": tc.step_states,
                "overallPass": tc.overall_pass,
                "overallFail": tc.overall_fail,
                "logs": tc.logs,
                "createdAt": str(tc.created_at),
                "creator": tc.creator,
                "currentCaseTitle": "",
                "currentIteration": 0,
                "failedSteps": tc.failed_steps,
                "status": tc.status,
                "outcome": tc.outcome,
                "round": tc.round,
                "conclusion": tc.conclusion,
                "bugTicket": tc.bug_ticket,
            }
        )
    return JsonResponse({"ok": True, "tasks": cards})


@require_auth
@csrf_exempt
def task_card_save(request):
    """POST /api/runner/tasks/save — Upsert a task card."""
    data = json.loads(request.body) if request.body else {}
    task_id = data.get("id", "").strip()
    if not task_id:
        return JsonResponse({"ok": False, "error": "任务ID不能为空"}, status=400)

    defaults = {
        "name": data.get("name", ""),
        "creator": data.get("creator", ""),
        "mode": data.get("mode", "immediate"),
        "device_serial": data.get("deviceSerial", ""),
        "case_ids": data.get("caseIds", []),
        "loop_count": data.get("loopCount", 1),
        "interval_seconds": data.get("intervalSeconds", 5),
        # running 不接受前端传入 —— 由后端运行时路径管理，避免与 status 漂移
        # run_id FK 由后端管理，不接受前端字符串（避免 FK 类型冲突）
        "case_items": data.get("caseItems", []),
        "step_states": data.get("stepStates", []),
        "overall_pass": data.get("overallPass", 0),
        "overall_fail": data.get("overallFail", 0),
        "logs": (data.get("logs") or [])[-200:],
        "outcome": data.get("outcome", ""),
        "round": data.get("round", 0),
        "conclusion": data.get("conclusion", ""),
        "bug_ticket": data.get("bugTicket", ""),
        "failed_steps": (data.get("failedSteps") or [])[-200:],
    }
    # status is backend-managed — only set on create, never overwrite from frontend
    try:
        task = TaskCard.objects.get(task_id=task_id)
        for k, v in defaults.items():
            setattr(task, k, v)
        task.save()
    except TaskCard.DoesNotExist:
        # Explicit create — every field must be set to avoid MySQL integrity errors
        task = TaskCard(
            task_id=task_id,
            name=data.get("name", ""),
            creator=data.get("creator", ""),
            mode=data.get("mode", "immediate"),
            device_serial=data.get("deviceSerial", ""),
            case_ids=data.get("caseIds", []),
            loop_count=data.get("loopCount", 1),
            interval_seconds=data.get("intervalSeconds", 5),
            running=False,  # 新建任务恒为未运行；执行由 POST /run 启动
            case_items=data.get("caseItems", []),
            step_states=data.get("stepStates", []),
            overall_pass=data.get("overallPass", 0),
            overall_fail=data.get("overallFail", 0),
            logs=(data.get("logs") or [])[-200:],
            outcome=data.get("outcome", ""),
            round=data.get("round", 0),
            conclusion=data.get("conclusion", ""),
            bug_ticket=data.get("bugTicket", ""),
            failed_steps=(data.get("failedSteps") or [])[-200:],
            status="idle",
        )
        task.save()
    return JsonResponse({"ok": True, "id": task_id})


@require_auth
@csrf_exempt
def task_card_delete(request, task_id):
    """DELETE /api/runner/tasks/{task_id} — Delete a task card."""
    try:
        TaskCard.objects.get(task_id=task_id).delete()
        return JsonResponse({"ok": True, "message": "已删除"})
    except TaskCard.DoesNotExist:
        return JsonResponse({"ok": True, "message": "任务不存在或已删除"})
