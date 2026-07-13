"""test-runner HTTP routes — 10 endpoints under /api/runner/*."""

import json
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from asgiref.sync import sync_to_async as _original_sta

# All sync_to_async in this file use thread_sensitive=False to avoid capturing
# the request-scoped CurrentThreadExecutor which dies after the HTTP response,
# breaking all background tasks (delayed_execute / _execute_tests / etc).
# None of our code relies on thread-sensitive DB state.
def _sta(fn):
    return _original_sta(fn, thread_sensitive=False)

# Drop-in replacements for @sync_to_async decorator and sync_to_async(func)() calls
_bg_sync = _sta           # decorator: @_bg_sync
sync_to_async = _sta       # inline:   sync_to_async(func)(args)

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
from .device_connect import DeviceCheckError, check_and_connect_async
from .callbacks import test_callbacks
from .models import TestResult, TestRunRecord, TaskCard
from . import state_machine as sm
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

# 后台任务引用保存 —— 防止 asyncio.create_task 的 Task 被 GC 回收、异常被静默吞掉
_bg_tasks: set = set()
# run_id → 预检阶段登记(锁了手机但还没真正执行)。供 stop 打"停止标记";
# delayed_execute 据此在释放设备+标记停止后退出,避免设备锁泄漏。
# 结构: {run_id: {"stopped": bool, "serial": str, "client_task_id": str}}
_preflight_runs: dict = {}


def _spawn_bg(coro, label: str = "bg"):
    """创建后台任务并保存引用,完成时记录异常(替代 fire-and-forget 吞错)。"""
    import logging, traceback, sys
    _bg_log = logging.getLogger("test_runner.bg")
    t = asyncio.create_task(coro)
    _bg_tasks.add(t)
    _bg_log.info(f"后台任务已创建: {label} (active={len(_bg_tasks)})")

    def _done(task):
        _bg_tasks.discard(task)
        if not task.cancelled():
            exc = task.exception()
            if exc is not None:
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                _bg_log.error(f"后台任务 {label} 异常: {exc!r}\n{tb}")
                print(f"[views] 后台任务 {label} 异常: {exc!r}", file=sys.stderr)
            else:
                _bg_log.info(f"后台任务 {label} 正常完成 (remaining={len(_bg_tasks)})")
        else:
            _bg_log.info(f"后台任务 {label} 被取消 (remaining={len(_bg_tasks)})")

    t.add_done_callback(_done)
    return t

# u2.connect() 超时上限（秒）—— USB 松动 / ATX agent 卡死时快速失败，
# 避免阻塞占用 _u2_executor 线程 / Daphne 事件循环。
U2_CONNECT_TIMEOUT = 15


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
        _spawn_bg(_start_next_queued(serial), f"next_queued:{serial}")


async def _enqueue_taskcard(client_task_id: str, serial: str):
    """Route a TaskCard IDLE → QUEUED through the state machine.

    Used when a device is busy and the task is parked in the in-memory queue.
    Idempotent + fault-tolerant: never raises to the caller.
    """
    if not client_task_id:
        return

    @_bg_sync
    def _do():
        try:
            tc = TaskCard.objects.get(task_id=client_task_id)
        except TaskCard.DoesNotExist:
            return
        try:
            sm.enqueue(tc, serial)
        except sm.InvalidTransition as e:
            print(f"[views] enqueue transition {client_task_id}: {e}")
        except Exception as e:
            print(f"[views] enqueue {client_task_id}: {e}")

    await _do()


