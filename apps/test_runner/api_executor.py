"""
ApiExecutor — executes API test case steps with variable resolution.

Mirrors StepExecutor pattern: receives adapter, dispatches by step.type,
emits step-level callbacks for WebSocket progress.
"""
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
        self._step_callback = None      # (step_index, total, type, description, result)
        self._step_started_callback = None  # (step_index, total, type, description)

    def _resolve(self, template: str) -> str:
        """Replace {{var}} placeholders with values from variables dict."""
        if not isinstance(template, str):
            return template
        def replacer(match):
            key = match.group(1)
            return str(self._variables.get(key, match.group(0)))
        return re.sub(r'\{\{(.+?)\}\}', replacer, template)

    def _resolve_dict(self, d: dict) -> dict:
        """Recursively resolve {{var}} in dict keys and values."""
        if not d:
            return d
        result = {}
        for k, v in d.items():
            resolved_key = self._resolve(k) if isinstance(k, str) else k
            if isinstance(v, str):
                result[resolved_key] = self._resolve(v)
            elif isinstance(v, dict):
                result[resolved_key] = self._resolve_dict(v)
            elif isinstance(v, list):
                result[resolved_key] = [
                    self._resolve(item) if isinstance(item, str) else item
                    for item in v
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
            header_key = path[len("$.headers."):]
            return response_headers.get(header_key)

        # Parse response body as JSON for $. paths
        try:
            body_obj = json.loads(response_body) if isinstance(response_body, str) else response_body
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

    def execute_case(self, case: TestCaseDef, iteration: int = 1) -> str:
        """Execute an API test case step by step.

        Args:
            case: TestCaseDef — prefers steps_data (from steps_json),
                  falls back to extra_data for single-step auto-build.
            iteration: current iteration number

        Returns: "pass" | "fail" | "stopped"
        """
        # ── Resolve steps: priority to steps_json, fallback to flat fields ──
        extra = getattr(case, 'extra_data', {}) or {}

        if case.steps_data:
            steps: list[TestStep] = case.steps_data
        elif extra:
            # Auto-build single step from flat fields (backward compat)
            steps = [self._auto_build_step(case, extra)]
        else:
            self.adapter.log(f"Error: no steps for '{case.title}'")
            return "fail"

        total = len(steps)
        self._variables.clear()
        self._last_response = None

        for i, step in enumerate(steps):
            if self.adapter.stopped():
                return "stopped"

            step_desc = step.description or f"{step.type}: {step.url or step.xpath}"
            if self._step_started_callback:
                self._step_started_callback(i, total, step.type, step_desc[:100])

            result = self._dispatch(step, i, total)

            if self._step_callback:
                self._step_callback(i, total, step.type, step_desc[:100], result)

            if result == "fail":
                return "fail"
            if result == "stopped":
                return "stopped"

        return "pass"

    def _auto_build_step(self, case: TestCaseDef, extra: dict) -> TestStep:
        """Build a single api_request step from legacy flat fields."""
        headers_str = extra.get("headers", "")
        body_str = extra.get("body", "")
        headers = {}
        body = {}
        if isinstance(headers_str, str) and headers_str.strip():
            try:
                headers = json.loads(headers_str)
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(headers_str, dict):
            headers = headers_str
        if isinstance(body_str, str) and body_str.strip():
            try:
                body = json.loads(body_str)
            except (json.JSONDecodeError, TypeError):
                body = body_str
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

    def _build_case_dict(self, s: TestStep) -> dict:
        """Convert a TestStep to a dict for legacy adapters lacking execute_step."""
        return {
            "type": s.type, "url": s.url, "method": s.method or s.xpath or "GET",
            "headers": dict(s.headers) if s.headers else {},
            "body": dict(s.body) if s.body else "",
            "timeout": s.timeout or 30,
            "expected_status": s.expected_status or 200,
            "expected_response": s.expected_response or "",
            "assertions": s.assertions if s.assertions else [],
        }

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

        result = self.adapter.execute_step(s) if hasattr(self.adapter, 'execute_step') \
            else self.adapter.execute_case(self._build_case_dict(s))

        # Guard: legacy adapters may return str (e.g. "pass"/"fail") instead of dict
        if not isinstance(result, dict):
            return str(result) if isinstance(result, str) else "fail"

        # Store response for variable extraction
        self._last_response = {
            "status_code": result.get("status_code", 0),
            "response_body": result.get("response_body", ""),
            "response_headers": result.get("response_headers", {}),
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
            body_obj = json.loads(response_body) if isinstance(response_body, str) else response_body
        except (json.JSONDecodeError, TypeError):
            body_obj = response_body

        for a in assertions:
            a_type = a.get("type", "")
            path = a.get("path", "")
            operator = a.get("operator", "equals")
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
                    self.adapter.log(f"Assert FAIL: {path} expected '{resolved_expected}', got '{actual}'")
                    return "fail"
                elif operator == "contains" and resolved_expected not in str(actual):
                    self.adapter.log(f"Assert FAIL: {path} does not contain '{resolved_expected}'")
                    return "fail"
                elif operator == "greater_than" and float(actual or 0) <= float(resolved_expected or 0):
                    self.adapter.log(f"Assert FAIL: {path} expected > {resolved_expected}, got {actual}")
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
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            if self.adapter.stopped():
                return "stopped"
            _time.sleep(0.1)
        return "pass"

    def _do_log(self, s: TestStep) -> str:
        self.adapter.log(s.description or "---")
        return "pass"
