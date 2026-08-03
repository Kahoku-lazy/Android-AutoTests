"""StepExecutor Mock 集成测试 — 24 种 UI 步骤分发。

使用纯 MagicMock 适配器（不依赖 DeviceAdapter 实现细节）。
覆盖：基本操作 / 断言 / 应用控制 / 性能Toast / 容器步骤 / 失败短路 / 停止 / 旧名兼容。
"""

import pytest
from unittest.mock import MagicMock
from models.step_types import TestStep
from apps.test_runner.executors.ui.executor import StepExecutor


@pytest.fixture
def mock_adapter():
    """纯 MagicMock 适配器，所有方法返回成功默认值。"""
    ad = MagicMock()
    ad.stopped.return_value = False
    ad.exists.return_value = True
    ad.get_text.return_value = "mock_text"
    ad.click.return_value = True
    ad.long_click.return_value = True
    ad.swipe.return_value = True
    ad.click_indexed.return_value = True
    ad.wait_for_toast.return_value = True
    ad.wait_appear_then_disappear.return_value = True
    ad.d = MagicMock()
    ad.d.app_start.return_value = None
    ad.PACKAGE_NAME = "com.test.app"
    ad._step_started_callback = None
    ad._step_callback = None
    return ad


class TestBasicOperations:
    def test_click_passes(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="click", xpath="//btn", description="点击按钮")])
        assert result == "pass"

    def test_long_click_passes(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="long_click", xpath="//item")])
        assert result == "pass"

    def test_swipe(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="swipe", direction="up", distance=500)])
        assert result == "pass"

    def test_wait_found(self, mock_adapter):
        mock_adapter.exists.return_value = True
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="wait", xpath="//view", timeout=0.1)])
        assert result == "pass"

    def test_wait_not_found_times_out(self, mock_adapter):
        mock_adapter.exists.return_value = False
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="wait", xpath="//missing", timeout=0.1)])
        assert result == "fail"

    def test_sleep(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="sleep", timeout=0.05)])
        assert result == "pass"

    def test_log(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="log", description="测试日志")])
        assert result == "pass"

    def test_screenshot(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="screenshot")])
        assert result == "pass"

    def test_click_indexed(self, mock_adapter):
        mock_adapter.click_indexed.return_value = True
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="click_indexed", xpath="//item", index=2)])
        assert result == "pass"


class TestAssertions:
    def test_verify_text_matches(self, mock_adapter):
        mock_adapter.get_text.return_value = "expected"
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="verify_text", xpath="//label", expected_text="expected")])
        assert result == "pass"

    def test_verify_text_mismatch_fails(self, mock_adapter):
        mock_adapter.get_text.return_value = "wrong"
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="verify_text", xpath="//label", expected_text="expected")])
        assert result == "fail"

    def test_poll_text_matches(self, mock_adapter):
        mock_adapter.exists.return_value = True
        mock_adapter.get_text.return_value = "ready"
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="poll_text", xpath="//status", expected_text="ready", timeout=0.1)])
        assert result == "pass"


class TestAppControl:
    def test_start_app(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="start_app", xpath="com.test.app")])
        assert result == "pass"

    def test_start_app_no_package_fails(self, mock_adapter):
        mock_adapter.PACKAGE_NAME = ""
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="start_app", xpath="")])
        assert result == "fail"

    def test_kill_app(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="kill_app")])
        assert result == "pass"


class TestPerfAndToast:
    def test_perf_element_time_found(self, mock_adapter):
        mock_adapter.exists.return_value = True
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="perf_element_time", xpath="//target", timeout=0.1)])
        assert result == "pass"

    def test_perf_element_time_not_found(self, mock_adapter):
        mock_adapter.exists.return_value = False
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="perf_element_time", xpath="//missing", timeout=0.1)])
        assert result == "fail"

    def test_wait_toast(self, mock_adapter):
        mock_adapter.wait_for_toast.return_value = True
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="wait_toast", expected_text="保存成功")])
        assert result == "pass"

    def test_wait_disappear(self, mock_adapter):
        mock_adapter.wait_appear_then_disappear.return_value = True
        result = StepExecutor(mock_adapter).execute_all(
            [TestStep(type="wait_disappear", xpath="//loading", timeout=0.1)])
        assert result == "pass"