async def _abort_run_before_execute(
    run_id: str, serial: str, client_task_id: str, error: str, outcome: str = "error"
):
    """执行前退出(设备检查失败 / 执行前异常 / 用户中途停止):
    释放设备、把 TaskCard 推到 done 终态、通知前端。outcome='error' 或 'stopped'。
    """
    import logging
    _log = logging.getLogger("test_runner.bg")
    _log.info(f"_abort_run_before_execute: {run_id} error={error} outcome={outcome}")
    icon = "⏹" if outcome == "stopped" else "❌"
    await test_callbacks.on_log(run_id, f"{icon} {error}")
    # 停止是用户主动行为,不当作"设备错误"上报(避免前端标红为 error)
    if outcome != "stopped":
        await test_callbacks.on_device_error(run_id, error)
    mark_device_idle(serial)
    try:
        await sync_to_async(dp_release_device)(serial, reason="manual")
    except Exception as e:
        print(f"[views] release after pre-run abort ({serial}): {e}")
    if client_task_id:

        @_bg_sync
        def mark_terminal():
            try:
                tc = TaskCard.objects.get(task_id=client_task_id)
            except TaskCard.DoesNotExist:
                return
            # 走完整合法路径 idle→queued→running→done,dequeue 建一条审计 TestRunRecord
            try:
                sm.enqueue(tc, serial)
                rec = sm.dequeue(tc, run_id, serial, [], tc.loop_count or 1)
                sm.fail(tc, rec, outcome=outcome)
            except sm.InvalidTransition as e:
                print(f"[views] pre-run mark {client_task_id}: {e}")
            except Exception as e:
                print(f"[views] pre-run mark task {client_task_id}: {e}")

        try:
            await mark_terminal()
        except Exception as e:
            print(f"[views] pre-run mark task {client_task_id}: {e}")
    _run_client_task.pop(run_id, None)
    _preflight_runs.pop(run_id, None)
    _schedule_next_queued(serial)


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

    @_bg_sync
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
                await _enqueue_taskcard(client_task_id, serial)
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
                await _enqueue_taskcard(client_task_id, serial)
            await test_callbacks.on_log(f"queue_{serial}", f"⏳ 设备 {serial} {e}，任务已加入队列")
            queued_serials.append(serial)
            continue
        mark_device_busy(serial)
        if client_task_id:
            schedule_update = {}
            if start_at:
                schedule_update["start_at"] = start_at
            if end_at:
                schedule_update["end_at"] = end_at
            if schedule_update:
                await sync_to_async(TaskCard.objects.filter(task_id=client_task_id).update)(
                    **schedule_update
                )

        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if client_task_id:
            _run_client_task[run_id] = client_task_id

        # Capture serial in default arg to avoid closure-over-loop-variable bug
        async def delayed_execute(
            rid, tcs, lc, interval, st, et, pkg, _serial=serial, _ctid=client_task_id
        ):
            pending_release = True  # 已持有设备锁,退出前须确保释放(除非交接给 _execute_tests)
            import logging
            _bg_log = logging.getLogger("test_runner.bg")
            _bg_log.info(f"delayed_execute 开始: {rid} device={_serial}")
            try:
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

                    _spawn_bg(auto_stop(), f"auto_stop:{rid}")

                # 延迟阶段就被停止
                if _preflight_runs.get(rid, {}).get("stopped"):
                    await _abort_run_before_execute(
                        rid, _serial, _ctid, "任务已被停止", outcome="stopped"
                    )
                    pending_release = False
                    return

                # ── 预检:检测在线 → 连接 → 验证能跑用例 ──
                try:
                    d = await check_and_connect_async(_serial, rid, test_callbacks, _u2_executor)
                except DeviceCheckError as e:
                    await _abort_run_before_execute(rid, _serial, _ctid, f"手机连接不上: {e}")
                    pending_release = False
                    return
                except Exception as e:
                    await _abort_run_before_execute(rid, _serial, _ctid, f"执行前异常: {e}")
                    pending_release = False
                    return

                # 连接期间被停止 → 按停止善后,不进入执行
                if _preflight_runs.get(rid, {}).get("stopped"):
                    await _abort_run_before_execute(
                        rid, _serial, _ctid, "任务已被停止", outcome="stopped"
                    )
                    pending_release = False
                    return

                # ── 预检通过:交接给执行(由 _execute_tests 的 finally 负责释放设备)──
                _preflight_runs.pop(rid, None)
                await test_callbacks.on_run_started(rid)
                pending_release = False
                try:
                    runner = TestRunner(d, pkg, callback=test_callbacks)
                    await _execute_tests(rid, runner, tcs, lc, interval, _serial)
                except Exception as e:
                    print(f"[runner] delayed_execute failed {rid}: {e}")
                    await _abort_run_before_execute(rid, _serial, _ctid, str(e))
            finally:
                # 兜底:持有锁却未交接执行、也未走 abort 的异常退出,确保释放设备(幂等)
                if pending_release:
                    mark_device_idle(_serial)
                    try:
                        await sync_to_async(dp_release_device)(_serial, reason="manual")
                    except Exception as e:
                        print(f"[views] delayed_execute finally release {_serial}: {e}")
                    _preflight_runs.pop(rid, None)
                    _schedule_next_queued(_serial)

        _spawn_bg(
            delayed_execute(
                run_id,
                test_cases,
                loop_count,
                interval_seconds,
                start_at,
                end_at,
                effective_pkg,
            ),
            f"delayed:{run_id}",
        )
        # 登记预检阶段,供 stop 在"锁了手机但还没真正执行"时打停止标记
        _preflight_runs[run_id] = {
            "stopped": False,
            "serial": serial,
            "client_task_id": client_task_id,
        }
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
    import logging
    _log = logging.getLogger("test_runner.bg")
    run_record = None
    run_completed = False
    effective_serial = serial or (getattr(runner.device, "serial", None) or "")
    try:
        client_tid = _run_client_task.get(run_id, "")
        dev_serial = serial or (runner.device.serial if hasattr(runner.device, "serial") else "")
        _log.info(f"_execute_tests 开始: {run_id} client_tid={client_tid} serial={dev_serial}")

        # Persist run record with case snapshot before execution. The snapshot
        # (case_id/title/steps_data) must survive later case edits for auditing.
        @_bg_sync
        def start_run():
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
            # Unified state path: enqueue (idle→queued) then dequeue (queued→running).
            # dequeue atomically creates the TestRunRecord and links it to the card.
            tc_card = None
            if client_tid:
                try:
                    tc_card = TaskCard.objects.get(task_id=client_tid)
                except TaskCard.DoesNotExist:
                    tc_card = None
            if tc_card is not None:
                try:
                    sm.enqueue(tc_card, dev_serial)
                    return sm.dequeue(tc_card, run_id, dev_serial, snapshots, loop_count)
                except sm.InvalidTransition as e:
                    print(f"[views] start_run transition {client_tid}: {e}")
                except Exception as e:
                    print(f"[views] start_run {client_tid}: {e}")
            # No TaskCard (or transition failed) → standalone record so execution
            # still proceeds and stays auditable.
            return TestRunRecord.objects.create(
                run_id=run_id,
                client_task_id=client_tid or "",
                status="RUNNING",
                device_serial=dev_serial,
                selected_cases=snapshots,
                loop_count=loop_count,
                started_at=datetime.now().isoformat(),
            )

        run_record = await start_run()
        _log.info(f"_execute_tests run_record={run_record.id if run_record else 'None'} status={run_record.status if run_record else 'N/A'}")

        # 设备检查已在 delayed_execute 完成；此处输出执行计划
        dev_serial = serial or (runner.device.serial if hasattr(runner.device, "serial") else "?")
        await test_callbacks.on_log(run_id, f"📱 当前设备 ID: {dev_serial}")
        await test_callbacks.on_log(run_id, f"循环 {loop_count} 轮 · 共 {len(test_cases)} 个用例")
        for tc in test_cases:
            step_count = len(tc.steps_data) if tc.steps_data else 0
            await test_callbacks.on_log(run_id, f"  · 用例 [{tc.id}] {tc.title} ({step_count} 步)")
        await test_callbacks.on_log(run_id, "────────────────────")

        run_model = await runner.run(run_id, test_cases, loop_count, interval_seconds)
        run_completed = True
        # Device is free — schedule next queued task before slow DB writes
        _schedule_next_queued(effective_serial)

        @_bg_sync
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

        # Finalize: aggregate results, then drive the terminal transition through
        # the state machine (complete/fail update TaskCard + TestRunRecord atomically).
        client_tid = _run_client_task.get(run_id, "")

        @_bg_sync
        def finalize():
            # Build case_items + overall counts from run results — single pass
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

            tc_card = None
            if client_tid:
                try:
                    tc_card = TaskCard.objects.get(task_id=client_tid)
                except TaskCard.DoesNotExist:
                    tc_card = None

            for cid, counts in by_case.items():
                # Title from selected_cases snapshot
                title = cid
                for sc in run_record.selected_cases or []:
                    if sc.get("case_id") == cid:
                        title = sc.get("title", cid)
                        break
                # Preserve step definitions from existing TaskCard case_items
                steps = []
                if tc_card is not None:
                    for old_ci in tc_card.case_items or []:
                        if str(old_ci.get("id")) == str(cid) and old_ci.get("steps"):
                            steps = old_ci["steps"]
                            break
                item = {
                    "id": cid,
                    "title": title,
                    "total": counts["total"],
                    "pass": counts["pass"],
                    "fail": counts["fail"],
                    "rate": round(counts["pass"] / counts["total"] * 100) if counts["total"] else 0,
                    "status": "done",
                }
                if steps:
                    item["steps"] = steps
                case_items.append(item)

            if tc_card is not None:
                try:
                    # 尊重用户手动停止 / 已记录的终态，不被 completed 覆盖
                    if tc_card.outcome in ("stopped", "interrupted", "error"):
                        sm.fail(
                            tc_card,
                            run_record,
                            outcome=tc_card.outcome,
                            overall_pass=overall_pass,
                            overall_fail=overall_fail,
                            case_items=case_items,
                            summary=run_model.summary,
                        )
                    elif run_model.status.value == "completed":
                        sm.complete(
                            tc_card,
                            run_record,
                            run_model.summary,
                            case_items,
                            overall_pass=overall_pass,
                            overall_fail=overall_fail,
                        )
                    else:
                        sm.fail(
                            tc_card,
                            run_record,
                            outcome="stopped",
                            overall_pass=overall_pass,
                            overall_fail=overall_fail,
                            case_items=case_items,
                            summary=run_model.summary,
                        )
                except sm.InvalidTransition as e:
                    print(f"[views] finalize transition {client_tid}: {e}")
                except Exception as e:
                    print(f"[views] finalize {client_tid}: {e}")
            else:
                # No TaskCard — finalize the run record standalone.
                run_record.status = run_model.status.value
                run_record.summary = run_model.summary
                run_record.finished_at = datetime.now().isoformat()
                run_record.save(update_fields=["status", "summary", "finished_at"])

        await finalize()

    except Exception as e:
        import traceback
        _log.error(f"Test run {run_id} error: {e}\n{traceback.format_exc()}")
        print(f"Test run {run_id} error: {e}")
        await test_callbacks.on_device_error(run_id, str(e))
        # Drive TaskCard to error via the state machine; always finalize the run
        # record as FAILED when the card can't take the transition.
        client_tid = _run_client_task.get(run_id, "")

        @_bg_sync
        def mark_failed():
            tc_card = None
            if client_tid:
                try:
                    tc_card = TaskCard.objects.get(task_id=client_tid)
                except TaskCard.DoesNotExist:
                    tc_card = None
            # Preserve an already-recorded terminal outcome (e.g. user stopped).
            if tc_card is not None and tc_card.outcome not in (
                "stopped",
                "interrupted",
                "error",
            ):
                try:
                    sm.fail(tc_card, run_record, outcome="error")
                    return  # fail() also finalized run_record
                except sm.InvalidTransition as e:
                    print(f"[views] mark_failed transition {client_tid}: {e}")
                except Exception as e:
                    print(f"[views] mark_failed {client_tid}: {e}")
            # TaskCard terminal/missing or transition failed → finalize run record.
            if run_record:
                run_record.status = "FAILED"
                run_record.finished_at = datetime.now().isoformat()
                run_record.save(update_fields=["status", "finished_at"])

        try:
            await mark_failed()
        except Exception as e:
            print(f"[views] mark_failed({run_id}) failed: {e}")
    finally:
        _log.info(f"_execute_tests finally: run_completed={run_completed} device={effective_serial}")
        # runner.run() also calls mark_device_idle in its own finally;
        # discard is idempotent. Only schedule dequeue if run never started.
        mark_device_idle(effective_serial)
        # Release DB-level device occupation
        try:
            await sync_to_async(dp_release_device)(effective_serial, reason="manual")
            _log.info(f"_execute_tests dp_release_device OK: {effective_serial}")
        except Exception as e:
            _log.error(f"_execute_tests dp_release_device({effective_serial}) failed: {e}")
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
    client_task_id = next_req.get("client_task_id", "")

    await test_callbacks.on_log(
        f"queue_{serial}",
        f"📤 设备 {serial} 空闲，从队列取出任务开始执行（剩余 {_queue_size(serial)} 个排队）",
    )

    executed = False  # tracks whether _execute_tests was reached
    try:
        # Load test cases
        @_bg_sync
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

        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        client_task_id = next_req.get("client_task_id", "")
        if client_task_id:
            _run_client_task[run_id] = client_task_id

        try:
            d = await check_and_connect_async(serial, run_id, test_callbacks, _u2_executor)
        except DeviceCheckError as e:
            await _abort_run_before_execute(run_id, serial, client_task_id, str(e))
            return

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
    # 活跃 run:走优雅停止(设置 is_running=False,执行循环到检查点自然收尾)
    if stop_run(run_id):
        return JsonResponse({"ok": True, "message": "stop requested"})
    # 预检阶段(锁了手机但还没真正执行):打停止标记,
    # delayed_execute 会在预检检查点释放设备 + 标记停止,避免设备锁泄漏
    pf = _preflight_runs.get(run_id)
    if pf is not None:
        pf["stopped"] = True
        return JsonResponse({"ok": True, "message": "stopping (pre-flight)"})
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
        # Reset TaskCard status so it can be re-executed — via state machine.
        try:
            tc = TaskCard.objects.get(task_id=client_task_id)
            sm.cancel(tc)
        except TaskCard.DoesNotExist:
            pass
        except sm.InvalidTransition as e:
            print(f"[views] cancel transition {client_task_id}: {e}")
        return JsonResponse(
            {
                "ok": True,
                "message": f"已取消排队任务（{len(removed.get('case_ids', []))} 个用例）",
            }
        )

    # Fallback: task may be queued in DB but not in memory (e.g. after server restart)
    try:
        tc = TaskCard.objects.get(task_id=client_task_id, status="queued", device_serial=serial)
        sm.cancel(tc)
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


