"""
Async test runner — executes selected test cases sequentially with loop_count iterations.

TREP v1.0: 纯执行单元。设备锁定由调度器在调用 run() 前完成，执行器不负责
设备生命周期管理。通过 TestRunnerCallback 上报进度，每 5s 发送心跳。
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
from .u2_recovery import (
    U2_CASE_RETRY_MAX,
    U2_RECONNECT_INTERVAL,
    check_u2_alive,
    is_u2_crash,
    wait_and_reconnect,
)

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

    async def on_run_started(self, run_id: str):
        """Pre-flight passed; execution is starting (frontend: 准备中 → 执行中)."""

    async def on_case_started(self, run_id: str, case_id: str, case_title: str, loop_count: int):
        """A test case is starting."""

    async def on_iteration_result(self, run_id: str, case_id: str,
                                   iteration: int, result: str, duration_ms: float):
        """A single iteration completed."""

    async def on_case_finished(self, run_id: str, case_id: str,
                                pass_count: int, fail_count: int, rate: str):
        """A test case finished all iterations."""

    async def on_run_finished(self, run_id: str, summary: dict,
                               log_path: str):
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

    async def on_heartbeat(self, run_id: str):
        """Periodic keep-alive signal (every 5s while run is active)."""


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

        # TREP v1.0: 设备锁定由调度器（views.py）在调用 run() 前完成。
        # 执行器不负责设备生命周期管理。

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

        # TREP v1.0: 每 5s 心跳，前端据此检测 WS 连接存活
        hb_task = None
        hb_task = asyncio.create_task(self._heartbeat(run_id, state))

        try:
            from apps.report_generator.api import ReportGenerator
            log_path = ""

            for case in test_cases:
                if not state.is_running:
                    break
                await self.callback.on_log(
                    run_id, f"🏃 开始运行用例: [{case.id}] {case.title}"
                )
                await self.callback.on_case_started(
                    run_id, case.id, case.title, loop_count)
                executor = await self._run_case(
                    state, case, executor, loop_count, interval_seconds,
                )
                if not state.is_running:
                    break

            if state.all_results:
                case_name = state.all_results[0]["case_title"] if state.all_results else ""
                log_path = await _safe_run_in_executor(
                    loop, ReportGenerator.save_log,
                    run_id, state.log_lines, case_name,
                    error_msg="保存执行日志失败")

            run_model.status = (TestRunStatus.COMPLETED
                                if state.is_running
                                else TestRunStatus.STOPPED)
            run_model.log_path = log_path
            run_model.finished_at = datetime.now().isoformat()

            for r in state.all_results:
                run_model.summary[r["case_title"]] = {
                    "pass": r["pass"], "fail": r["fail"], "rate": r["rate"],
                }

            await self.callback.on_run_finished(
                run_id, run_model.summary, log_path)

        except Exception as e:
            await self.callback.on_device_error(run_id, str(e))
            run_model.status = TestRunStatus.STOPPED
        finally:
            if hb_task is not None:
                hb_task.cancel()
                try:
                    await hb_task
                except asyncio.CancelledError:
                    pass
            _active_runs.pop(run_id, None)
            # TREP v1.0: 设备释放由调度器（views.py）在 _execute_tests.finally 中完成

        return run_model

    async def _heartbeat(self, run_id: str, state: _RunState, interval: float = 5.0):
        """TREP v1.0: 每 interval 秒发送心跳，前端 15s 无心跳 → 连接丢失指示。"""
        while state.is_running and run_id in _active_runs:
            await asyncio.sleep(interval)
            if run_id in _active_runs and state.is_running:
                await self.callback.on_heartbeat(run_id)

    def _wire_step_callbacks(self, state: _RunState, case: TestCaseDef, iteration: int, loop):
        """绑定步骤 WS 回调到当前 adapter。"""
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

        state.adapter._step_callback = _make_step_cb(iteration)
        state.adapter._step_started_callback = _make_step_started_cb(iteration)

    async def _recreate_adapter_executor(self, state: _RunState, loop) -> StepExecutor:
        """u2 重连后重建 adapter 与 executor。"""
        def create_adapter():
            return DeviceAdapter(
                self.device, package_name=self.package_name,
                logger=lambda msg, l=loop: self._sync_log(state, msg, l),
                should_stop=lambda: not state.is_running,
            )

        state.adapter = await _safe_run_in_executor(
            loop, create_adapter, error_msg="重建设备适配器失败",
        )
        return StepExecutor(state.adapter)

    async def _execute_iteration_with_retry(
        self,
        state: _RunState,
        case: TestCaseDef,
        executor: StepExecutor,
        iteration: int,
        loop,
    ) -> tuple[str, StepExecutor, bool]:
        """执行单轮步骤，u2 崩溃时最多重试 U2_CASE_RETRY_MAX 次。

        Returns:
            (result, executor, fatal_u2)
            - fatal_u2=True: u2 服务无法恢复，停止整个任务
        """
        if not case.steps_data:
            state.adapter.log(f'用例 "{case.title}" 无步骤，直接通过')
            return "pass", executor, False

        last_error = ""
        for attempt in range(1, U2_CASE_RETRY_MAX + 1):
            if not state.is_running:
                return "stopped", executor, False

            self._wire_step_callbacks(state, case, iteration, loop)

            try:
                if not check_u2_alive(self.device):
                    state.adapter.log(
                        f"⚠️ u2 连接不可用，尝试重连 ({attempt}/{U2_CASE_RETRY_MAX})..."
                    )
                    self.device = await _safe_run_in_executor(
                        loop,
                        wait_and_reconnect,
                        self.device.serial,
                        U2_RECONNECT_INTERVAL,
                        error_msg="u2 重连失败",
                    )
                    executor = await self._recreate_adapter_executor(state, loop)
                    self._wire_step_callbacks(state, case, iteration, loop)

                result = await _safe_run_in_executor(
                    loop, executor.execute_all, case.steps_data,
                    error_msg=f"执行用例 '{case.title}' 步骤时设备断连",
                )
                return result, executor, False

            except Exception as e:
                if not is_u2_crash(e):
                    raise
                last_error = str(e)
                state.adapter.log(
                    f"⚠️ u2 崩溃 ({attempt}/{U2_CASE_RETRY_MAX}): {last_error}"
                )
                if attempt >= U2_CASE_RETRY_MAX:
                    break
                try:
                    self.device = await _safe_run_in_executor(
                        loop,
                        wait_and_reconnect,
                        self.device.serial,
                        U2_RECONNECT_INTERVAL,
                        error_msg="u2 重连失败",
                    )
                    executor = await self._recreate_adapter_executor(state, loop)
                except Exception as reconnect_err:
                    state.adapter.log(f"  重连失败: {reconnect_err}")

        if not check_u2_alive(self.device):
            state.adapter.log(
                f"💥 u2 服务 {U2_CASE_RETRY_MAX} 次重试后仍无法恢复，停止当前任务"
            )
            await self.callback.on_device_error(
                state.run_model.run_id,
                f"u2 服务无法恢复: {last_error}",
            )
            return "fail", executor, True

        state.adapter.log(
            f"✘ 用例「{case.title}」第 {iteration} 轮："
            f"u2 崩溃 {U2_CASE_RETRY_MAX} 次后仍未完成，标记失败，继续下一条用例"
        )
        return "fail", executor, False

    async def _run_case(self, state: _RunState, case: TestCaseDef,
                        executor: StepExecutor, loop_count: int,
                        interval_seconds: int = 5) -> StepExecutor:
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

            result, executor, fatal_u2 = await self._execute_iteration_with_retry(
                state, case, executor, i, loop,
            )

            if fatal_u2:
                state.is_running = False
                fail_count += 1
                actual_count = i
                elapsed = (time.time() - start) * 1000
                state.failure_details.append({
                    "case_title": case.title, "iteration": i,
                    "elapsed_ms": f"{elapsed:.0f}",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "log": state.adapter.get_log_buffer(),
                })
                await self.callback.on_iteration_result(
                    state.run_model.run_id, case.id, i, "fail", elapsed)
                break

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

        return executor

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
