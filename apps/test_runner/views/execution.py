"""Main execution flow — start_test_run + queue dequeue."""
import json
import asyncio
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from models.step_types import TestStep
from models.test_models import TestCaseDef
from ..runner import (
    TestRunner, stop_run, is_device_busy, mark_device_busy, mark_device_idle,
    _device_executor as _u2_executor,
)
from ..device_connect import DeviceCheckError, check_and_connect_async
from ..callbacks import test_callbacks
from ..models import TestResult, TestRunRecord, TaskCard
from apps.device_pool.api import device
from apps.device_pool.api import acquire_device as dp_acquire_device
from apps.device_pool.api import release_device as dp_release_device
from apps.device_pool.models import Device as PoolDevice
from apps.case_manager.models import TestDefinition

from .helpers import (
    _bg_sync, sync_to_async, _bg_log,
    _enqueue, _enqueue_front, _device_lock, _dequeue, _queue_size,
    _device_queue, _run_client_task, _preflight_runs,
    _spawn_bg, _schedule_next_queued, _enqueue_taskcard, _abort_run_before_execute,
    require_auth,
)

from .executor import _execute_tests


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
                        _bg_log.exception("invalid start_at for %s: %r", rid, st)
                if et:

                    async def auto_stop(_rid=rid, _end_at=et):
                        try:
                            target = datetime.fromisoformat(_end_at)
                            delay = (target - datetime.now()).total_seconds()
                            if delay > 0:
                                await asyncio.sleep(delay)
                                stop_run(_rid)
                                await test_callbacks.on_log(_rid, "⏰ 到达结束时间，自动停止")
                        except Exception:
                            _bg_log.exception("auto_stop failed for %s", _rid)

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
                    _bg_log.exception("delayed_execute failed %s", rid)
                    await _abort_run_before_execute(rid, _serial, _ctid, str(e))
            finally:
                # 兜底:持有锁却未交接执行、也未走 abort 的异常退出,确保释放设备(幂等)
                if pending_release:
                    mark_device_idle(_serial)
                    try:
                        await sync_to_async(dp_release_device)(_serial, reason="manual")
                    except Exception:
                        _bg_log.exception("delayed_execute finally release %s", _serial)
                    _preflight_runs.pop(rid, None)
                    _schedule_next_queued(_serial)

        # 登记预检阶段,供 stop 在"锁了手机但还没真正执行"时打停止标记
        _preflight_runs[run_id] = {
            "stopped": False,
            "serial": serial,
            "client_task_id": client_task_id,
        }
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


async def _start_next_queued(serial: str):
    """Dequeue and start the next waiting task for a device.

    Called from _execute_tests.finally after a run finishes.
    Must be atomic: mark busy → dequeue → start, to prevent races.
    """
    if not serial:
        return

    lock = _device_lock(serial)
    async with lock:
        if is_device_busy(serial):
            return
        next_req = _dequeue(serial)
        if not next_req:
            return
        mark_device_busy(serial)

    # DB-level acquire — cross-process protection (outside lock)
    try:
        await sync_to_async(dp_acquire_device)(serial, user_id=f"runner-{serial}", timeout=3600)
    except ValueError as e:
        mark_device_idle(serial)
        _enqueue_front(serial, next_req)
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
            try:
                await sync_to_async(dp_release_device)(serial, reason="error")
            except Exception:
                _bg_log.exception("release device %s after empty queue load", serial)
            _schedule_next_queued(serial)
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
        _bg_log.exception("queue task start failed on %s", serial)
        await test_callbacks.on_log(
            f"queue_{serial}", f"❌ 队列任务启动失败: {e}（剩余 {_queue_size(serial)} 个排队）"
        )
        mark_device_idle(serial)
        try:
            await sync_to_async(dp_release_device)(serial, reason="manual")
        except Exception:
            _bg_log.exception("dp_release_device(%s) in queue handler failed", serial)
        if not executed:
            # Exception happened before _execute_tests was reached
            # (e.g. load() or u2.connect() failed). Retry next queued task.
            _schedule_next_queued(serial)
        # else: _execute_tests.finally handles cleanup + schedules next dequeue