@require_auth
def list_active(request):
    """GET /api/runner/active — List currently active runs.

    Also triggers lazy recovery: rebuild queues, mark orphan running tasks.
    """
    from .recovery_helpers import recover_stale_running_taskcards, queue_payload_from_taskcard

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


@require_auth
def task_card_list(request):
    """GET /api/runner/tasks — List all task cards."""
    from .recovery_helpers import recover_stale_running_taskcards

    recover_stale_running_taskcards()

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
                "currentCaseTitle": tc.current_case_title or "",
                "currentIteration": tc.current_iteration or 0,
                "failedSteps": tc.failed_steps,
                "status": tc.status,
                "outcome": tc.outcome,
                "round": tc.round,
                "conclusion": tc.conclusion,
                "bugTicket": tc.bug_ticket,
                "startAt": tc.start_at or "",
                "endAt": tc.end_at or "",
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
        "current_case_title": data.get("currentCaseTitle", ""),
        "current_iteration": int(data.get("currentIteration") or 0),
        "start_at": data.get("startAt") or "",
        "end_at": data.get("endAt") or "",
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
            current_case_title=data.get("currentCaseTitle", ""),
            current_iteration=int(data.get("currentIteration") or 0),
            start_at=data.get("startAt") or "",
            end_at=data.get("endAt") or "",
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