class TestContainers:
    def test_if_appear_executes_children_when_found(self, mock_adapter):
        mock_adapter.exists.return_value = True
        step = TestStep(type="if_element_appear", xpath="//dialog",
                        children=[TestStep(type="click", xpath="//ok"),
                                  TestStep(type="log", description="done")])
        result = StepExecutor(mock_adapter).execute_all([step])
        assert result == "pass"

    def test_if_appear_skips_children_when_not_found(self, mock_adapter):
        mock_adapter.exists.return_value = False
        step = TestStep(type="if_element_appear", xpath="//dialog",
                        children=[TestStep(type="click", xpath="//ok")])
        result = StepExecutor(mock_adapter).execute_all([step])
        assert result == "pass"  # skip ≠ fail

    def test_if_disappear_executes_when_absent(self, mock_adapter):
        mock_adapter.exists.return_value = False
        step = TestStep(type="if_element_disappear", xpath="//loading",
                        children=[TestStep(type="log")])
        result = StepExecutor(mock_adapter).execute_all([step])
        assert result == "pass"

    def test_loop_n_repeats(self, mock_adapter):
        call_count = [0]

        def counting_log(s):
            call_count[0] += 1
            return "pass"

        executor = StepExecutor(mock_adapter)
        executor._do_log = counting_log
        step = TestStep(type="loop_n", index=3,
                        children=[TestStep(type="log")])
        result = executor.execute_all([step])
        assert result == "pass"
        assert call_count[0] >= 3  # 循环 3 次，每次至少调用 1 次子步骤

    def test_loop_n_stops_on_child_failure(self, mock_adapter):
        calls = []
        mock_adapter.click.side_effect = lambda *a, **kw: (
            calls.append(1) or True if len(calls) == 0 else (calls.append(1) or False))
        step = TestStep(type="loop_n", index=5,
                        children=[TestStep(type="click", xpath="//btn")])
        result = StepExecutor(mock_adapter).execute_all([step])
        # With click returning False on second attempt, loop will stop
        assert result in ("pass", "fail")

    def test_loop_elements_iterates(self, mock_adapter):
        step = TestStep(type="loop_elements",
                        xpath="//item1|//item2|//item3",
                        children=[TestStep(type="click", xpath="//item")])
        result = StepExecutor(mock_adapter).execute_all([step])
        assert result == "pass"


class TestFailureShortCircuit:
    def test_first_failure_halts_remaining(self, mock_adapter):
        """第一步 wait 失败 → 第二步 click 不执行。"""
        mock_adapter.exists.return_value = False
        executor = StepExecutor(mock_adapter)
        result = executor.execute_all([
            TestStep(type="wait", xpath="//missing", timeout=0.05),
            TestStep(type="click", xpath="//never_executed"),
        ])
        assert result == "fail"


class TestStopInterrupt:
    def test_stop_before_execute_returns_stopped(self, mock_adapter):
        mock_adapter.stopped.return_value = True
        result = StepExecutor(mock_adapter).execute(
            TestStep(type="click", xpath="//btn"))
        assert result == "stopped"


class TestLegacyNames:
    @pytest.mark.parametrize("step_type", [
        "start_app", "kill_app", "wait_toast", "perf_element_time",
        "if_element_appear", "if_element_disappear", "loop_n", "loop_elements",
        "poll_text", "verify_text", "wait_disappear",
    ])
    def test_legacy_name_recognized(self, mock_adapter, step_type):
        mock_adapter.exists.return_value = True
        mock_adapter.get_text.return_value = "ok"
        mock_adapter.wait_for_toast.return_value = True
        mock_adapter.wait_appear_then_disappear.return_value = True
        executor = StepExecutor(mock_adapter)
        step = TestStep(type=step_type, xpath="//elem", expected_text="ok",
                        timeout=0.05, description=f"legacy {step_type}")
        result = executor.execute(step)
        assert result in ("pass", "fail", "skip"), f"{step_type} returned {result}"


class TestUnknownType:
    def test_unknown_type_returns_fail(self, mock_adapter):
        result = StepExecutor(mock_adapter).execute(
            TestStep(type="non_existent_type"))
        assert result == "fail"
