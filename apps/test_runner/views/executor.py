"""Core test executor — _execute_tests.

生命周期编排: persist_run_start → runner.run() → persist_case_results → finalize_run
异常路径:       任意阶段异常 → mark_run_failed
清理 (finally):  cleanup_device
"""

import logging
import traceback

from apps.device_pool.api import release_device as dp_release_device

from ..callbacks import test_callbacks
from ..models import TestRunRecord
from ..runner import _active_runs, mark_device_idle
from .execution_steps import (
    _finalize_run,
    _mark_run_failed,
    _persist_case_results,
    _persist_run_start,
)
from .helpers import (
    _bg_log,
    _run_client_task,
    _schedule_next_queued,
    sync_to_async,
)

# Serial values for task types that don't require physical devices
_VIRTUAL_SERIALS = frozenset({"api", "web"})

_log = logging.getLogger("test_runner.bg")


# ── Helpers ───────────────────────────────────────────────────────


def _resolve_device_serial(runner, serial: str = "", fallback: str = "") -> str:
    """从 runner 实例解析设备序列号。"""
    if serial:
        return serial
    if hasattr(runner, "device_conn") and hasattr(runner.device_conn, "serial"):
        return runner.device_conn.serial
    if hasattr(runner, "device"):
        return getattr(runner.device, "serial", None) or fallback
    return fallback


# ── Cleanup ───────────────────────────────────────────────────────


async def _cleanup_device(effective_serial: str) -> None:
    """释放物理设备并调度下一个排队任务。虚拟设备 (api/web) 跳过。"""
    if effective_serial in _VIRTUAL_SERIALS:
        return

    mark_device_idle(effective_serial)
    try:
        await sync_to_async(dp_release_device)(effective_serial, reason="manual")
        _log.info("_execute_tests dp_release_device OK: %s", effective_serial)
    except Exception:
        _bg_log.exception("dp_release_device(%s) in cleanup failed", effective_serial)

    if effective_serial:
        _schedule_next_queued(effective_serial)


# ── Orchestrator ──────────────────────────────────────────────────


async def _execute_tests(
    run_id: str,
    runner,
    test_cases: list,
    loop_count: int,
    interval_seconds: int = 5,
    serial: str = "",
):
    """编排一次测试执行的完整生命周期。

    生命周期:
      persist_run_start → runner.run() → persist_case_results → finalize_run
    异常路径:
      任意阶段异常 → mark_run_failed
    清理 (finally):
      cleanup_device

    结果通过 WebSocket 实时推送 + DB 持久化，本函数不返回值。
    """
    effective_serial = _resolve_device_serial(runner, serial)
    client_tid: str = _run_client_task.get(run_id, "")
    dev_serial: str = _resolve_device_serial(runner, serial, fallback="")

    run_record: TestRunRecord | None = None
    run_model = None
    run_completed: bool = False

    try:
        _log.info(
            "_execute_tests 开始: %s client_tid=%s serial=%s",
            run_id,
            client_tid,
            dev_serial,
        )

        # ── 1. 启动记录 ──
        run_record = await _persist_run_start(
            client_tid,
            run_id,
            dev_serial,
            test_cases,
            loop_count,
        )
        _log.info(
            "_execute_tests run_record=%s status=%s",
            run_record.id if run_record else "None",
            run_record.status if run_record else "N/A",
        )

        # ── 2. 通知前端执行计划 ──
        dev_label = _resolve_device_serial(runner, serial, fallback="?")
        await test_callbacks.on_log(run_id, f"📱 当前设备 ID: {dev_label}")
        await test_callbacks.on_log(
            run_id,
            f"循环 {loop_count} 轮 · 共 {len(test_cases)} 个用例",
        )
        for tc in test_cases:
            step_count = len(tc.steps_data) if tc.steps_data else 0
            await test_callbacks.on_log(
                run_id,
                f"  · 用例 [{tc.id}] {tc.title} ({step_count} 步)",
            )
        await test_callbacks.on_log(run_id, "────────────────────")

        # ── 3. 执行 ──
        try:
            _log.info(
                "_execute_tests: calling runner.run(%d cases, %d loops)",
                len(test_cases),
                loop_count,
            )
            run_model = await runner.run(
                run_id,
                test_cases,
                loop_count,
                interval_seconds,
            )
            _log.info(
                "_execute_tests: runner.run returned status=%s case_results=%d",
                run_model.status,
                len(run_model.case_results),
            )
        except Exception as e:
            _log.error(
                "_execute_tests runner.run() crashed: %s\n%s",
                e,
                traceback.format_exc(),
            )
            # 尝试从 active runs 中恢复已完成的 case 结果
            run_model = None
            if run_id in _active_runs:
                state = _active_runs[run_id]
                if hasattr(state, "run_model") and state.run_model:
                    run_model = state.run_model
                    _log.info(
                        "_execute_tests: recovered partial results from crashed run %s", run_id
                    )

        run_completed = True

        # ── 4. 持久化结果 ──
        await _persist_case_results(run_record, run_model)

        # ── 5. 终态收敛 ──
        await _finalize_run(run_record, run_model, client_tid)

        _run_client_task.pop(run_id, None)

    except Exception as e:
        _log.error(
            "Test run %s error: %s\n%s",
            run_id,
            e,
            traceback.format_exc(),
        )
        await test_callbacks.on_device_error(run_id, str(e))

        # 尽力标记失败——自身不抛异常
        try:
            await _mark_run_failed(run_record, run_model, client_tid)
        except Exception:
            _bg_log.exception("mark_failed(%s) failed", run_id)

        _run_client_task.pop(run_id, None)

    finally:
        _log.info(
            "_execute_tests finally: run_completed=%s device=%s",
            run_completed,
            effective_serial,
        )
        await _cleanup_device(effective_serial)