# ═══════════════════════════════════════════════════════════════
# TREP v1.0 Phase 0: 监控端点 + 状态快照
# ═══════════════════════════════════════════════════════════════


@require_auth
def run_monitor(request, run_id):
    """GET /api/runner/monitor/:run_id — TREP v1.0 协议健康监控。

    返回: {ok, live, status, device, log_tail, is_running, started_at, ...}
    WS 断开时前端可降级轮询此端点。
    """
    state = get_active_run(run_id)

    if not state:
        # 已完成/不存在的 run → 查 DB
        try:
            record = TestRunRecord.objects.get(run_id=run_id)
            return JsonResponse({
                "ok": True, "run_id": run_id,
                "live": False,
                "status": record.status,
                "device_serial": record.device_serial,
                "selected_cases": record.selected_cases,
                "loop_count": record.loop_count,
                "summary": record.summary,
                "started_at": record.started_at,
                "finished_at": record.finished_at,
            })
        except TestRunRecord.DoesNotExist:
            return JsonResponse({"ok": False, "error": "run not found"}, status=404)

    # Live run — 组装实时状态快照
    adapter = state.adapter
    device_info = {"serial": state.run_model.device_serial, "status": "connected"}
    if adapter and adapter.d:
        try:
            info = adapter.d.info
            device_info.update({
                "resolution": f"{info.get('displayWidth', '?')}x{info.get('displayHeight', '?')}",
                "sdk": info.get("sdkVersion", "?"),
                "battery": info.get("battery", {}).get("level", "?"),
            })
        except Exception:
            device_info["status"] = "disconnected"

    return JsonResponse({
        "ok": True, "run_id": run_id,
        "live": True,
        "status": state.run_model.status.value if hasattr(state.run_model.status, 'value') else str(state.run_model.status),
        "is_running": state.is_running,
        "device": device_info,
        "selected_cases": state.run_model.selected_cases,
        "loop_count": state.run_model.loop_count,
        "started_at": state.run_model.started_at,
        "log_tail": state.log_lines[-50:],
    })


