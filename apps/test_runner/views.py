"""test-runner HTTP routes — 4 endpoints under /api/runner/*."""
import json
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Max
from asgiref.sync import sync_to_async

from models.step_types import TestStep
from models.test_models import TestCaseDef
from .runner import (TestRunner, get_active_run, stop_run,
                       is_device_busy, mark_device_busy, mark_device_idle)
from .runner import _active_runs as list_active_runs
from .callbacks import test_callbacks
from .models import TestResult
from apps.device_pool.api import device
from ..device_pool.models import Device as PoolDevice
from ..case_manager.models import TestDefinition

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


async def start_test_run(request):
    """POST /api/runner/run — Start async test execution (multi-device + schedule).

    Accepts:
      - device_serials: list of device serials (one run per device)
      - device_serial:  single serial (backward compat)
      - start_at:  ISO datetime for delayed start (None = immediate)
      - end_at:    ISO datetime for auto-stop (None = run until done/stopped)
    """
    data = json.loads(request.body)
    case_ids = data.get("case_ids", [])
    loop_count = data.get("loop_count", 3)
    package_name = data.get("package_name", "")
    start_at = data.get("start_at")      # ISO str or None
    end_at = data.get("end_at")          # ISO str or None
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
                id=r.id, title=r.title, category=r.category,
                description=r.description, steps=r.steps,
                enabled=r.enabled, steps_data=steps_data, is_json=True,
                package_name=r.package_name or package_name,
                created_at=str(r.created_at), updated_at=str(r.updated_at),
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
        if dev.status in ('OFFLINE', 'DISCONNECTED'):
            continue

        # Check if device is already executing — queue the request
        if is_device_busy(serial):
            _enqueue(serial, {
                "case_ids": case_ids,
                "loop_count": loop_count,
                "package_name": effective_pkg,
                "start_at": start_at,
                "end_at": end_at,
                "client_task_id": client_task_id,
            })
            await test_callbacks.on_log(
                f"queue_{serial}", f"⏳ 设备 {serial} 正忙，任务已加入队列（前面有 {_queue_size(serial)} 个任务）")
            queued_serials.append(serial)
            continue

        # Create independent u2 connection per device
        def make_connection(s=serial):
            import uiautomator2 as u2
            return u2.connect(s)
        d = await asyncio.get_event_loop().run_in_executor(None, make_connection)

        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if client_task_id:
            _run_client_task[run_id] = client_task_id
        runner = TestRunner(d, effective_pkg, callback=test_callbacks)

        # Capture serial in default arg to avoid closure-over-loop-variable bug
        async def delayed_execute(rid, r, tcs, lc, st, et, _serial=serial):
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
            await _execute_tests(rid, r, tcs, lc, _serial)

        asyncio.create_task(delayed_execute(run_id, runner, test_cases, loop_count, start_at, end_at))
        run_ids.append({"run_id": run_id, "serial": serial})

    if not run_ids and not queued_serials:
        return JsonResponse({
            "ok": False,
            "error": "没有可用设备，请确认设备已连接且状态为在线",
        }, status=400)

    return JsonResponse({
        "ok": True,
        "runs": run_ids,
        "queued": queued_serials,
        "case_count": len(test_cases),
        "loop_count": loop_count,
        "parallel": len(run_ids),
    })


async def _execute_tests(run_id: str, runner, test_cases: list, loop_count: int, serial: str = ""):
    try:
        # Log device info
        dev_serial = serial or runner.device.serial if hasattr(runner.device, 'serial') else '?'
        await test_callbacks.on_log(run_id, f"📱 设备: {dev_serial}")
        try:
            d_info = runner.device.info
            await test_callbacks.on_log(
                run_id,
                f"分辨率: {d_info.get('displayWidth', '?')}x{d_info.get('displayHeight', '?')}"
            )
        except Exception:
            pass
        await test_callbacks.on_log(run_id, f"循环次数: {loop_count}")
        for tc in test_cases:
            step_count = len(tc.steps_data) if tc.steps_data else 0
            await test_callbacks.on_log(
                run_id,
                f"用例: [{tc.id}] {tc.title} ({step_count} 步)"
            )
        await test_callbacks.on_log(run_id, "────────────────────")

        run_model = await runner.run(run_id, test_cases, loop_count)

        @sync_to_async
        def persist():
            for r in run_model.case_results:
                TestResult.objects.create(
                    case_id=r.case_id, iteration=r.iteration,
                    result=r.result, duration_ms=r.duration_ms, detail=r.detail,
                )
        await persist()
    except Exception as e:
        print(f"Test run {run_id} error: {e}")
        await test_callbacks.on_device_error(run_id, str(e))
    finally:
        # Start next queued task for this device
        asyncio.create_task(_start_next_queued(serial))


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

    await test_callbacks.on_log(
        f"queue_{serial}",
        f"📤 设备 {serial} 空闲，从队列取出任务开始执行（剩余 {_queue_size(serial)} 个排队）")

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
                tcs.append(TestCaseDef(
                    id=r.id, title=r.title, category=r.category,
                    description=r.description, steps=r.steps,
                    enabled=r.enabled, steps_data=steps_data, is_json=True,
                    package_name=r.package_name or next_req.get("package_name", ""),
                    created_at=str(r.created_at), updated_at=str(r.updated_at),
                ))
            return tcs

        test_cases = await load()
        if not test_cases:
            mark_device_idle(serial)
            return

        # Create u2 connection and runner
        def make_connection():
            import uiautomator2 as u2
            return u2.connect(serial)

        d = await asyncio.get_event_loop().run_in_executor(None, make_connection)
        run_id = f"run_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        client_task_id = next_req.get("client_task_id", "")
        if client_task_id:
            _run_client_task[run_id] = client_task_id
        runner = TestRunner(d, next_req.get("package_name", ""), callback=test_callbacks)
        await _execute_tests(
            run_id, runner, test_cases,
            next_req.get("loop_count", 3), serial)
    except Exception as e:
        print(f"[queue] Failed to start queued task on {serial}: {e}")
        await test_callbacks.on_log(
            f"queue_{serial}",
            f"❌ 队列任务启动失败: {e}（剩余 {_queue_size(serial)} 个排队）")
        mark_device_idle(serial)
        # Try next queued task if any
        asyncio.create_task(_start_next_queued(serial))


