"""Variable substitution unit tests — ApiExecutorV2._substitute_vars.

Tests the 5-field deep substitution: url, headers, body, request_schema, response_schema.
Also tests priority: row_input > extract_vars.
"""

import allure

from apps.test_runner.executors.api.executor_v2 import ApiExecutorV2

# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


class _NullAdapter:
    """Minimal adapter stub — never actually called during _substitute_vars tests."""

    def log(self, msg):
        pass

    def stopped(self):
        return False


def _make_executor(extract_vars: dict = None):
    """Create an executor with pre-populated extract variables."""
    ex = ApiExecutorV2(_NullAdapter())
    if extract_vars:
        ex._variables = dict(extract_vars)
    return ex


def _step(**overrides):
    """Build a step_cfg dict with defaults."""
    s = {
        "name": "TestStep",
        "domain": "",
        "url": "/test",
        "method": "GET",
        "headers": {},
        "body": {},
        "request_schema": None,
        "response_schema": None,
        "extract": [],
        "assert": False,
    }
    s.update(overrides)
    return s


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("变量替换")
@allure.story("URL 替换")
def test_url_substitution():
    """TC-SUB-001: url 中 {{id}} → 替换正确"""
    executor = _make_executor()
    step = _step(url="/users/{{userId}}/posts/{{postId}}")
    row = {"userId": "42", "postId": "7"}

    result = executor._substitute_vars(step, row)

    assert result["url"] == "/users/42/posts/7"


@allure.feature("变量替换")
@allure.story("Headers 替换")
def test_headers_substitution():
    """TC-SUB-002: headers 中 {{token}} → 替换正确"""
    executor = _make_executor(extract_vars={"token": "abc123xyz"})
    step = _step(headers={"Authorization": "Bearer {{token}}", "X-User": "{{userId}}"})
    row = {"userId": "alice"}

    result = executor._substitute_vars(step, row)

    assert result["headers"]["Authorization"] == "Bearer abc123xyz"
    assert result["headers"]["X-User"] == "alice"


@allure.feature("变量替换")
@allure.story("Body 替换")
def test_body_substitution_nested():
    """TC-SUB-003: body 中嵌套 {{username}} → 替换正确"""
    executor = _make_executor()
    step = _step(
        body={
            "user": "{{username}}",
            "meta": {
                "role": "{{role}}",
                "tags": ["{{tag}}"],
            },
        }
    )
    row = {"username": "admin", "role": "superuser", "tag": "vip"}

    result = executor._substitute_vars(step, row)

    assert result["body"]["user"] == "admin"
    assert result["body"]["meta"]["role"] == "superuser"
    assert result["body"]["meta"]["tags"] == ["vip"]


@allure.feature("变量替换")
@allure.story("response_schema 替换")
def test_response_schema_substitution():
    """TC-SUB-004: response_schema 中 {{expected_role}} → 替换正确（关键回归）

    If response_schema is NOT substituted before assertion, dynamic expected
    values in test data rows will NEVER match — all rows fail.
    """
    executor = _make_executor()
    step = _step(
        response_schema={
            "type": "object",
            "required": ["data"],
            "properties": {
                "data": {
                    "type": "object",
                    "required": ["role"],
                    "properties": {
                        "role": {"const": "{{expected_role}}"},
                    },
                },
            },
        },
    )
    row = {"expected_role": "admin"}

    result = executor._substitute_vars(step, row)

    role_const = result["response_schema"]["properties"]["data"]["properties"]["role"]["const"]
    assert role_const == "admin", f"response_schema not substituted, got: {role_const}"


@allure.feature("变量替换")
@allure.story("request_schema 替换")
def test_request_schema_substitution():
    """TC-SUB-005: request_schema 中 {{min_length}} → 替换正确"""
    executor = _make_executor()
    step = _step(
        request_schema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": "{{min_len}}"},
            },
        },
    )
    row = {"min_len": "3"}

    result = executor._substitute_vars(step, row)

    # Note: minLength becomes string "3" because row values are strings.
    # In practice, schemas use numeric constraints; this tests the mechanism.
    assert result["request_schema"]["properties"]["username"]["minLength"] == "3"


@allure.feature("变量替换")
@allure.story("优先级")
def test_row_input_overrides_extract_vars():
    """TC-SUB-006: row.input 同名覆盖 extract_vars（行数据优先级更高）"""
    executor = _make_executor(extract_vars={"token": "extracted_abc", "user": "extracted_user"})
    step = _step(
        url="/users/{{user}}",
        headers={"Authorization": "Bearer {{token}}"},
        body={"token": "{{token}}", "user": "{{user}}"},
    )
    row = {"user": "row_alice"}  # only overrides user, token stays from extract

    result = executor._substitute_vars(step, row)

    # row.user wins over extract_vars.user
    assert result["url"] == "/users/row_alice"
    assert result["body"]["user"] == "row_alice"
    # token only exists in extract_vars → uses that
    assert result["headers"]["Authorization"] == "Bearer extracted_abc"
    assert result["body"]["token"] == "extracted_abc"


@allure.feature("变量替换")
@allure.story("无匹配")
def test_unmatched_placeholder_left_unchanged():
    """TC-SUB-007: 未匹配的 {{var}} 保持原样"""
    executor = _make_executor()
    step = _step(url="/users/{{nonexistent}}")
    row = {}

    result = executor._substitute_vars(step, row)

    assert result["url"] == "/users/{{nonexistent}}"


@allure.feature("变量替换")
@allure.story("不可变性")
def test_original_step_not_mutated():
    """TC-SUB-008: deep-clone 保证原 step_cfg 不被修改"""
    executor = _make_executor()
    original = _step(url="/users/{{id}}", headers={"X-Tenant": "{{tenant}}"})
    row = {"id": "99", "tenant": "acme"}

    result = executor._substitute_vars(original, row)

    # Original must be unchanged
    assert original["url"] == "/users/{{id}}"
    assert original["headers"]["X-Tenant"] == "{{tenant}}"
    # Result has substitutions
    assert result["url"] == "/users/99"
