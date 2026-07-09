"""
Async test runner — executes selected test cases sequentially with loop_count iterations.

Device isolation: acquires device via device_pool.api.acquire_device before execution
and releases it in finally. The DB-level Device.status=BUSY + Device.occupied_by
are the source of truth for cross-module device availability checks.
"""
import time
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from models.test_models import TestCaseDef, TestResult, TestRun, TestRunStatus
from .adapter import DeviceAdapter
from .executor import StepExecutor
from apps.device_pool.api import acquire_device, release_device

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
EXPORT_DIR = BASE_DIR / "exports"


# Dedicated thread pool for uiautomator2 operations — isolated from Django's
# sync_to_async pool to prevent CurrentThreadExecutor corruption from breaking
# all ORM operations.
import concurrent.futures
_u2_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix='u2')


async def _safe_run_in_executor(loop, func, *args, error_msg="executor failed"):
    """Run a sync function in executor with protection against CurrentThreadExecutor quit.

    Uses a dedicated thread pool (_u2_executor) instead of the default (None)
    to prevent uiautomator2's CurrentThreadExecutor from corrupting the shared
    thread pool used by Django's sync_to_async.
    """
    try:
        return await loop.run_in_executor(_u2_executor, func, *args)
    except RuntimeError as e:
        msg = str(e)
        if 'quit' in msg.lower() or 'broken' in msg.lower():
            raise ConnectionError(
                f"设备连接已断开 (executor quit): {error_msg}"
            ) from e
        raise
    except BrokenPipeError as e:
        raise ConnectionError(
            f"设备连接中断 (broken pipe): {error_msg}"
        ) from e
    except OSError as e:
        if getattr(e, 'errno', None) == 22:
            raise  # Invalid argument (e.g. bad filename) — don't wrap
        raise ConnectionError(
            f"设备 IO 错误: {error_msg}: {e}"
        ) from e


class TestRunnerCallback:
    """Async callback interface for test runner progress."""

    async def on_log(self, run_id: str, message: str):
        """A log message was emitted."""

    async def on_case_started(self, run_id: str, case_id: str, case_title: str, loop_count: int):
        """A test case is starting."""

    async def on_iteration_result(self, run_id: str, case_id: str,
                                   iteration: int, result: str, duration_ms: float):
        """A single iteration completed."""

    async def on_case_finished(self, run_id: str, case_id: str,
                                pass_count: int, fail_count: int, rate: str):
        """A test case finished all iterations."""

    async def on_run_finished(self, run_id: str, summary: dict,
                               csv_path: str, log_path: str):
        """All test cases completed (or stopped)."""

    async def on_step_started(self, run_id: str, case_id: str,
                               iteration: int, step_index: int, total_steps: int,
                               step_type: str, description: str):
        """A step is about to execute."""

    async def on_step_result(self, run_id: str, case_id: str,
                              iteration: int, step_index: int, total_steps: int,
                              step_type: str, description: str, result: str):
        """A single step completed."""

    async def on_device_error(self, run_id: str, error: str):
        """Device connection failed."""


@dataclass
class _RunState:
    """Internal mutable state for a running test."""
    run_model: TestRun
    callback: TestRunnerCallback
    adapter: Optional[DeviceAdapter] = None
    is_running: bool = True
    all_results: list = field(default_factory=list)
    failure_details: list = field(default_factory=list)
    log_lines: list = field(default_factory=list)


# Global registry of active runs
_active_runs: dict[str, _RunState] = {}

# Device busy tracking — one device can only run one task at a time
_device_busy: set[str] = set()


def is_device_busy(serial: str) -> bool:
    """Check if a device is currently executing a task."""
    return serial in _device_busy


def mark_device_busy(serial: str):
    """Mark a device as busy (executing)."""
    _device_busy.add(serial)


def mark_device_idle(serial: str):
    """Mark a device as idle (available for new tasks)."""
    _device_busy.discard(serial)