@csrf_exempt
def stop_test_run(request, run_id):
    """POST /api/runner/run/{run_id}/stop."""
    if stop_run(run_id):
        return JsonResponse({"ok": True, "message": "stop requested"})
    return JsonResponse({"ok": False, "error": "run not found or already finished"})


def list_active(request):
    """GET /api/runner/active — List currently active runs."""
    active = []
    for run_id, state in list_active_runs.items():
        if state.is_running:
            active.append({
                "run_id": run_id,
                "status": state.run_model.status.value,
                "selected_cases": state.run_model.selected_cases,
                "loop_count": state.run_model.loop_count,
                "started_at": state.run_model.started_at,
                "device_serial": state.run_model.device_serial,
                "client_task_id": _run_client_task.get(run_id, ""),
            })
    # Clean up stale client_task_id mappings for finished runs
    for rid in list(_run_client_task.keys()):
        if rid not in list_active_runs:
            del _run_client_task[rid]
    return JsonResponse({"ok": True, "active": active})


def test_run_status(request, run_id):
    """GET /api/runner/run/{run_id}/status."""
    state = get_active_run(run_id)
    if state:
        return JsonResponse({
            "ok": True, "run_id": run_id,
            "status": state.run_model.status.value,
            "is_running": state.is_running,
            "selected_cases": state.run_model.selected_cases,
            "loop_count": state.run_model.loop_count,
            "started_at": state.run_model.started_at,
        })

    agg = TestResult.objects.filter(case_id__startswith=run_id[:10]).aggregate(
        total=Count('id'), passed=Count('id', filter=Q(result='pass')),
    )
    if agg["total"]:
        return JsonResponse({
            "ok": True, "run_id": run_id, "status": "completed",
            "total_iterations": agg["total"], "passed": agg["passed"],
        })

    return JsonResponse({"ok": False, "error": "run not found"}, status=404)


def list_test_runs(request):
    """GET /api/runner/runs — List run history."""
    rows = (
        TestResult.objects
        .values('id')  # placeholder — group by recent
        .annotate(
            total=Count('id'), passed=Count('id', filter=Q(result='pass')),
            failed=Count('id', filter=Q(result='fail')), last_time=Max('created_at'),
        )
        .order_by('-last_time')[:50]
    )
    return JsonResponse({"ok": True, "runs": list(rows)})


@csrf_exempt
def run_single_step(request):
    """POST /api/runner/run-step — Execute a single step on the current device for debugging."""
    data = json.loads(request.body) if request.body else {}
    step_type = data.get('type', 'click')
    xpath = data.get('xpath', '')
    xpath2 = data.get('xpath2', '')
    timeout = data.get('timeout', 10)
    expected_text = data.get('expected_text', '')
    index = data.get('index', 0)
    direction = data.get('direction', '')
    distance = data.get('distance', 500)
    description = data.get('description', step_type)

    if step_type not in ('click', 'long_click', 'click_indexed', 'swipe', 'wait', 'wait_disappear',
                         'wait_any', 'wait_toast', 'sleep', 'verify_text', 'poll_text',
                         'start_app', 'kill_app', 'restart_app', 'retry_click', 'log'):
        return JsonResponse({"ok": False, "error": f"Unknown step type: {step_type}"})

    try:
        from .adapter import DeviceAdapter
        from .executor import StepExecutor

        target_serial = data.get('device_serial', '').strip()
        if target_serial:
            device.switch_to(target_serial)
        elif not device.current_serial:
            return JsonResponse({"ok": False, "error": "请先在用例编辑页顶部选择调试设备"})

        step = TestStep(
            type=step_type, xpath=xpath, xpath2=xpath2, timeout=timeout,
            expected_text=expected_text, index=index, direction=direction,
            distance=distance, description=description,
        )

        logs: list[str] = []
        adapter = DeviceAdapter(
            device.d,
            package_name=xpath if step_type in ('start_app', 'kill_app', 'restart_app') else '',
            logger=logs.append,
        )
        executor = StepExecutor(adapter)
        result = executor.execute(step)

        if result == 'pass':
            return JsonResponse({
                "ok": True,
                "result": result,
                "message": f"步骤「{description}」执行成功",
                "logs": logs,
            })
        return JsonResponse({
            "ok": False,
            "result": result,
            "error": f"步骤「{description}」执行失败 ({result})",
            "logs": logs,
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"步骤执行异常: {str(e)}"})
