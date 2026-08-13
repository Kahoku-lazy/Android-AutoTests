"""
ApiExecutor — executes API test case steps with variable resolution.

Mirrors StepExecutor pattern: receives adapter, dispatches by step.type,
emits step-level callbacks for WebSocket progress.
"""

import copy
import json
import re
import time

from models.step_types import TestStep
from models.test_models import TestCaseDef


class ApiExecutor:
    """Executes API test case steps sequentially with variable passing."""

    def __init__(self, adapter):
        """
        Args:
            adapter: ApiAdapter instance (with log/stopped/execute_case)
        """
        self.adapter = adapter
        self._variables: dict[str, str] = {}
        self._last_response: dict | None = None
        self._step_callback = None  # (step_index, total, type, description, result)
        self._step_started_callback = None  # (step_index, total, type, description)

    def _resolve(self, template: str) -> str:
        """Replace {{var}} placeholders with values from variables dict."""
        if not isinstance(template, str):
            return template

        def replacer(match):
            key = match.group(1)
            return str(self._variables.get(key, match.group(0)))

        return re.sub(r"\{\{(.+?)\}\}", replacer, template)

    def _resolve_dict(self, d: dict) -> dict:
        """Recursively resolve {{var}} in dict keys and values."""
        if not d:
            return d
        result: dict = {}
        for k, v in d.items():
            resolved_key = self._resolve(k) if isinstance(k, str) else k
            if isinstance(v, str):
                result[resolved_key] = self._resolve(v)
            elif isinstance(v, dict):
                result[resolved_key] = self._resolve_dict(v)
            elif isinstance(v, list):
                result[resolved_key] = [
                    self._resolve(item) if isinstance(item, str) else item for item in v
                ]
            else:
                result[resolved_key] = v
        return result

    def _extract_variables(self, extract_rules: dict):
        """Extract variables from the last API response using JSONPath rules.

        Args:
            extract_rules: {"var_name": "$.json.path"}
        """
        if not extract_rules or not self._last_response:
            return
        response_body = self._last_response.get("response_body", "")
        response_headers = self._last_response.get("response_headers", {})

        for var_name, json_path in extract_rules.items():
            if not isinstance(json_path, str):
                continue
            try:
                value = self._eval_json_path(json_path, response_body, response_headers)
                if value is not None:
                    self._variables[var_name] = str(value)
                    self.adapter.log(f"  ↳ extract: {var_name} = {value}")
            except Exception as e:
                self.adapter.log(f"  ⚠ extract {var_name} failed: {e}")

    def _eval_json_path(self, path: str, response_body: str, response_headers: dict) -> str | None:
        """Evaluate a simple JSONPath expression against response data."""
        # Support: $.data.token, $.headers.x-csrf-token
        if path.startswith("$.headers."):
            header_key = path[len("$.headers.") :]
            return response_headers.get(header_key)

        # Parse response body as JSON for $. paths
        try:
            body_obj = (
                json.loads(response_body) if isinstance(response_body, str) else response_body
            )
        except (json.JSONDecodeError, TypeError):
            return None

        if path == "$":
            return str(body_obj)

        # Navigate $.data.token, $.data.user.id etc.
        parts = path.lstrip("$.").split(".")
        current = body_obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None
            if current is None:
                return None
        return current

    @staticmethod
    def _to_row_dicts(rows: list) -> list[dict]:
        """Convert columnar rows [{key, values, kind}] to row-wise [{col: val}]."""
        if not rows:
            return []
        # Defensive: handle JSON-string that wasn't deserialized
        if isinstance(rows, str):
            try:
                rows = json.loads(rows)
            except Exception:
                import logging

                logging.getLogger("test_runner.api").exception(
                    "_to_row_dicts JSON parse failed — returning [], data-driven rows skipped"
                )
                return []
        if not isinstance(rows, list):
            return []
        keys = [r.get("key", "") for r in rows if isinstance(r, dict)]
        cols = [r.get("values", []) for r in rows if isinstance(r, dict)]
        max_len = max((len(c) for c in cols), default=0)
        result = []
        for i in range(max_len):
            row = {}
            for j, k in enumerate(keys):
                row[k] = cols[j][i] if i < len(cols[j]) else ""
            result.append(row)
        return result

    @staticmethod
    def _split_rows(rows: list) -> tuple:
        """Split rows into input and validate groups."""
        inputs = [r for r in rows if r.get("kind") != "validate"]
        validates = [r for r in rows if r.get("kind") == "validate"]
        return inputs, validates

    def _clone_steps(self, steps: list[TestStep]) -> list[TestStep]:
        """Deep-clone steps so per-row substitution doesn't mutate originals."""
        return copy.deepcopy(steps)

    def execute_case(self, case: TestCaseDef, iteration: int = 1, run_id: str = "") -> str:
        """Execute an API test case step by step.

        Supports data-driven testing: if extra_data._rows is present,
        each row becomes a separate sub-iteration with {{var}} substitution.
        """
        extra = getattr(case, "extra_data", {}) or {}
        rows = self._to_row_dicts(extra.get("_rows", []))

        if case.steps_data:
            base_steps: list[TestStep] = case.steps_data
        elif extra:
            base_steps = [self._auto_build_step(case, extra)]
        else:
            self.adapter.log(f"Error: no steps for '{case.title}'")
            return "fail"

        if not rows:
            return self._execute_steps(base_steps)

        # ── Data-driven: iterate over each row ──
        input_rows, validate_rows = self._split_rows(extra.get("_rows", []))
        validate_cols = [r for r in validate_rows if r.get("key")]
        all_pass = True
        for ri, row_data in enumerate(rows):
            if self.adapter.stopped():
                return "stopped"
            self.adapter.log(f"Data row {ri + 1}/{len(rows)}: {row_data}")
            steps = self._clone_steps(base_steps)
            for step in steps:
                self._substitute_step(step, row_data)
            self._variables.clear()
            self._last_response = None
            result = self._execute_steps(steps)

            # ── Validate response fields ──
            if result == "pass" and validate_cols and self._last_response:
                for vc in validate_cols:
                    path = vc.get("key", "")
                    expected_val = str(row_data.get(path, "") or "")
                    if not path or not expected_val:
                        continue
                    body = self._last_response.get("response_body", "")
                    headers = self._last_response.get("response_headers", {})
                    actual_val = self._eval_json_path(path, body, headers)
                    actual_str = str(actual_val) if actual_val is not None else ""
                    if actual_val is None or actual_str != expected_val:
                        self.adapter.log(
                            f"Validation FAIL: {path} expected='{expected_val}' actual='{actual_str}'"
                        )
                        result = "fail"
                    else:
                        self.adapter.log(f"Validation OK: {path} = '{expected_val}'")

            if result != "pass":
                all_pass = False
                self.adapter.log(f"Data row {ri + 1} FAILED, continuing...")
        return "pass" if all_pass else "fail"

    def _execute_steps(self, steps: list[TestStep]) -> str:
        """Execute a list of steps and return pass/fail/stopped."""
        total = len(steps)
        for i, step in enumerate(steps):
            if self.adapter.stopped():
                return "stopped"
            step_desc = step.description or f"{step.type}: {step.url or step.xpath}"
            if self._step_started_callback:
                self._step_started_callback(i, total, step.type, step_desc[:100])
            result = self._dispatch(step, i, total)
            if self._step_callback:
                self._step_callback(i, total, step.type, step_desc[:100], result)
            if result != "pass":
                return result
        return "pass"

    @staticmethod
    def _resolve_with(data: dict, template: str) -> str:
        """Replace {{key}} placeholders using the given data dict."""
        if not isinstance(template, str):
            return template

        def replacer(match):
            key = match.group(1)
            return str(data.get(key, match.group(0)))

        return re.sub(r"\{\{(.+?)\}\}", replacer, template)

    @classmethod
    def _resolve_dict_with(cls, data: dict, d: dict) -> dict:
        """Recursively resolve {{key}} in dict using the given data source."""
        if not d:
            return d
        result: dict = {}
        for k, v in d.items():
            rk = cls._resolve_with(data, k) if isinstance(k, str) else k
            if isinstance(v, str):
                result[rk] = cls._resolve_with(data, v)
            elif isinstance(v, dict):
                result[rk] = cls._resolve_dict_with(data, v)
            elif isinstance(v, list):
                result[rk] = [cls._resolve_with(data, x) if isinstance(x, str) else x for x in v]
            else:
                result[rk] = v
        return result

    def _substitute_step(self, step: TestStep, data: dict):
        """Replace {{key}} placeholders in step fields with data values."""
        if step.url:
            step.url = self._resolve_with(data, step.url)
        if step.body and isinstance(step.body, dict):
            step.body = self._resolve_dict_with(data, step.body)
        if step.headers and isinstance(step.headers, dict):
            step.headers = self._resolve_dict_with(data, step.headers)
        if step.expected_text:
            step.expected_text = self._resolve_with(data, step.expected_text)
        if step.value:
            step.value = self._resolve_with(data, step.value)

    def _auto_build_step(self, case: TestCaseDef, extra: dict) -> TestStep:
        """Build a single api_request step from legacy flat fields."""
        headers_str = extra.get("headers", "")
        body_str = extra.get("body", "")
        headers: dict = {}
        body: dict = {}
        if isinstance(headers_str, str) and headers_str.strip():
            try:
                headers = json.loads(headers_str)
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(headers_str, dict):
            headers = headers_str
        if isinstance(body_str, str) and body_str.strip():
            try:
                parsed = json.loads(body_str)
                if isinstance(parsed, dict):
                    body = parsed
            except (json.JSONDecodeError, TypeError):
                pass  # JSON parse failed — TestStep.body must be dict, leave as {}
        elif isinstance(body_str, dict):
            body = body_str

        return TestStep(
            type="api_request",
            method=extra.get("method", "GET"),
            url=extra.get("url", ""),
            headers=headers,
            body=body,
            expected_text=extra.get("expected_response", ""),
            description=f"Auto-built: {extra.get('method', 'GET')} {extra.get('url', '')}",
        )

    def _dispatch(self, step: TestStep, idx: int, total: int) -> str:
        """Dispatch step by type."""
        handlers = {
            "api_request": self._do_request,
            "api_assert": self._do_assert,
            "api_sleep": self._do_sleep,
            "api_log": self._do_log,
        }
        handler = handlers.get(step.type)
        if handler:
            return handler(step)
        self.adapter.log(f"Unknown API step type: {step.type}")
        return "fail"

    # ── Step handlers ──

    def _do_request(self, s: TestStep) -> str:
        # Resolve variables in-place before passing to adapter
        if s.url:
            s.url = self._resolve(s.url)
        if s.xpath:
            s.xpath = self._resolve(s.xpath)
        if s.headers:
            s.headers = self._resolve_dict(dict(s.headers))
        if s.body:
            s.body = self._resolve_dict(dict(s.body))

        result = self.adapter.execute_step(s)

        if not isinstance(result, dict):
            return str(result) if isinstance(result, str) else "fail"

        # Store response for variable extraction
        self._last_response = {
            "status_code": result.get("status_code", 0),
            "response_body": result.get("response_body", ""),
            "response_headers": result.get("response_headers", {}),
            "duration_ms": result.get("duration_ms", 0),
        }

        # Extract variables if step has extract rules
        if s.extract:
            self._extract_variables(dict(s.extract))

        return result.get("result", "fail")

    def _do_assert(self, s: TestStep) -> str:
        if not self._last_response:
            self.adapter.log("Assert: no previous response to validate")
            return "fail"

        assertions = list(s.assertions) if s.assertions else []
        if not assertions:
            # Simple status check
            status = self._last_response.get("status_code", 0)
            expected = s.expected_status
            if expected and status != expected:
                self.adapter.log(f"Assert FAIL: expected status {expected}, got {status}")
                return "fail"
            return "pass"

        # Run custom assertions against last response
        response_body = self._last_response.get("response_body", "")
        try:
            body_obj = (
                json.loads(response_body) if isinstance(response_body, str) else response_body
            )
        except (json.JSONDecodeError, TypeError):
            body_obj = response_body

        for a in assertions:
            a_type = a.get("type", "")
            path = a.get("path", "")
            # Support both naming conventions: "op"/"expect" (from steps_json) and "operator"/"expected"
            operator = a.get("op") or a.get("operator", "equals")
            expected = a.get("expect")
            if expected is None:
                expected = a.get("expected", "")

            if a_type == "response_time":
                max_ms = float(expected or 5000)
                duration = self._last_response.get("duration_ms", 0)
                if duration > max_ms:
                    self.adapter.log(f"Assert FAIL: response time {duration}ms > {max_ms}ms")
                    return "fail"
            elif path:
                # Navigate JSON path
                actual = self._navigate_json(body_obj, path)
                resolved_expected = self._resolve(str(expected))

                if operator == "equals" and str(actual) != resolved_expected:
                    self.adapter.log(
                        f"Assert FAIL: {path} expected '{resolved_expected}', got '{actual}'"
                    )
                    return "fail"
                elif operator == "contains" and resolved_expected not in str(actual):
                    self.adapter.log(f"Assert FAIL: {path} does not contain '{resolved_expected}'")
                    return "fail"
                elif operator == "greater_than" and float(actual or 0) <= float(
                    resolved_expected or 0
                ):
                    self.adapter.log(
                        f"Assert FAIL: {path} expected > {resolved_expected}, got {actual}"
                    )
                    return "fail"

        self.adapter.log(f"Assert PASS: {len(assertions)} assertions")
        return "pass"

    def _navigate_json(self, obj, path: str):
        """Navigate a dotted path into a JSON object."""
        parts = path.lstrip("$.").split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)] if int(part) < len(current) else None
            else:
                return None
        return current

    def _do_sleep(self, s: TestStep) -> str:
        timeout = s.timeout if s.timeout is not None else 1
        self.adapter.log(f"Sleep {timeout}s")
        # Interruptible sleep
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.adapter.stopped():
                return "stopped"
            time.sleep(0.1)
        return "pass"

    def _do_log(self, s: TestStep) -> str:
        self.adapter.log(s.description or "---")
        return "pass"
