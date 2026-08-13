"""ApiExecutorV2 unit tests — mock adapter, 11 cases covering the 7-step pipeline.

Tests the config_json-native executor without real HTTP requests.
Uses a MockAdapter that returns controlled responses.
"""

import json

import allure

from apps.test_runner.executors.api.executor_v2 import ApiExecutorV2
from models.step_types import TestStep
from models.test_models import TestCaseDef

# ═══════════════════════════════════════════════════════════════════
# Mock Adapter
# ═══════════════════════════════════════════════════════════════════


class MockAdapter:
    """Fake adapter that returns controlled HTTP responses for unit testing."""

    def __init__(self, responses=None, stopped=False):
        """
        Args:
            responses: list of dicts — each is a response for one execute_step call.
                       If None, returns a default-pass response.
            stopped: whether adapter reports as stopped.
        """
        self._responses = responses or []
        self._call_index = 0
        self._stopped = stopped
        self.logs: list[str] = []

    def log(self, msg: str):
        self.logs.append(msg)

    def stopped(self) -> bool:
        return self._stopped

    def execute_step(self, step: TestStep) -> dict:
        """Return the next canned response, or a default success."""
        if self._call_index < len(self._responses):
            resp = self._responses[self._call_index]
            self._call_index += 1
            return resp
        self._call_index += 1
        return {
            "result": "pass",
            "status_code": 200,
            "response_body": json.dumps({"ok": True}),
            "response_headers": {"Content-Type": "application/json"},
            "duration_ms": 42,
        }


def _make_step_cfg(
    name="Echo GET",
    method="GET",
    url="/get",
    body=None,
    headers=None,
    extract=None,
    assert_=False,
    request_schema=None,
    response_schema=None,
    domain="",
):
    """Build a minimal config_json step dict."""
    return {
        "name": name,
        "domain": domain,
        "url": url,
        "method": method,
        "headers": headers or {},
        "body": body or {},
        "request_schema": request_schema,
        "response_schema": response_schema,
        "extract": extract or [],
        "assert": assert_,
    }


def _make_case(steps_cfg, test_data=None, validation=None):
    """Build a TestCaseDef with config_json in extra_data."""
    return TestCaseDef(
        id="TC-001",
        title="Test Case",
        task_type="api_testing",
        extra_data={
            "config_json": {
                "steps": steps_cfg,
                "test_data": test_data or [],
                "validation": validation or [],
            },
        },
    )


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API Executor V2")
@allure.story("单步执行")
def test_single_get_step_passes():
    """TC-EXEC-001: 单步 GET 请求 → pass"""
    adapter = MockAdapter()
    executor = ApiExecutorV2(adapter)
    steps = [_make_step_cfg(method="GET", url="/get")]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "pass"


@allure.feature("API Executor V2")
@allure.story("request_schema 校验")
def test_request_schema_pass_sends_request():
    """TC-EXEC-002: request_schema 匹配 → 发送 HTTP 请求并 pass"""
    adapter = MockAdapter()
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            method="POST",
            url="/post",
            body={"username": "admin", "password": "admin123"},
            request_schema={
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string", "minLength": 3},
                    "password": {"type": "string", "minLength": 6},
                },
            },
        )
    ]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "pass"


@allure.feature("API Executor V2")
@allure.story("request_schema 校验")
def test_request_schema_mismatch_fails_no_request():
    """TC-EXEC-003: request_schema 不匹配 → fail，不发送 HTTP 请求"""
    adapter = MockAdapter()
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            method="POST",
            url="/post",
            body={"username": "ab"},  # too short for minLength: 3
            request_schema={
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string", "minLength": 3},
                    "password": {"type": "string", "minLength": 6},
                },
            },
        )
    ]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "fail"
    # No HTTP request was sent — adapter never called execute_step
    assert adapter._call_index == 0


@allure.feature("API Executor V2")
@allure.story("response_schema 断言")
def test_response_schema_match_passes():
    """TC-EXEC-004: response_schema 匹配 → pass"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"status": "ok", "data": {"id": 1}}),
                "response_headers": {},
                "duration_ms": 30,
            }
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            method="GET",
            url="/get",
            assert_=True,
            response_schema={
                "type": "object",
                "required": ["status", "data"],
                "properties": {
                    "status": {"const": "ok"},
                    "data": {"type": "object"},
                },
            },
        )
    ]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "pass"


@allure.feature("API Executor V2")
@allure.story("response_schema 断言")
def test_response_schema_mismatch_fails():
    """TC-EXEC-005: response_schema 不匹配 → fail（含 schema diff 信息）"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"status": "error", "msg": "not found"}),
                "response_headers": {},
                "duration_ms": 30,
            }
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            method="GET",
            url="/get",
            assert_=True,
            response_schema={
                "type": "object",
                "required": ["status", "data"],
                "properties": {
                    "status": {"const": "ok"},
                },
            },
        )
    ]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "fail"
    # Check that the failure was logged
    assert any("response_schema FAIL" in log for log in adapter.logs)