@require_auth
def run_snapshot(request, run_id):
    """GET /api/runner/run/:run_id/snapshot — TREP v1.0 状态快照（WS 降级兜底）。

    返回: {ok, live, status, cases: [{case_id, pass, fail, total}], client_task_id}
    """
    state = get_active_run(run_id)
    client_tid = _run_client_task.get(run_id, "")

    if state:
        # Live run — 从内存组装
        cases = []
        for r in state.all_results:
            cases.append({
                "case_title": r.get("case_title", ""),
                "pass": int(r.get("pass", 0)),
                "fail": int(r.get("fail", 0)),
                "rate": r.get("rate", "0%"),
            })
        return JsonResponse({
            "ok": True, "run_id": run_id,
            "live": True,
            "status": state.run_model.status.value if hasattr(state.run_model.status, 'value') else str(state.run_model.status),
            "cases": cases,
            "client_task_id": client_tid,
        })

    # 已完成 run → 从 DB
    try:
        record = TestRunRecord.objects.get(run_id=run_id)
        from .models import TestResult as TR
        results = TR.objects.filter(run=record)
        by_case = {}
        for r in results:
            cid = str(r.case_id) if r.case_id else "unknown"
            if cid not in by_case:
                by_case[cid] = {"case_id": cid, "pass": 0, "fail": 0, "total": 0}
            by_case[cid]["total"] += 1
            if r.result == "pass":
                by_case[cid]["pass"] += 1
            else:
                by_case[cid]["fail"] += 1
        return JsonResponse({
            "ok": True, "run_id": run_id,
            "live": False,
            "status": record.status,
            "cases": list(by_case.values()),
            "client_task_id": record.client_task_id,
        })
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)
