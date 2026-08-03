"""ApiExecutor 纯逻辑测试 — 零 I/O，无 DB/HTTP/适配器依赖。

覆盖：
- _resolve / _resolve_with：{{var}} 模板替换
- _resolve_dict / _resolve_dict_with：递归字典替换
- _to_row_dicts：列式转行式数据
- _split_rows：按 kind 拆分输入行/验证行
- _navigate_json / _eval_json_path：JSON 路径导航
- _clone_steps：深拷贝隔离
- _substitute_step：步骤字段替换
"""

import pytest
from models.step_types import TestStep
from apps.test_runner.executors.api.executor import ApiExecutor


def _make_executor():
    """构造一个最小 ApiExecutor（不调 __init__，不接触适配器）。"""
    executor = ApiExecutor.__new__(ApiExecutor)
    executor._variables = {}
    executor._last_response = None
    return executor


# ═════════════════════════════════
# _resolve
# ═════════════════════════════════

class TestResolve:
    def test_single_variable(self):
        ex = _make_executor()
        ex._variables = {"token": "abc123"}
        assert ex._resolve("Bearer {{token}}") == "Bearer abc123"

    def test_multiple_variables(self):
        ex = _make_executor()
        ex._variables = {"host": "api.com", "port": "8080"}
        assert ex._resolve("http://{{host}}:{{port}}/path") == "http://api.com:8080/path"

    def test_unresolved_variable_stays_unchanged(self):
        ex = _make_executor()
        ex._variables = {}
        assert ex._resolve("{{missing}}") == "{{missing}}"

    def test_partial_resolution(self):
        """有的变量存在、有的不存在 → 存在的替换，不存在的不变。"""
        ex = _make_executor()
        ex._variables = {"host": "api.com"}
        assert ex._resolve("http://{{host}}/{{path}}") == "http://api.com/{{path}}"

    def test_no_variables_in_string(self):
        ex = _make_executor()
        ex._variables = {"host": "api.com"}
        assert ex._resolve("plain string") == "plain string"

    def test_non_string_passed_through(self):
        """非字符串输入原样返回。"""
        ex = _make_executor()
        assert ex._resolve(42) == 42
        assert ex._resolve(None) is None
        assert ex._resolve(["list"]) == ["list"]

    def test_empty_template(self):
        ex = _make_executor()
        assert ex._resolve("") == ""


# ═════════════════════════════════
# _resolve_with（类方法，不依赖实例）
# ═════════════════════════════════

class TestResolveWith:
    def test_resolves_from_provided_data(self):
        assert ApiExecutor._resolve_with({"name": "test"}, "Hello {{name}}") == "Hello test"

    def test_non_string_data_passed_through(self):
        assert ApiExecutor._resolve_with({}, 123) == 123


# ═════════════════════════════════
# _resolve_dict
# ═════════════════════════════════

class TestResolveDict:
    def test_resolves_values(self):
        ex = _make_executor()
        ex._variables = {"token": "abc"}
        result = ex._resolve_dict({"auth": "Bearer {{token}}"})
        assert result == {"auth": "Bearer abc"}

    def test_resolves_nested_dicts(self):
        ex = _make_executor()
        ex._variables = {"token": "x"}
        result = ex._resolve_dict({"headers": {"X-Token": "{{token}}"}})
        assert result == {"headers": {"X-Token": "x"}}

    def test_resolves_list_items(self):
        ex = _make_executor()
        ex._variables = {"host": "api.com"}
        result = ex._resolve_dict({"urls": ["http://{{host}}/a", "http://{{host}}/b"]})
        assert result == {"urls": ["http://api.com/a", "http://api.com/b"]}

    def test_empty_dict_returns_empty(self):
        ex = _make_executor()
        assert ex._resolve_dict({}) == {}


# ═════════════════════════════════
# _to_row_dicts
# ═════════════════════════════════

class TestToRowDicts:
    def test_columnar_to_row_wise(self):
        data = [
            {"key": "col1", "values": ["a", "b"]},
            {"key": "col2", "values": ["1", "2"]},
        ]
        rows = ApiExecutor._to_row_dicts(data)
        assert rows == [{"col1": "a", "col2": "1"}, {"col1": "b", "col2": "2"}]

    def test_single_column(self):
        data = [{"key": "endpoint", "values": ["login", "signup"]}]
        rows = ApiExecutor._to_row_dicts(data)
        assert rows == [{"endpoint": "login"}, {"endpoint": "signup"}]

    def test_unequal_length_pads_with_empty(self):
        data = [
            {"key": "col1", "values": ["a", "b", "c"]},
            {"key": "col2", "values": ["1"]},
        ]
        rows = ApiExecutor._to_row_dicts(data)
        assert len(rows) == 3
        assert rows[0] == {"col1": "a", "col2": "1"}
        assert rows[1] == {"col1": "b", "col2": ""}
        assert rows[2] == {"col1": "c", "col2": ""}

    def test_empty_input(self):
        assert ApiExecutor._to_row_dicts([]) == []

    def test_non_list_input(self):
        """None 等非法输入返回空列表。"""
        assert ApiExecutor._to_row_dicts(None) == []