@allure.feature("API Executor V2")
@allure.story("变量提取与传递")
def test_variable_extraction_and_passing():
    """TC-EXEC-006: 两步变量传递（extract → {{var}}）→ pass"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"data": {"token": "abc123", "id": 42}}),
                "response_headers": {},
                "duration_ms": 50,
            },
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"user": "admin"}),
                "response_headers": {},
                "duration_ms": 30,
            },
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            name="Login",
            method="POST",
            url="/login",
            body={"username": "admin", "password": "admin123"},
            extract=[
                {"name": "token", "path": "$.data.token"},
                {"name": "userId", "path": "$.data.id"},
            ],
        ),
        _make_step_cfg(
            name="GetUser",
            method="GET",
            url="/user/me",
            body={"user_id": "{{userId}}"},
            headers={"Authorization": "Bearer {{token}}"},
        ),
    ]
    case = _make_case(steps)

    result = executor.execute_case(case)

    assert result == "pass"
    # Verify the second call had substituted values
    assert adapter._call_index == 2


@allure.feature("API Executor V2")
@allure.story("数据驱动")
def test_data_driven_two_rows_two_steps():
    """TC-EXEC-007: test_data 2 行 × 2 步 → 4 次请求全部执行"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": "{}",
                "response_headers": {},
                "duration_ms": 10,
            },
            {
                "result": "pass",
                "status_code": 200,
                "response_body": "{}",
                "response_headers": {},
                "duration_ms": 10,
            },
            {
                "result": "pass",
                "status_code": 200,
                "response_body": "{}",
                "response_headers": {},
                "duration_ms": 10,
            },
            {
                "result": "pass",
                "status_code": 200,
                "response_body": "{}",
                "response_headers": {},
                "duration_ms": 10,
            },
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(name="Step1", method="GET", url="/a"),
        _make_step_cfg(name="Step2", method="GET", url="/b"),
    ]
    test_data = [
        {"input": {"user": "alice"}},
        {"input": {"user": "bob"}},
    ]
    case = _make_case(steps, test_data=test_data)

    result = executor.execute_case(case)

    assert result == "pass"
    # 2 rows × 2 steps = 4 HTTP requests
    assert adapter._call_index == 4


@allure.feature("API Executor V2")
@allure.story("行级输出断言")
def test_row_output_schema_assertion():
    """TC-EXEC-008: 行级 output_schema 覆盖 → 断言生效"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"status": "ok", "data": {"role": "admin"}}),
                "response_headers": {},
                "duration_ms": 10,
            },
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"status": "ok", "data": {"role": "admin"}}),
                "response_headers": {},
                "duration_ms": 10,
            },
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(name="Login", method="POST", url="/login", body={"user": "{{user}}"}),
        _make_step_cfg(name="Profile", method="GET", url="/profile"),
    ]
    test_data = [
        {
            "input": {"user": "alice"},
            "output_schema": {
                "step_index": 1,
                "schema": {
                    "type": "object",
                    "required": ["status", "data"],
                    "properties": {
                        "status": {"const": "ok"},
                    },
                },
            },
        },
        {"input": {"user": "bob"}},  # no output_schema — uses last_response for schema check
    ]
    case = _make_case(steps, test_data=test_data)

    result = executor.execute_case(case)

    assert result == "pass"
    assert adapter._call_index == 4  # 2 rows × 2 steps


@allure.feature("API Executor V2")
@allure.story("行级输出断言")
def test_row_output_schema_fails():
    """TC-EXEC-009: 行级 output_schema 不匹配 → fail"""
    adapter = MockAdapter(
        responses=[
            {
                "result": "pass",
                "status_code": 200,
                "response_body": json.dumps({"status": "error"}),
                "response_headers": {},
                "duration_ms": 10,
            },
        ]
    )
    executor = ApiExecutorV2(adapter)
    steps = [_make_step_cfg(name="Step1", method="GET", url="/a")]
    test_data = [
        {
            "input": {},
            "output_schema": {
                "step_index": 0,
                "schema": {
                    "type": "object",
                    "required": ["status", "data"],  # response is missing "data"
                    "properties": {
                        "status": {"const": "ok"},
                    },
                },
            },
        }
    ]
    case = _make_case(steps, test_data=test_data)

    result = executor.execute_case(case)

    assert result == "fail"
    assert any("output_schema FAIL" in log for log in adapter.logs)


@allure.feature("API Executor V2")
@allure.story("validation 校验")
def test_validation_check_blocks_request():
    """TC-EXEC-010: validation schema 不匹配 → fail，不发请求"""
    adapter = MockAdapter()
    executor = ApiExecutorV2(adapter)
    steps = [
        _make_step_cfg(
            method="POST",
            url="/post",
            body={"username": "ab"},  # too short, missing "password"
        )
    ]
    validation = [
        {
            "step_index": 0,
            "enabled": True,
            "schema": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string", "minLength": 3},
                    "password": {"type": "string"},
                },
            },
        }
    ]
    case = _make_case(steps, validation=validation)

    result = executor.execute_case(case)

    assert result == "fail"
    assert adapter._call_index == 0  # No HTTP request sent


@allure.feature("API Executor V2")
@allure.story("边界情况")
def test_validation_disabled_skips():
    """TC-EXEC-011: validation enabled=false → 跳过校验，正常执行"""
    adapter = MockAdapter()
    executor = ApiExecutorV2(adapter)
    steps = [_make_step_cfg(method="GET", url="/get")]
    validation = [
        {
            "step_index": 0,
            "enabled": False,  # disabled
            "schema": {
                "type": "object",
                "required": ["nonexistent_field"],
            },
        }
    ]
    case = _make_case(steps, validation=validation)

    result = executor.execute_case(case)

    assert result == "pass"
    assert adapter._call_index == 1  # HTTP request still sent
