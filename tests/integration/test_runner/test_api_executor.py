"""ApiExecutor Mock 集成测试 — 变量提取 + 数据驱动 + 断言。

使用 Mock ApiAdapter（来自 conftest），不依赖真实 HTTP 调用。
"""

import pytest
from models.step_types import TestStep
from models.test_models import TestCaseDef
from apps.test_runner.executors.api.executor import ApiExecutor


def _case(steps_data, extra_data=None, case_id="API-001"):
    return TestCaseDef(id=case_id, title="Test", steps_data=steps_data,
                       extra_data=extra_data or {})


def _step(**kw):
    defaults = {"type": "api_request", "description": "step"}
    defaults.update(kw)
    return TestStep(**defaults)


class TestBasicExecution:
    def test_single_step_passes(self, mock_api_adapter):
        case = _case([_step(url="/api/status")])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_multiple_steps(self, mock_api_adapter):
        case = _case([
            _step(url="/api/login"),
            _step(url="/api/user"),
            _step(type="api_log", description="done"),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"
        # 只有 api_request 步调用 adapter.execute_step
        assert mock_api_adapter.execute_step.call_count == 2

    def test_first_failure_short_circuits(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {"status_code": 200, "response_body": "{}", "response_headers": {}, "duration_ms": 50.0, "result": "fail"}
        case = _case([
            _step(url="/api/bad"),
            _step(url="/api/never"),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "fail"
        assert mock_api_adapter.execute_step.call_count == 1

    def test_stop_during_sleep(self, mock_api_adapter):
        mock_api_adapter.stopped.return_value = True
        case = _case([_step(type="api_sleep", timeout=10)])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "stopped"


class TestVariableExtraction:
    def test_extract_and_use_variable(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {
            "status_code": 200,
            "response_body": '{"data":{"token":"abc123"}}',
            "response_headers": {},
            "duration_ms": 50.0,
            "result": "pass",
        }
        case = _case([
            TestStep(type="api_request", url="/api/login",
                     extract={"token": "$.data.token"}),
            _step(url="/api/user",
                  headers={"Authorization": "Bearer {{token}}"}),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"
        second_call = mock_api_adapter.execute_step.call_args_list[1][0][0]
        # _do_request 会 resolve headers 中的 {{token}} → abc123
        assert "abc123" in str(second_call.headers)

    def test_header_variable_extraction(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {
            "status_code": 200,
            "response_body": "{}",
            "response_headers": {"x-csrf-token": "csrf-xyz"},
            "duration_ms": 50.0,
            "result": "pass",
        }
        case = _case([
            TestStep(type="api_request", url="/api/login",
                     extract={"csrf": "$.headers.x-csrf-token"}),
            _step(url="/api/action", headers={"X-CSRF": "{{csrf}}"}),
        ])
        ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        second_call = mock_api_adapter.execute_step.call_args_list[1][0][0]
        assert "csrf-xyz" in str(second_call.headers)


class TestDataDriven:
    def test_two_rows_two_executions(self, mock_api_adapter):
        case = _case(
            steps_data=[_step(url="/api/{{endpoint}}")],
            extra_data={"_rows": [
                {"key": "endpoint", "values": ["login", "signin"]},
            ]},
        )
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"
        assert mock_api_adapter.execute_step.call_count == 2

    def test_validation_row_passes(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {"status_code": 200, "response_body": '{"status":"ok"}', "response_headers": {}, "duration_ms": 50.0, "result": "pass"}
        case = _case(
            steps_data=[_step(url="/api/status")],
            extra_data={"_rows": [
                {"key": "endpoint", "values": ["status"], "kind": "input"},
                {"key": "$.status", "values": ["ok"], "kind": "validate"},
            ]},
        )
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_validation_mismatch_fails(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {"status_code": 200, "response_body": '{"status":"error"}', "response_headers": {}, "duration_ms": 50.0, "result": "pass"}
        case = _case(
            steps_data=[_step(url="/api/status")],
            extra_data={"_rows": [
                {"key": "endpoint", "values": ["status"], "kind": "input"},
                {"key": "$.status", "values": ["ok"], "kind": "validate"},
            ]},
        )
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "fail"


class TestAssertions:
    def _setup(self, mock_api_adapter, status=200, body="{}", duration=50.0):
        mock_api_adapter.execute_step.return_value = {
            "status_code": status,
            "response_body": body,
            "response_headers": {},
            "duration_ms": duration,
            "result": "pass",
        }

    def test_status_code_simple(self, mock_api_adapter):
        """不传 assertions 时，用 expected_status 做简单状态码校验。"""
        self._setup(mock_api_adapter)
        case = _case([
            _step(url="/api/status"),
            TestStep(type="api_assert", expected_status=200),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_status_code_mismatch_fails(self, mock_api_adapter):
        self._setup(mock_api_adapter, status=500)
        case = _case([
            _step(url="/api/status"),
            TestStep(type="api_assert", expected_status=200),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "fail"

    def test_response_time(self, mock_api_adapter):
        self._setup(mock_api_adapter, duration=150.0)
        case = _case([
            _step(url="/api/slow"),
            TestStep(type="api_assert", assertions=[
                {"type": "response_time", "expect": 5000},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_response_time_exceeds_fails(self, mock_api_adapter):
        self._setup(mock_api_adapter, duration=6000.0)
        case = _case([
            _step(url="/api/slow"),
            TestStep(type="api_assert", assertions=[
                {"type": "response_time", "expect": 5000},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "fail"

    def test_json_path_equals(self, mock_api_adapter):
        self._setup(mock_api_adapter, body='{"data":{"id":42}}')
        case = _case([
            _step(url="/api/data"),
            TestStep(type="api_assert", assertions=[
                {"path": "$.data.id", "op": "equals", "expect": 42},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_json_contains(self, mock_api_adapter):
        self._setup(mock_api_adapter, body='{"message":"hello world"}')
        case = _case([
            _step(url="/api/message"),
            TestStep(type="api_assert", assertions=[
                {"path": "$.message", "op": "contains", "expect": "hello"},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_json_greater_than(self, mock_api_adapter):
        self._setup(mock_api_adapter, body='{"count":10}')
        case = _case([
            _step(url="/api/count"),
            TestStep(type="api_assert", assertions=[
                {"path": "$.count", "op": "greater_than", "expect": 5},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "pass"

    def test_equals_mismatch_fails(self, mock_api_adapter):
        self._setup(mock_api_adapter, body='{"status":"error"}')
        case = _case([
            _step(url="/api/check"),
            TestStep(type="api_assert", assertions=[
                {"path": "$.status", "op": "equals", "expect": "ok"},
            ]),
        ])
        result = ApiExecutor(mock_api_adapter).execute_case(case, iteration=1, run_id="r")
        assert result == "fail"


class TestStepCallbacks:
    def test_callbacks_in_order(self, mock_api_adapter):
        started, results = [], []
        executor = ApiExecutor(mock_api_adapter)
        executor._step_started_callback = lambda i, t, tp, d: started.append((i, tp))
        executor._step_callback = lambda i, t, tp, d, r: results.append((i, tp, r))

        case = _case([_step(url="/api/a"), _step(url="/api/b")])
        executor.execute_case(case, iteration=1, run_id="r")

        assert len(started) == 2
        assert len(results) == 2
        assert all(r[2] == "pass" for r in results)

    def test_fail_step_callback_reports_fail(self, mock_api_adapter):
        mock_api_adapter.execute_step.return_value = {"status_code": 200, "response_body": "{}", "response_headers": {}, "duration_ms": 50.0, "result": "fail"}
        results = []
        executor = ApiExecutor(mock_api_adapter)
        executor._step_callback = lambda i, t, tp, d, r: results.append(r)

        case = _case([_step(url="/api/fail")])
        executor.execute_case(case, iteration=1, run_id="r")
        assert results[0] == "fail"