class TestRunner:
    """Executes test cases asynchronously against a connected device."""

    def __init__(self, device, package_name: str = "",
                 callback: TestRunnerCallback = None):
        self.device = device
        self.package_name = package_name
        self.callback = callback or TestRunnerCallback()

    async def run(self, run_id: str, test_cases: list[TestCaseDef],
                  loop_count: int = 3, interval_seconds: int = 5) -> TestRun:
        """Run all test cases sequentially."""
        run_model = TestRun(
            run_id=run_id,
            device_serial=self.device.serial,
            status=TestRunStatus.RUNNING,
            selected_cases=[tc.id for tc in test_cases],
            loop_count=loop_count,
            started_at=datetime.now().isoformat(),
        )

        state = _RunState(run_model=run_model, callback=self.callback)
        _active_runs[run_id] = state

        # DB-level device occupation — source of truth for cross-module checks
        acquire_device(self.device.serial, user_id=f"runner-{self.device.serial}", timeout=3600)
        # Memory-level fast check for same-process scheduling
        mark_device_busy(self.device.serial)

        loop = asyncio.get_event_loop()

        def create_adapter():
            return DeviceAdapter(
                self.device, package_name=self.package_name,
                logger=lambda msg, l=loop: self._sync_log(state, msg, l),
                should_stop=lambda: not state.is_running,
            )

        adapter = await _safe_run_in_executor(loop, create_adapter,
                                               error_msg="创建设备适配器失败")
        state.adapter = adapter
        executor = StepExecutor(adapter)

        try:
            from apps.report_generator.api import ReportGenerator
            csv_paths = []
            log_path = ""

            for case in test_cases:
                if not state.is_running:
                    break
                await self.callback.on_case_started(
                    run_id, case.id, case.title, loop_count)
                await self._run_case(state, case, executor, loop_count, interval_seconds)
                # Save CSV per case (append mode)
                if state.all_results:
                    last = state.all_results[-1]
                    fp = await _safe_run_in_executor(
                        loop, ReportGenerator.save_csv,
                        last, state.failure_details,
                        error_msg="保存 CSV 报告失败")
                    csv_paths.append(fp)

            if state.all_results:
                case_name = state.all_results[0]["case_title"] if state.all_results else ""
                log_path = await _safe_run_in_executor(
                    loop, ReportGenerator.save_log,
                    run_id, state.log_lines, case_name,
                    error_msg="保存执行日志失败")

            run_model.status = (TestRunStatus.COMPLETED
                                if state.is_running
                                else TestRunStatus.STOPPED)
            run_model.case_results = [r for r in run_model.case_results]
            run_model.csv_path = "; ".join(csv_paths)
            run_model.log_path = log_path
            run_model.finished_at = datetime.now().isoformat()

            for r in state.all_results:
                run_model.summary[r["case_title"]] = {
                    "pass": r["pass"], "fail": r["fail"], "rate": r["rate"],
                }

            await self.callback.on_run_finished(
                run_id, run_model.summary, csv_path, log_path)

        except Exception as e:
            await self.callback.on_device_error(run_id, str(e))
            run_model.status = TestRunStatus.STOPPED
        finally:
            _active_runs.pop(run_id, None)
            mark_device_idle(self.device.serial)
            # Release DB-level device occupation
            try:
                release_device(self.device.serial, reason="manual")
            except Exception as e:
                print(f"[runner] WARNING: release_device failed for {self.device.serial}: {e}")

        return run_model

    async def _run_case(self, state: _RunState, case: TestCaseDef,
                        executor: StepExecutor, loop_count: int,
                        interval_seconds: int = 5):
        loop = asyncio.get_event_loop()
        pass_count = 0
        fail_count = 0
        actual_count = 0

        for i in range(1, loop_count + 1):
            if not state.is_running:
                break

            state.adapter.clear_log_buffer()
            start = time.time()

            step_count = len(case.steps_data) if case.steps_data else 0
            state.adapter.log(f'━━━ 第 {i}/{loop_count} 轮 ({step_count} 个步骤) ━━━')

            # Wire step callbacks to broadcast results (sync → async bridge)
            def _make_step_cb(iter_no):
                def cb(si, total, st, desc, r):
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.callback.on_step_result(
                                state.run_model.run_id, case.id, iter_no,
                                si, total, st, desc, r,
                            ), loop)
                    except Exception as e:
                        print(f"[runner] on_step_result callback failed: {e}")
                return cb

            def _make_step_started_cb(iter_no):
                def cb(si, total, st, desc):
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.callback.on_step_started(
                                state.run_model.run_id, case.id, iter_no,
                                si, total, st, desc,
                            ), loop)
                    except Exception as e:
                        print(f"[runner] on_step_started callback failed: {e}")
                return cb

            state.adapter._step_callback = _make_step_cb(i)
            state.adapter._step_started_callback = _make_step_started_cb(i)

            if case.steps_data:
                try:
                    result = await _safe_run_in_executor(
                        loop, executor.execute_all, case.steps_data,
                        error_msg=f"执行用例 '{case.title}' 步骤时设备断连")
                except ConnectionError as e:
                    state.adapter.log(f'💥 设备连接错误: {e}')
                    await self.callback.on_device_error(state.run_model.run_id, str(e))
                    state.is_running = False
                    break
            else:
                # No steps: treat as pass (empty sequence always succeeds)
                state.adapter.log(f'用例 "{case.title}" 无步骤，直接通过')
                result = "pass"

            elapsed = (time.time() - start) * 1000
            actual_count = i

            if result == "stopped":
                await self.callback.on_log(state.run_model.run_id, f"  第{i}轮: 已中断")
                break

            if result == "pass":
                pass_count += 1
                state.adapter.log(f'  ✔ 第{i}轮 通过 ({elapsed:.0f}ms)')
            else:
                fail_count += 1
                state.adapter.log(f'  ✘ 第{i}轮 失败 ({elapsed:.0f}ms)')
                state.failure_details.append({
                    "case_title": case.title, "iteration": i,
                    "elapsed_ms": f"{elapsed:.0f}",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "log": state.adapter.get_log_buffer(),
                })

            await self.callback.on_iteration_result(
                state.run_model.run_id, case.id, i, result, elapsed)

            if i < loop_count and state.is_running:
                await asyncio.sleep(interval_seconds)

        rate = f"{(pass_count / actual_count * 100):.1f}%" if actual_count > 0 else "0%"
        state.all_results.append({
            "case_title": case.title, "case_steps": case.steps,
            "planned": str(loop_count), "actual": str(actual_count),
            "pass": str(pass_count), "fail": str(fail_count), "rate": rate,
        })

        await self.callback.on_case_finished(
            state.run_model.run_id, case.id, pass_count, fail_count, rate)

    def _sync_log(self, state: _RunState, msg: str, loop=None):
        state.log_lines.append(msg)
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                state.callback.on_log(state.run_model.run_id, msg), loop)


def get_active_run(run_id: str) -> Optional[_RunState]:
    return _active_runs.get(run_id)


def stop_run(run_id: str) -> bool:
    state = _active_runs.get(run_id)
    if state:
        state.is_running = False
        return True
    return False


def list_active_runs() -> list[str]:
    return list(_active_runs.keys())
