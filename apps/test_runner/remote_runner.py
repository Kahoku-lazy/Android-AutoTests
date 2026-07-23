"""
RemoteTestRunner — unified async runner for API and Web test execution.

Replaces the near-identical ApiTestRunner and WebTestRunner with a single
parameterized class. Integrates with the same _execute_tests pipeline and
WsTestCallback used by the UI TestRunner.
"""
import asyncio
import time
from datetime import datetime
from models.test_models import TestCaseDef, TestResult, TestRun, TestRunStatus
from dataclasses import dataclass
from .runner import _active_runs


@dataclass
class _RemoteRunState:
    """Lightweight mutable state for stop signalling."""
    is_running: bool = True


class RemoteTestRunner:
    """Executes API or Web test cases asynchronously with WS callback integration.

    Parameters:
        adapter:       ApiAdapter or WebAdapter instance
        executor:      ApiExecutor or WebExecutor instance
        device_label:  "api" or "web" — used as virtual serial
        callback:      WsTestCallback singleton
        is_async_executor: True for WebExecutor (async execute_case), False for ApiExecutor
        cleanup:       Optional async callable invoked in finally (e.g. adapter.close for Web)
    """

    def __init__(self, adapter, executor, device_label: str = "api",
                 callback=None, is_async_executor: bool = False, cleanup=None):
        self.adapter = adapter
        self.executor = executor
        self.device_conn = _RemoteFakeDeviceConn(device_label)
        self.callback = callback
        self.package_name = ""
        self._is_async = is_async_executor
        self._cleanup = cleanup

    async def run(
        self,
        run_id: str,
        test_cases: list[TestCaseDef],
        loop_count: int = 3,
        interval_seconds: int = 5,
    ) -> TestRun:
        loop = asyncio.get_event_loop()
        state = _RemoteRunState()
        _active_runs[run_id] = state
        self.adapter._should_stop = lambda: not state.is_running
        run_model = TestRun(
            run_id=run_id,
            device_serial=self.device_conn.serial,
            status=TestRunStatus.RUNNING,
            selected_cases=[tc.id for tc in test_cases],
            loop_count=loop_count,
            started_at=datetime.now().isoformat(),
        )

        self._wire_callbacks(run_id, loop)
        hb_task = asyncio.create_task(self._heartbeat(run_id))

        try:
            for case in test_cases:
                if self.adapter.stopped():
                    break

                await self._emit("on_log", run_id, f"Starting: [{case.id}] {case.title}")
                await self._emit("on_case_started", run_id, case.id, case.title, loop_count)

                pass_count, fail_count = 0, 0

                for i in range(1, loop_count + 1):
                    if self.adapter.stopped():
                        break
                    # Re-wire step callbacks for this iteration (matching UI runner pattern)
                    self._wire_step_callbacks(run_id, case.id, i, loop)
                    self.adapter.clear_log_buffer()
                    start = time.time()

                    self.adapter.log(f"--- Iteration {i}/{loop_count} ---")
                    if self._is_async:
                        result = await self.executor.execute_case(case, iteration=i)
                    else:
                        result = self.executor.execute_case(case, iteration=i)

                    elapsed = (time.time() - start) * 1000
                    if result == "pass":
                        pass_count += 1
                    else:
                        fail_count += 1

                    run_model.case_results.append(TestResult(
                        case_id=case.id, case_title=case.title,
                        iteration=i, result=result, duration_ms=elapsed,
                        detail=self._last_log(),
                        case_type=case.task_type,
                    ))

                    await self._emit("on_iteration_result", run_id, case.id, i, result, elapsed)

                    if i < loop_count and not self.adapter.stopped():
                        await asyncio.sleep(interval_seconds)

                actual = pass_count + fail_count
                rate = f"{(pass_count / actual * 100):.1f}%" if actual > 0 else "0%"
                await self._emit("on_case_finished", run_id, case.id, pass_count, fail_count, rate)

            run_model.status = TestRunStatus.COMPLETED if not self.adapter.stopped() else TestRunStatus.STOPPED
            run_model.finished_at = datetime.now().isoformat()
            await self._emit("on_run_finished", run_id, run_model.summary, "")

        except Exception as e:
            run_model.status = TestRunStatus.STOPPED
            run_model.finished_at = datetime.now().isoformat()
            await self._emit("on_device_error", run_id, str(e))
        finally:
            _active_runs.pop(run_id, None)
            if hb_task:
                hb_task.cancel()
                try:
                    await hb_task
                except asyncio.CancelledError:
                    pass
            if self._cleanup:
                try:
                    await self._cleanup()
                except Exception:
                    pass

        return run_model

    def _last_log(self) -> str:
        buf = self.adapter.get_log_buffer()
        return buf[-1] if buf else ""

    async def _heartbeat(self, run_id: str, interval: float = 5.0):
        while True:
            await asyncio.sleep(interval)
            await self._emit("on_heartbeat", run_id)

    def _wire_callbacks(self, run_id: str, loop):
        """Initial wiring with defaults (overridden per-iteration)."""
        def noop(*args): pass
        self.executor._step_callback = noop
        self.executor._step_started_callback = noop

    def _wire_step_callbacks(self, run_id: str, case_id: str, iteration: int, loop):
        """Wire step callbacks for a specific case/iteration (matches UI runner pattern)."""
        def step_started(si, total, st, desc):
            asyncio.run_coroutine_threadsafe(
                self.callback.on_step_started(run_id, case_id, iteration, si, total, st, desc),
                loop,
            )

        def step_result(si, total, st, desc, r):
            asyncio.run_coroutine_threadsafe(
                self.callback.on_step_result(run_id, case_id, iteration, si, total, st, desc, r),
                loop,
            )

        self.executor._step_callback = step_result
        self.executor._step_started_callback = step_started

    async def _emit(self, method: str, *args):
        """Safely emit a callback event."""
        if self.callback is None:
            return
        try:
            fn = getattr(self.callback, method, None)
            if fn:
                await fn(*args)
        except Exception:
            pass


class _RemoteFakeDeviceConn:
    """Minimal object satisfying hasattr(runner, 'device_conn')."""
    def __init__(self, serial: str):
        self.serial = serial
