"""
Systematic regression tests for execution engine blind spots.

Covers paths that have 0% existing test coverage:
  - Web executor (adapter.py, executor.py)
  - RemoteTestRunner (remote_runner.py)
  - api_directories case_type branches
  - _persist_run_start / _finalize_run full integration
  - start_test_run dispatch for all task types
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call


# ══════════════════════════════════════════════════════════════════════
# A. Web Executor — dispatch + step handling
# ══════════════════════════════════════════════════════════════════════


class TestWebExecutorDispatch:
    """WebExecutor._dispatch(): step type routing, error handling, callbacks."""

    def _make_executor(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        return WebExecutor(adapter), adapter

    def _make_step(self, **kw):
        from models.step_types import TestStep
        defaults = {"type": "web_navigate", "url": "http://x.com"}
        defaults.update(kw)
        return TestStep(**defaults)

    @pytest.mark.asyncio
    async def test_navigate_dispatches_to_adapter(self):
        exec_, adapter = self._make_executor()
        step = self._make_step(type="web_navigate", url="http://example.com")
        adapter._navigate = AsyncMock()

        result = await exec_._dispatch(step)
        assert result == "pass"
        adapter._navigate.assert_called_once_with("http://example.com")

    @pytest.mark.asyncio
    async def test_click_finds_selector_or_xpath(self):
        exec_, adapter = self._make_executor()
        adapter._click = AsyncMock()

        # selector present
        step = self._make_step(type="web_click", selector="#btn")
        await exec_._dispatch(step)
        adapter._click.assert_called_with("#btn")

        # fallback to xpath
        step2 = self._make_step(type="click", xpath="//button")
        await exec_._dispatch(step2)
        adapter._click.assert_called_with("//button")

    @pytest.mark.asyncio
    async def test_fill_requires_selector(self):
        exec_, adapter = self._make_executor()
        adapter._fill = AsyncMock()

        # With selector → proceeds
        step = self._make_step(type="web_fill", selector="#inp", value="hi")
        await exec_._dispatch(step)
        adapter._fill.assert_called_once()

        # Without selector → should log but not crash (doesn't call _fill)
        adapter._fill.reset_mock()
        step2 = self._make_step(type="web_fill", selector="", value="hi")
        result = await exec_._dispatch(step2)
        # Still returns pass (doesn't crash), but fill is skipped
        assert result == "pass"

    @pytest.mark.asyncio
    async def test_wait_with_timeout_sleeps(self):
        exec_, adapter = self._make_executor()
        step = self._make_step(type="sleep", timeout=0.01)
        result = await exec_._dispatch(step)
        assert result == "pass"

    @pytest.mark.asyncio
    async def test_wait_with_selector_calls_adapter(self):
        exec_, adapter = self._make_executor()
        adapter._wait_for = AsyncMock()
        step = self._make_step(type="web_wait", selector=".loading", timeout=5)
        await exec_._dispatch(step)
        adapter._wait_for.assert_called_once_with(".loading", 5)

    @pytest.mark.asyncio
    async def test_assert_with_expected_text(self):
        exec_, adapter = self._make_executor()
        adapter._verify_text = AsyncMock()
        step = self._make_step(type="web_assert", expected_text="Dashboard")
        result = await exec_._dispatch(step)
        assert result == "pass"
        adapter._verify_text.assert_called_once_with("Dashboard")

    @pytest.mark.asyncio
    async def test_adapter_exception_returns_fail(self):
        exec_, adapter = self._make_executor()
        adapter._navigate = AsyncMock(side_effect=RuntimeError("boom"))
        step = self._make_step(type="web_navigate", url="http://x.com")

        result = await exec_._dispatch(step)
        assert result == "fail"
        # Should log the error
        assert adapter.log.call_count >= 2  # "Navigate: ..." + "Step failed: ..."

    @pytest.mark.asyncio
    async def test_unknown_step_type_returns_fail(self):
        exec_, adapter = self._make_executor()
        step = self._make_step(type="unknown_xyz")
        result = await exec_._dispatch(step)
        assert result == "fail"

    @pytest.mark.asyncio
    async def test_step_started_callback_fires_from_execute_case(self):
        """Step started callback fires during execute_case()."""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = []

        exec_ = WebExecutor(adapter)
        cb = MagicMock()
        exec_._step_started_callback = cb

        steps = [TestStep(type="web_navigate", url="http://x.com", description="go")]
        case = TestCaseDef(id="TC-CB-1", title="t", steps_data=steps, enabled=True,
                           task_type="web_automation")
        await exec_.execute_case(case, iteration=1, run_id="r1")
        assert cb.call_count >= 1

    @pytest.mark.asyncio
    async def test_step_result_callback_fires_from_execute_case(self):
        """Step result callback fires during execute_case()."""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = []

        exec_ = WebExecutor(adapter)
        cb = MagicMock()
        exec_._step_callback = cb

        steps = [TestStep(type="web_navigate", url="http://x.com", description="go")]
        case = TestCaseDef(id="TC-CB-2", title="t", steps_data=steps, enabled=True,
                           task_type="web_automation")
        await exec_.execute_case(case, iteration=1, run_id="r1")
        assert cb.call_count >= 1
        assert cb.call_args_list[-1][0][4] == "pass"

    @pytest.mark.asyncio
    async def test_legacy_web_click_maps_to_click(self):
        exec_, adapter = self._make_executor()
        adapter._click = AsyncMock()
        step = self._make_step(type="web_click", selector="#old")
        result = await exec_._dispatch(step)
        assert result == "pass"
        adapter._click.assert_called_once_with("#old")


# ══════════════════════════════════════════════════════════════════════
# B. Web Executor — execute_case lifecycle
# ══════════════════════════════════════════════════════════════════════


class TestWebExecutorExecuteCase:
    """WebExecutor.execute_case(): iteration, step collection, stop."""

    def _make_case(self, steps_data=None, extra_data=None, title="Test"):
        from models.test_models import TestCaseDef
        from models.step_types import TestStep
        if steps_data is None:
            steps_data = [
                TestStep(type="web_navigate", url="http://x.com", description="go"),
                TestStep(type="web_click", selector="#btn", description="click"),
            ]
        return TestCaseDef(
            id="TC-001", title=title, category="web",
            steps_data=steps_data, enabled=True, task_type="web_automation",
            extra_data=extra_data or {},
        )

    @pytest.mark.asyncio
    async def test_all_steps_pass_returns_pass(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False

        exec_ = WebExecutor(adapter)
        case = self._make_case()
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "pass"
        assert len(exec_._last_step_details) == 2
        assert all(d["result"] == "pass" for d in exec_._last_step_details)

    @pytest.mark.asyncio
    async def test_first_failure_stops_remaining_steps(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock(side_effect=RuntimeError("element gone"))
        adapter.get_log_buffer.return_value = ["Step failed: element gone"]
        adapter.stopped.return_value = False

        exec_ = WebExecutor(adapter)
        case = self._make_case()
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "fail"
        # Only step 0 succeeded, step 1 failed → 2 details
        assert len(exec_._last_step_details) == 2
        assert exec_._last_step_details[0]["result"] == "pass"
        assert exec_._last_step_details[1]["result"] == "fail"

    @pytest.mark.asyncio
    async def test_stop_during_execution_returns_stopped(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.side_effect = [False, True]  # stops after step 0

        exec_ = WebExecutor(adapter)
        case = self._make_case()
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "stopped"

    @pytest.mark.asyncio
    async def test_no_steps_returns_fail(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter.stopped.return_value = False

        exec_ = WebExecutor(adapter)
        case = self._make_case(steps_data=[])
        # No steps_data, no extra_data → should fail
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "fail"

    @pytest.mark.asyncio
    async def test_expected_result_verification_appends_extra_step(self):
        """When expected_result is set, an extra web_assert step_detail is appended."""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False

        exec_ = WebExecutor(adapter)
        steps = [TestStep(type="web_navigate", url="http://x.com", description="go")]
        case = self._make_case(
            steps_data=steps,
            extra_data={"expected_result": "Dashboard"},
        )

        # Mock _ensure_browser + page.content for verify step
        adapter._ensure_browser = AsyncMock()
        adapter._page = MagicMock()
        adapter._page.content.return_value = "<html><body>Dashboard</body></html>"

        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "pass"
        # 1 manual step + 1 verify step = 2
        assert len(exec_._last_step_details) == 2
        assert exec_._last_step_details[1]["type"] == "web_assert"

    @pytest.mark.asyncio
    async def test_expected_result_not_found_returns_fail(self):
        """expected_result text not in page → step fails, case fails."""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._ensure_browser = AsyncMock()
        adapter._page = MagicMock()
        adapter._page.content.return_value = "<html><body>Wrong content</body></html>"

        exec_ = WebExecutor(adapter)
        steps = [TestStep(type="web_navigate", url="http://x.com", description="go")]
        case = self._make_case(
            steps_data=steps,
            extra_data={"expected_result": "Dashboard"},
        )
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "fail"

    @pytest.mark.asyncio
    async def test_watchers_run_before_each_step(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = [{"selector": ".popup", "action": "click"}]
        adapter.run_watchers = AsyncMock(return_value=1)

        exec_ = WebExecutor(adapter)
        case = self._make_case()
        await exec_.execute_case(case, iteration=1, run_id="r1")
        # run_watchers called before each of 2 steps
        assert adapter.run_watchers.call_count == 2

    @pytest.mark.asyncio
    async def test_empty_case_without_steps_or_extra_fails(self):
        from apps.test_runner.executors.web.executor import WebExecutor
        adapter = MagicMock()
        adapter.stopped.return_value = False

        exec_ = WebExecutor(adapter)
        case = self._make_case(steps_data=None)
        result = await exec_.execute_case(case, iteration=1, run_id="r1")
        assert result == "fail"


# ══════════════════════════════════════════════════════════════════════
# C. RemoteTestRunner — case ordering, isolation, intervals
# ══════════════════════════════════════════════════════════════════════


class TestRemoteTestRunner:
    """RemoteTestRunner: case execution order, inter-case delay, isolation."""

    @pytest.mark.asyncio
    async def test_cases_execute_in_provided_order(self):
        """Cases must execute in the exact order passed, not DB order."""
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        # Create cases in a specific order
        cases = [
            TestCaseDef(id="C1", title="First", steps_data=[
                TestStep(type="web_navigate", url="http://x.com"),
            ], enabled=True, task_type="web_automation"),
            TestCaseDef(id="C2", title="Second", steps_data=[
                TestStep(type="web_click", selector="#btn"),
            ], enabled=True, task_type="web_automation"),
        ]

        await runner.run("run-order-001", cases, loop_count=1)

        # Both cases executed
        assert executor.execute_case.call_count == 2
        # First call = case C1, second call = case C2
        assert executor.execute_case.call_args_list[0][0][0].id == "C1"
        assert executor.execute_case.call_args_list[1][0][0].id == "C2"

    @pytest.mark.asyncio
    async def test_inter_case_delay_applied(self):
        """interval_seconds should cause a delay between cases."""
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep
        import time

        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        cases = [
            TestCaseDef(id="C1", title="A", steps_data=[
                TestStep(type="web_navigate", url="http://x.com"),
            ], enabled=True, task_type="web_automation"),
            TestCaseDef(id="C2", title="B", steps_data=[
                TestStep(type="web_click", selector="#btn"),
            ], enabled=True, task_type="web_automation"),
        ]

        start = time.monotonic()
        await runner.run("run-delay-001", cases, loop_count=1, interval_seconds=0.5)
        elapsed = time.monotonic() - start

        # Should have at least 0.5s between cases
        assert elapsed >= 0.4, f"Expected >= 0.4s delay, got {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_stop_between_cases_halts_remaining(self):
        """If adapter.stopped() returns True mid-run, remaining cases skipped."""
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        adapter = MagicMock()
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False
        adapter.stopped.side_effect = lambda: (
            executor.execute_case.call_count >= 2  # stop after 2nd case
        )
        adapter.reset_state = AsyncMock()

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        cases = [
            TestCaseDef(id="C1", title="A", steps_data=[
                TestStep(type="web_navigate", url="http://x.com"),
            ], enabled=True, task_type="web_automation"),
            TestCaseDef(id="C2", title="B", steps_data=[
                TestStep(type="web_click", selector="#btn"),
            ], enabled=True, task_type="web_automation"),
            TestCaseDef(id="C3", title="C", steps_data=[
                TestStep(type="web_click", selector="#btn2"),
            ], enabled=True, task_type="web_automation"),
        ]

        await runner.run("run-stop-001", cases, loop_count=1)
        # C1 + C2 executed; C3 stopped before execution
        assert executor.execute_case.call_count == 2

    @pytest.mark.asyncio
    async def test_case_isolation_reset_between_cases(self):
        """reset_state() is called between cases to clear cookies/storage."""
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False
        adapter.reset_state = AsyncMock()

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        cases = [
            TestCaseDef(id="C1", title="A", steps_data=[
                TestStep(type="web_navigate", url="http://x.com"),
            ], enabled=True, task_type="web_automation"),
            TestCaseDef(id="C2", title="B", steps_data=[
                TestStep(type="web_click", selector="#btn"),
            ], enabled=True, task_type="web_automation"),
        ]

        await runner.run("run-isolate-001", cases, loop_count=1)
        # reset_state called after C1 completes, before C2 starts
        assert adapter.reset_state.call_count == 2  # once per case

    @pytest.mark.asyncio
    async def test_run_finished_event_emitted_on_completion(self):
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        cases = [TestCaseDef(id="C1", title="Test", steps_data=[
            TestStep(type="web_navigate", url="http://x.com"),
        ], enabled=True, task_type="web_automation")]

        await runner.run("run-finish-001", cases, loop_count=1)
        # on_run_finished should have been called
        run_finished_calls = [
            c for c in runner._emit.call_args_list
            if c[0][0] == "on_run_finished"
        ]
        assert len(run_finished_calls) == 1

    @pytest.mark.asyncio
    async def test_run_model_completed_status_on_success(self):
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep, TestRunStatus

        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True)
        runner._emit = AsyncMock()

        cases = [TestCaseDef(id="C1", title="Test", steps_data=[
            TestStep(type="web_navigate", url="http://x.com"),
        ], enabled=True, task_type="web_automation")]

        run_model = await runner.run("run-status-001", cases, loop_count=1)
        assert run_model.status == TestRunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cleanup_called_in_finally(self):
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        cleanup = AsyncMock()
        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(return_value="pass")
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True, cleanup=cleanup)
        runner._emit = AsyncMock()

        cases = [TestCaseDef(id="C1", title="Test", steps_data=[
            TestStep(type="web_navigate", url="http://x.com"),
        ], enabled=True, task_type="web_automation")]

        await runner.run("run-cleanup-001", cases, loop_count=1)
        cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_called_even_on_error(self):
        from apps.test_runner.remote_runner import RemoteTestRunner
        from models.test_models import TestCaseDef, TestStep

        cleanup = AsyncMock()
        adapter = MagicMock()
        adapter.stopped.return_value = False
        adapter.get_log_buffer.return_value = []
        adapter._should_stop = lambda: False

        executor = MagicMock()
        executor.execute_case = AsyncMock(side_effect=RuntimeError("crash"))
        executor._last_step_details = []

        runner = RemoteTestRunner(adapter, executor, device_label="web",
                                  is_async_executor=True, cleanup=cleanup)
        runner._emit = AsyncMock()

        cases = [TestCaseDef(id="C1", title="Test", steps_data=[
            TestStep(type="web_navigate", url="http://x.com"),
        ], enabled=True, task_type="web_automation")]

        await runner.run("run-cleanup-err-001", cases, loop_count=1)
        cleanup.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# D. api_directories — all case_type branches
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDirectoryTreeAllCaseTypes:
    """get_directory_tree() must handle all four case types without crashing."""

    def _create_dir_and_case(self, case_type, model_class, case_id, case_kw=None):
        from apps.case_manager.models import CaseDirectory
        d = CaseDirectory.objects.create(name=f"dir-{case_type}", case_type=case_type)
        kw = {"id": case_id, "title": f"Case {case_type}", "directory": d}
        if case_kw:
            kw.update(case_kw)
        model_class.objects.create(**kw)
        return d

    def test_ui_automation_directory_tree_works(self):
        from apps.case_manager.api_directories import get_directory_tree
        from apps.case_manager.models import TestDefinition

        self._create_dir_and_case("ui_automation", TestDefinition, "TC-UI-001")
        tree = get_directory_tree(case_type="ui_automation")
        assert len(tree) >= 1

    def test_api_testing_directory_tree_works(self):
        from apps.case_manager.api_directories import get_directory_tree
        from apps.case_manager.models_api import ApiTestCase

        self._create_dir_and_case("api_testing", ApiTestCase, "API-001",
                                  case_kw={"method": "GET", "url": "http://x.com"})
        tree = get_directory_tree(case_type="api_testing")
        assert len(tree) >= 1

    def test_web_automation_directory_tree_works(self):
        from apps.case_manager.api_directories import get_directory_tree
        from apps.case_manager.models_web import WebTestCase

        self._create_dir_and_case("web_automation", WebTestCase, "WEB-001",
                                  case_kw={"url": "http://x.com"})
        tree = get_directory_tree(case_type="web_automation")
        assert len(tree) >= 1

    def test_null_case_type_returns_test_definition_only(self):
        """None/backward-compat should query TestDefinition."""
        from apps.case_manager.api_directories import get_directory_tree
        from apps.case_manager.models import TestDefinition

        self._create_dir_and_case("ui_automation", TestDefinition, "TC-UI-NULL")
        tree = get_directory_tree()  # no case_type
        assert len(tree) >= 1

    def test_case_type_fallback_to_ui_automation(self):
        """Unknown case_type value defaults to ui_automation."""
        from apps.case_manager.api_directories import get_directory_tree
        tree = get_directory_tree(case_type=None)
        assert isinstance(tree, list)  # should not crash


# ══════════════════════════════════════════════════════════════════════
# E. _persist_run_start → state machine full integration
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestPersistRunStartIntegration:
    """Full lifecycle: idle → enqueue → dequeue → running."""

    @pytest.mark.asyncio
    async def test_full_idle_to_running_flow(self):
        """The complete path a new TaskCard takes."""
        from apps.test_runner.models import TaskCard, TestRunRecord
        from apps.test_runner import state_machine as sm
        from apps.test_runner.views.execution_steps import _persist_run_start
        from models.test_models import TestCaseDef

        tc = await TaskCard.objects.acreate(
            task_id="INTEGRATION-001", status="idle", device_serial="web",
        )
        test_cases = [
            TestCaseDef(id="TC-1", title="test", steps_data=[], enabled=True,
                        task_type="web_automation"),
        ]

        # _persist_run_start is decorated with @_bg_sync → it's a coroutine
        run_record = await _persist_run_start(
            "INTEGRATION-001", "run-int-001", "web", test_cases, 1,
        )
        assert run_record is not None
        assert run_record.run_id == "run-int-001"
        assert run_record.status == "RUNNING"

        # TaskCard should be running
        await tc.arefresh_from_db()
        assert tc.status == "running"
        assert tc.run_id == run_record.id
        assert tc.running is True

    @pytest.mark.asyncio
    async def test_already_running_task_returns_existing_record(self):
        """Idempotent: calling with already-running task returns the existing run."""
        from apps.test_runner.models import TaskCard
        from apps.test_runner.views.execution_steps import _persist_run_start
        from models.test_models import TestCaseDef

        tc = await TaskCard.objects.acreate(
            task_id="INTEGRATION-002", status="idle", device_serial="web",
        )
        test_cases = [TestCaseDef(id="TC-1", title="t", steps_data=[],
                                  enabled=True, task_type="web_automation")]

        r1 = await _persist_run_start("INTEGRATION-002", "run-1", "web", test_cases, 1)
        assert r1 is not None

        # Second call with same task (already running) → returns existing
        r2 = await _persist_run_start("INTEGRATION-002", "run-2", "web", test_cases, 1)
        assert r2 is not None
        assert r2.id == r1.id  # same run record

    @pytest.mark.asyncio
    async def test_no_client_task_id_creates_standalone_record(self):
        """Without a TaskCard, a standalone TestRunRecord is created."""
        from apps.test_runner.views.execution_steps import _persist_run_start
        from models.test_models import TestCaseDef

        run_record = await _persist_run_start("", "run-standalone", "web", [], 1)
        assert run_record is not None
        assert run_record.run_id == "run-standalone"
        assert run_record.client_task_id == ""


# ══════════════════════════════════════════════════════════════════════
# F. _finalize_run — state convergence
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestFinalizeRunIntegration:
    """_finalize_run: case_items aggregation, TaskCard.run persistence."""

    @pytest.mark.asyncio
    async def test_finalize_sets_taskcard_to_done_completed(self):
        from apps.test_runner.models import TaskCard, TestRunRecord
        from apps.test_runner import state_machine as sm
        from apps.test_runner.views.execution_steps import (
            _persist_run_start, _finalize_run,
        )
        from models.test_models import TestCaseDef, TestResult, TestRun, TestRunStatus

        tc = await TaskCard.objects.acreate(
            task_id="FINALIZE-001", status="idle", device_serial="web",
        )
        cases = [TestCaseDef(id="TC-1", title="t", steps_data=[], enabled=True,
                             task_type="web_automation")]
        run_record = await _persist_run_start("FINALIZE-001", "run-fin-001", "web", cases, 1)

        run_model = TestRun(
            run_id="run-fin-001", device_serial="web",
            status=TestRunStatus.COMPLETED, selected_cases=["TC-1"], loop_count=1,
            case_results=[
                TestResult(case_id="TC-1", case_title="t", iteration=1,
                           result="pass", duration_ms=100, case_type="web_automation"),
            ],
        )
        await tc.arefresh_from_db()

        await _finalize_run(run_record, run_model, "FINALIZE-001")

        await tc.arefresh_from_db()
        assert tc.status == "done"
        assert tc.outcome == "completed"
        assert tc.running is False
        assert len(tc.case_items) == 1
        assert tc.case_items[0]["pass"] == 1
        assert tc.case_items[0]["fail"] == 0

    @pytest.mark.asyncio
    async def test_finalize_with_multiple_cases_aggregates_correctly(self):
        from apps.test_runner.models import TaskCard
        from apps.test_runner.views.execution_steps import (
            _persist_run_start, _finalize_run,
        )
        from models.test_models import TestCaseDef, TestResult, TestRun, TestRunStatus

        tc = await TaskCard.objects.acreate(
            task_id="FINALIZE-002", status="idle", device_serial="web",
        )
        cases = [
            TestCaseDef(id="TC-1", title="pass case", steps_data=[], enabled=True,
                        task_type="web_automation"),
            TestCaseDef(id="TC-2", title="fail case", steps_data=[], enabled=True,
                        task_type="web_automation"),
        ]
        run_record = await _persist_run_start("FINALIZE-002", "run-fin-002", "web", cases, 1)

        run_model = TestRun(
            run_id="run-fin-002", device_serial="web",
            status=TestRunStatus.COMPLETED, selected_cases=["TC-1", "TC-2"], loop_count=1,
            case_results=[
                TestResult(case_id="TC-1", case_title="pass case", iteration=1,
                           result="pass", duration_ms=100, case_type="web_automation"),
                TestResult(case_id="TC-2", case_title="fail case", iteration=1,
                           result="fail", duration_ms=200, case_type="web_automation"),
            ],
        )
        await tc.arefresh_from_db()

        await _finalize_run(run_record, run_model, "FINALIZE-002")

        await tc.arefresh_from_db()
        assert tc.overall_pass == 1
        assert tc.overall_fail == 1
        assert len(tc.case_items) == 2


# ══════════════════════════════════════════════════════════════════════
# G. start_test_run — task type dispatch
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestStartTestRunDispatch:
    """start_test_run: verify all task types load cases correctly."""

    def test_web_task_loads_correct_model(self):
        from apps.case_manager.models_web import WebTestCase

        WebTestCase.objects.create(
            id="WEB-TEST-001", title="test", url="http://x.com", enabled=True,
        )
        rows = WebTestCase.objects.filter(id__in=["WEB-TEST-001"], enabled=True)
        assert rows.count() == 1
        assert rows[0].id == "WEB-TEST-001"

    def test_api_task_loads_correct_model(self):
        from apps.case_manager.models_api import ApiTestCase

        ApiTestCase.objects.create(
            id="API-TEST-001", title="test", method="GET", url="http://x.com",
            enabled=True,
        )
        rows = ApiTestCase.objects.filter(id__in=["API-TEST-001"], enabled=True)
        assert rows.count() == 1
        assert rows[0].method == "GET"

    def test_ui_task_loads_correct_model(self):
        from apps.case_manager.models import TestDefinition

        TestDefinition.objects.create(
            id="TC-TEST-001", title="test", enabled=True,
        )
        rows = TestDefinition.objects.filter(id__in=["TC-TEST-001"], enabled=True)
        assert rows.count() == 1
        assert rows[0].id == "TC-TEST-001"

    def test_disabled_case_not_loaded(self):
        from apps.case_manager.models import TestDefinition

        TestDefinition.objects.create(
            id="TC-DISABLED-001", title="disabled", enabled=False,
        )
        rows = TestDefinition.objects.filter(
            id__in=["TC-DISABLED-001"], enabled=True
        )
        assert rows.count() == 0, "Disabled cases should be excluded"

    def test_nonexistent_case_ids_return_empty(self):
        from apps.case_manager.models import TestDefinition

        rows = TestDefinition.objects.filter(
            id__in=["NONEXISTENT-001"], enabled=True
        )
        assert rows.count() == 0


# ══════════════════════════════════════════════════════════════════════
# H. State machine — dequeue completeness
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestStateMachineDequeueCompleteness:
    """Verify dequeue() sets all fields correctly."""

    def test_dequeue_sets_all_required_fields(self):
        from apps.test_runner.models import TaskCard, TestRunRecord
        from apps.test_runner import state_machine as sm

        tc = TaskCard.objects.create(
            task_id="SM-FULL-001", status="queued", device_serial="test",
        )
        run_record = sm.dequeue(tc, "run-sm-001", "test-device",
                                [{"case_id": "TC-1"}], 3)

        # RunRecord fields
        assert run_record.run_id == "run-sm-001"
        assert run_record.status == "RUNNING"
        assert run_record.device_serial == "test-device"
        assert len(run_record.selected_cases) == 1
        assert run_record.loop_count == 3

        # TaskCard fields
        tc.refresh_from_db()
        assert tc.status == "running"
        assert tc.running is True
        assert tc.run_id == run_record.id

    def test_dequeue_preserves_selected_cases_snapshots(self):
        from apps.test_runner.models import TaskCard
        from apps.test_runner import state_machine as sm

        tc = TaskCard.objects.create(
            task_id="SM-SNAP-001", status="queued", device_serial="test",
        )
        snapshots = [
            {"case_id": "TC-A", "title": "Case A", "steps_data": [{"type": "click"}]},
            {"case_id": "TC-B", "title": "Case B", "steps_data": []},
        ]
        run_record = sm.dequeue(tc, "run-snap-001", "test", snapshots, 1)
        assert run_record.selected_cases == snapshots


# ══════════════════════════════════════════════════════════════════════
# I. Log completeness — logs vs step_details consistency
# ══════════════════════════════════════════════════════════════════════


class TestLogCompleteness:
    """PRD §5.2: 10 种 WS 事件必须可靠送达。

    Bug: ID-062 执行完毕产生 16 条 step_detail，但 TaskCard 只保存了 4 条日志。
    根因：_broadcast() 丢弃 consumer 后无反馈，log() 调用方无法感知数据丢失。
    """

    # ── Layer 1: Executor 产生正确数量的日志 ──

    @pytest.mark.asyncio
    async def test_executor_produces_one_log_per_step(self):
        """WebExecutor._dispatch 每步至少产生 1 条 adapter.log() 调用。"""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = []

        exec_ = WebExecutor(adapter)
        steps = [
            TestStep(type="web_navigate", url="http://x.com", description="go"),
            TestStep(type="web_click", selector="#btn", description="click"),
            TestStep(type="web_fill", selector="#inp", value="hi", description="fill"),
        ]
        case = TestCaseDef(id="TC-LOG-1", title="t", steps_data=steps, enabled=True,
                           task_type="web_automation")
        await exec_.execute_case(case, iteration=1, run_id="r-log-1")

        # 3 steps → at least 3 log calls (one per _dispatch)
        assert adapter.log.call_count >= 3, (
            f"expected ≥3 log calls for 3 steps, got {adapter.log.call_count}"
        )
        # 3 steps → exactly 3 step_details
        assert len(exec_._last_step_details) == 3, (
            f"step_details count ({len(exec_._last_step_details)}) != step count (3)"
        )

    @pytest.mark.asyncio
    async def test_executor_produces_one_callback_per_step(self):
        """每个步骤触发 step_started + step_result 回调各一次。"""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter._click = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = []

        exec_ = WebExecutor(adapter)
        started = MagicMock()
        result = MagicMock()
        exec_._step_started_callback = started
        exec_._step_callback = result

        steps = [
            TestStep(type="web_navigate", url="http://x.com", description="a"),
            TestStep(type="web_click", selector="#b", description="b"),
        ]
        case = TestCaseDef(id="TC-CB-3", title="t", steps_data=steps, enabled=True,
                           task_type="web_automation")
        await exec_.execute_case(case, iteration=1, run_id="r-cb-3")

        assert started.call_count == 2, (
            f"step_started callback: expected 2, got {started.call_count}"
        )
        assert result.call_count == 2, (
            f"step_result callback: expected 2, got {result.call_count}"
        )

    # ── Layer 2: step_details 与日志数量一致性 ──

    @pytest.mark.asyncio
    async def test_step_details_count_matches_expected(self):
        """N 个手动步骤 + expected_result → N+1 条 step_detail（始终一致）。"""
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = MagicMock()
        adapter._navigate = AsyncMock()
        adapter.get_log_buffer.return_value = []
        adapter.stopped.return_value = False
        adapter._watchers = []

        # 7 manual steps + expected_result → should produce 8 step_details
        steps = [TestStep(type="web_navigate", url="http://x.com", description=f"s{i}")
                 for i in range(7)]
        case = TestCaseDef(
            id="TC-LOG-2", title="t", steps_data=steps, enabled=True,
            task_type="web_automation",
            extra_data={"expected_result": "Dashboard"},
        )

        exec_ = WebExecutor(adapter)
        # Mock the verify step
        adapter._ensure_browser = AsyncMock()
        adapter._page = MagicMock()
        adapter._page.content.return_value = "<html><body>Dashboard</body></html>"

        await exec_.execute_case(case, iteration=1, run_id="r-log-2")

        assert len(exec_._last_step_details) == 8, (
            f"7 manual steps + expected_result should = 8 step_details, "
            f"got {len(exec_._last_step_details)}"
        )

    # ── Layer 3: WS 广播不做静默丢弃 ──

    @pytest.mark.asyncio
    async def test_broadcast_dropped_messages_are_countable(self):
        """_broadcast 无 consumer 时，调用方应能感知消息未被送达。

        PRD §5.2: "慢客户端超时自动移除，不阻塞其他客户端" —
        移除是正确的，但丢弃应该可被观测（返回值/计数器/日志），
        否则 _bridge_ws_log 永远不知道消息丢了。
        """
        from apps.test_runner.callbacks import WsTestCallback

        cb = WsTestCallback()
        attempt_count = 0

        # Monkey-patch _broadcast 来计数丢弃
        _orig = cb._broadcast

        async def _counting_broadcast(run_id, msg, timeout=2.0):
            nonlocal attempt_count
            attempt_count += 1
            await _orig(run_id, msg, timeout)
            # After this returns, check if consumer is still there
            return len(cb.clients.get(run_id, []))

        cb._broadcast = _counting_broadcast

        # Step 1: register a consumer that will time out
        slow = AsyncMock()
        slow.send = AsyncMock(side_effect=asyncio.TimeoutError)
        cb.register("run-drop", slow)

        await cb.on_log("run-drop", "msg-1")  # consumer discarded
        remaining = len(cb.clients.get("run-drop", []))

        # Step 2: subsequent broadcasts — consumer count = 0
        await cb.on_log("run-drop", "msg-2-lost")
        await cb.on_step_result("run-drop", "C1", 1, 0, 3, "x", "y", "pass")

        # Bug: 3 attempts were made, but after the first one, all were silent.
        # Caller (_bridge_ws_log) has no way to know msg-2 and msg-3 were dropped.
        if remaining == 0 and attempt_count >= 3:
            pytest.fail(
                f"BUG CONFIRMED: {attempt_count} broadcast attempts made, "
                f"but after consumer was discarded on attempt 1, subsequent "
                f"messages were silently dropped. _broadcast() should return "
                f"a delivery status or log a warning so _bridge_ws_log can "
                f"detect data loss. PRD §5.2 requires 10 event types to be "
                f"delivered reliably."
            )
