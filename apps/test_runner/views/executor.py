"""Core test executor — _execute_tests."""
import logging
from datetime import datetime
from django.db.models import Count, Q

from .helpers import (
    _bg_sync, _bg_log,
    _run_client_task,
    _schedule_next_queued,
)

from ..runner import mark_device_idle
from ..callbacks import test_callbacks
from ..models import TestResult, TestRunRecord, TaskCard
from .. import state_machine as sm
from apps.device_pool.api import release_device as dp_release_device


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
        dev_serial = serial or (runner.device_conn.serial if hasattr(runner, "device_conn") and hasattr(runner.device_conn, "serial") else "")
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
                    if tc_card.status == "queued":
                        # 已在队列中（设备忙时入队）— 只需 dequeue，不可再 enqueue
                        return sm.dequeue(
                            tc_card, run_id, dev_serial, snapshots, loop_count
                        )
                    if tc_card.status == "idle":
                        sm.enqueue(tc_card, dev_serial)
                        return sm.dequeue(
                            tc_card, run_id, dev_serial, snapshots, loop_count
                        )
                    if tc_card.status == "running" and tc_card.run_id:
                        # 幂等：已有运行中记录（如重入）
                        return tc_card.run
                    _bg_log.warning(
                        "start_run skip transition %s: status=%s outcome=%s",
                        client_tid,
                        tc_card.status,
                        tc_card.outcome or "",
                    )
                except sm.InvalidTransition as e:
                    _bg_log.warning("start_run transition %s: %s", client_tid, e)
                except Exception:
                    _bg_log.exception("start_run %s failed", client_tid)
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
        dev_serial = serial or (runner.device_conn.serial if hasattr(runner, "device_conn") and hasattr(runner.device_conn, "serial") else "?")
        await test_callbacks.on_log(run_id, f"📱 当前设备 ID: {dev_serial}")
        await test_callbacks.on_log(run_id, f"循环 {loop_count} 轮 · 共 {len(test_cases)} 个用例")
        for tc in test_cases:
            step_count = len(tc.steps_data) if tc.steps_data else 0
            await test_callbacks.on_log(run_id, f"  · 用例 [{tc.id}] {tc.title} ({step_count} 步)")
        await test_callbacks.on_log(run_id, "────────────────────")

        run_model = await runner.run(run_id, test_cases, loop_count, interval_seconds)
        run_completed = True

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
                    _bg_log.warning("finalize transition %s: %s", client_tid, e)
                except Exception:
                    _bg_log.exception("finalize %s failed", client_tid)
            else:
                # No TaskCard — finalize the run record standalone.
                run_record.status = run_model.status.value
                run_record.summary = run_model.summary
                run_record.finished_at = datetime.now().isoformat()
                run_record.save(update_fields=["status", "summary", "finished_at"])

        await finalize()
        _run_client_task.pop(run_id, None)

    except Exception as e:
        import traceback
        _log.error(f"Test run {run_id} error: {e}\n{traceback.format_exc()}")
        await test_callbacks.on_device_error(run_id, str(e))
        # Drive TaskCard to error via the state machine; always finalize the run
        # record as FAILED when the card can't take the transition.

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
                    _bg_log.warning("mark_failed transition %s: %s", client_tid, e)
                except Exception:
                    _bg_log.exception("mark_failed %s failed", client_tid)
            # TaskCard terminal/missing or transition failed → finalize run record.
            if run_record:
                run_record.status = "FAILED"
                run_record.finished_at = datetime.now().isoformat()
                run_record.save(update_fields=["status", "finished_at"])

        try:
            await mark_failed()
        except Exception:
            _bg_log.exception("mark_failed(%s) failed", run_id)
        _run_client_task.pop(run_id, None)
    finally:
        _log.info(f"_execute_tests finally: run_completed={run_completed} device={effective_serial}")
        mark_device_idle(effective_serial)
        # Release DB-level device occupation
        try:
            from .helpers import sync_to_async
            await sync_to_async(dp_release_device)(effective_serial, reason="manual")
            _log.info(f"_execute_tests dp_release_device OK: {effective_serial}")
        except Exception:
            _bg_log.exception("dp_release_device(%s) in finally failed", effective_serial)
        if effective_serial:
            _schedule_next_queued(effective_serial)