# ═════════════════════════════════
# _split_rows
# ═════════════════════════════════

class TestSplitRows:
    def test_mixed_rows(self):
        rows = [
            {"kind": "input", "endpoint": "login"},
            {"kind": "validate", "$.status": "ok"},
        ]
        inputs, validates = ApiExecutor._split_rows(rows)
        assert len(inputs) == 1
        assert len(validates) == 1
        assert inputs[0]["endpoint"] == "login"
        assert validates[0]["$.status"] == "ok"

    def test_all_inputs(self):
        rows = [{"kind": "input", "a": "1"}, {"kind": "input", "a": "2"}]
        inputs, validates = ApiExecutor._split_rows(rows)
        assert len(inputs) == 2
        assert len(validates) == 0

    def test_all_validates(self):
        rows = [{"kind": "validate", "$.x": "1"}]
        inputs, validates = ApiExecutor._split_rows(rows)
        assert len(inputs) == 0
        assert len(validates) == 1

    def test_rows_without_kind_treated_as_input(self):
        rows = [{"endpoint": "login"}]
        inputs, validates = ApiExecutor._split_rows(rows)
        assert len(inputs) == 1
        assert len(validates) == 0


# ═════════════════════════════════
# _navigate_json
# ═════════════════════════════════

class TestNavigateJson:
    def test_root_path_returns_none(self):
        """已知缺陷：$ 路径 lstrip("$.") 后为空串，split 得到 [""]，get("") 返回 None。

        期望：$ 应返回整个对象。当前实现不支持。
        """
        result = ApiExecutor._navigate_json(None, {"a": 1}, "$")
        assert result is None  # 当前实际行为

    def test_single_key(self):
        result = ApiExecutor._navigate_json(None, {"name": "test"}, "$.name")
        assert result == "test"

    def test_nested_keys(self):
        obj = {"data": {"user": {"name": "test"}}}
        result = ApiExecutor._navigate_json(None, obj, "$.data.user.name")
        assert result == "test"

    def test_list_index(self):
        obj = {"items": [{"id": 1}, {"id": 2}]}
        result = ApiExecutor._navigate_json(None, obj, "$.items.1.id")
        assert result == 2

    def test_missing_key_returns_none(self):
        result = ApiExecutor._navigate_json(None, {"a": 1}, "$.b.c")
        assert result is None

    def test_non_dict_intermediate(self):
        """键路径中间遇到非 dict（如字符串），无法继续导航 → None。"""
        result = ApiExecutor._navigate_json(None, {"a": "string_value"}, "$.a.b")
        assert result is None

    def test_empty_path_returns_none(self):
        """$ 路径同 test_root_path_returns_none，当前实现不支持。"""
        result = ApiExecutor._navigate_json(None, {"x": 1}, "$")
        assert result is None


# ═════════════════════════════════
# _eval_json_path
# ═════════════════════════════════

class TestEvalJsonPath:
    def test_body_path(self):
        ex = _make_executor()
        result = ex._eval_json_path("$.data.token", '{"data":{"token":"abc"}}', {})
        assert result == "abc"

    def test_header_path(self):
        ex = _make_executor()
        result = ex._eval_json_path(
            "$.headers.x-csrf-token",
            "{}",
            {"x-csrf-token": "csrf123"},
        )
        assert result == "csrf123"

    def test_bad_json_body_returns_none(self):
        ex = _make_executor()
        result = ex._eval_json_path("$.data.token", "not-json", {})
        assert result is None


# ═════════════════════════════════
# _clone_steps
# ═════════════════════════════════

class TestCloneSteps:
    def test_returns_deep_copy(self):
        ex = _make_executor()
        original = [TestStep(type="click", description="btn")]
        cloned = ex._clone_steps(original)
        assert cloned[0].description == "btn"
        # 修改副本不影响原始
        cloned[0].description = "modified"
        assert original[0].description == "btn"


# ═════════════════════════════════
# _substitute_step
# ═════════════════════════════════

class TestSubstituteStep:
    def test_substitutes_url_header_body(self):
        ex = _make_executor()
        step = TestStep(
            type="api_request",
            url="/{{endpoint}}",
            headers={"Authorization": "Bearer {{token}}"},
            body={"user": "{{name}}"},
        )
        data = {"endpoint": "login", "token": "abc", "name": "admin"}
        ex._substitute_step(step, data)
        assert step.url == "/login"
        assert step.headers["Authorization"] == "Bearer abc"
        assert step.body["user"] == "admin"

    def test_no_substitution_without_placeholders(self):
        ex = _make_executor()
        step = TestStep(type="api_request", url="/login")
        data = {"token": "abc"}
        ex._substitute_step(step, data)
        assert step.url == "/login"
