"""
API adapter — executes HTTP requests for API test cases.
Provides a compatible interface for the test runner to use instead of DeviceAdapter.
"""
import time
import json
import urllib.request
import urllib.error
from models.step_types import TestStep


class ApiAdapter:
    """Executes API test cases via HTTP requests.

    Provides the minimal interface needed by the test runner:
    - execute_case(case_def) -> dict with result/status/duration/response
    - log(), stopped(), get_log_buffer(), clear_log_buffer()
    """

    def __init__(self, logger: callable = None, should_stop: callable = None):
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._log_buffer: list[str] = []
        self._step_callback = None
        self._step_started_callback = None

    def log(self, msg: str):
        self._emit_log(msg)
        self._log_buffer.append(msg)

    def clear_log_buffer(self):
        self._log_buffer.clear()

    def get_log_buffer(self) -> list[str]:
        return list(self._log_buffer)

    def stopped(self) -> bool:
        return self._should_stop()

    def execute_case(self, case: dict) -> dict:
        """Execute a single API test case.

        Args:
            case: dict with keys:
                id, title, http_method, url, headers, query_params, request_body,
                expected_status, expected_response, assertions, pre_script, post_script

        Returns:
            {"result": "pass"|"fail"|"stopped", "status_code": int,
             "response_body": str, "response_headers": dict, "duration_ms": float,
             "detail": str, "diagnostics": dict|None}
        """
        if self.stopped():
            return {"result": "stopped", "status_code": 0, "response_body": "",
                    "response_headers": {}, "duration_ms": 0, "detail": "Execution stopped"}

        http_method = case.get("http_method", "GET").upper()
        url = case.get("url", "")
        headers = case.get("headers", {}) or {}
        query_params = case.get("query_params", {}) or {}
        request_body = case.get("request_body", {}) or {}
        expected_status = case.get("expected_status", 200)
        expected_response = case.get("expected_response", {}) or {}
        assertions = case.get("assertions", []) or []

        # Build URL with query params
        if query_params:
            from urllib.parse import urlencode
            sep = "&" if "?" in url else "?"
            url = url + sep + urlencode(query_params)

        # Prepare request body
        body_bytes = None
        if http_method in ("POST", "PUT", "PATCH") and request_body:
            if isinstance(request_body, dict):
                body_bytes = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
                headers.setdefault("Content-Type", "application/json")
            elif isinstance(request_body, str):
                body_bytes = request_body.encode("utf-8")

        self.log(f"API {http_method} {url}")
        start = time.time()
        response_headers = {}

        try:
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method=http_method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                response_text = resp.read().decode("utf-8", errors="replace")
                response_headers = dict(resp.getheaders())

            duration_ms = (time.time() - start) * 1000

            # Check status code
            if expected_status > 0 and status_code != expected_status:
                self.log(f"FAIL: expected status {expected_status}, got {status_code}")
                diag = self._build_diagnostics(http_method, url, headers, request_body,
                                               status_code, response_text, duration_ms)
                return _fail(status_code, response_text[:2000], duration_ms,
                             f"Expected HTTP {expected_status}, got {status_code}",
                             response_headers, diag)

            # Check response body
            if expected_response:
                try:
                    expected_obj = (expected_response if isinstance(expected_response, dict)
                                    else json.loads(expected_response))
                    actual_obj = json.loads(response_text)
                    if expected_obj != actual_obj:
                        self.log("FAIL: response body mismatch")
                        diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                       status_code, response_text, duration_ms)
                        return _fail(status_code, response_text[:2000], duration_ms,
                                     "Response body does not match expected",
                                     response_headers, diag)
                except json.JSONDecodeError:
                    if response_text.strip() != str(expected_response).strip():
                        diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                       status_code, response_text, duration_ms)
                        return _fail(status_code, response_text[:2000], duration_ms,
                                     "Response text does not match expected",
                                     response_headers, diag)

            # Custom assertions
            for a in assertions:
                a_type = a.get("type", "")
                expected = a.get("expected", "")
                if a_type == "response_time" and duration_ms > float(expected or 5000):
                    self.log(f"FAIL: response time {duration_ms:.0f}ms > {expected}ms")
                    diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                   status_code, response_text, duration_ms)
                    return _fail(status_code, response_text[:2000], duration_ms,
                                 f"Response time {duration_ms:.0f}ms exceeds {expected}ms",
                                 response_headers, diag)

            self.log(f"PASS: {http_method} {url} -> {status_code} ({duration_ms:.0f}ms)")
            return {
                "result": "pass",
                "status_code": status_code,
                "response_body": response_text[:2000],
                "response_headers": response_headers,
                "duration_ms": round(duration_ms, 1),
                "detail": "",
            }

        except urllib.error.HTTPError as e:
            duration_ms = (time.time() - start) * 1000
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")[:2000]
            except Exception:
                pass
            self.log(f"FAIL: HTTP {e.code} {e.reason}")
            diag = self._build_diagnostics(http_method, url, headers, request_body,
                                           e.code, error_body, duration_ms)
            return _fail(e.code, error_body, duration_ms,
                         f"HTTP {e.code}: {e.reason}", response_headers, diag)
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            diag = self._build_diagnostics(http_method, url, headers, request_body,
                                           0, "", duration_ms)
            return _fail(0, "", duration_ms, str(e), response_headers, diag)

    def execute_step(self, step: TestStep) -> dict:
        """Execute a single API request from a TestStep object (preferred).

        This is the canonical interface for ApiExecutor._do_request().
        The older execute_case(case: dict) is kept for backward compatibility.
        """
        if self.stopped():
            return {"result": "stopped", "status_code": 0, "response_body": "",
                    "response_headers": {}, "duration_ms": 0, "detail": "Execution stopped"}

        http_method = (step.method or "GET").upper()
        url = step.url or step.xpath
        headers = dict(step.headers) if step.headers else {}
        request_body = dict(step.body) if step.body else {}
        expected_status = step.expected_status
        expected_response = step.expected_text or ""
        assertions = list(step.assertions) if step.assertions else []

        # Build URL with query params (query_params not in TestStep; pass via body for GET)
        # Prepare request body
        body_bytes = None
        if http_method in ("POST", "PUT", "PATCH") and request_body:
            body_bytes = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        self.log(f"API {http_method} {url}")
        start = time.time()
        response_headers = {}

        try:
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method=http_method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                response_text = resp.read().decode("utf-8", errors="replace")
                response_headers = dict(resp.getheaders())

            duration_ms = (time.time() - start) * 1000

            # Check status code
            if expected_status > 0 and status_code != expected_status:
                self.log(f"FAIL: expected status {expected_status}, got {status_code}")
                diag = self._build_diagnostics(http_method, url, headers, request_body,
                                               status_code, response_text, duration_ms)
                return _fail(status_code, response_text, duration_ms,
                             f"Status mismatch: expected {expected_status} got {status_code}",
                             response_headers, diag)

            # Validate response body if provided
            if expected_response:
                try:
                    expected_json = json.loads(expected_response) if isinstance(expected_response, str) else expected_response
                except (json.JSONDecodeError, TypeError):
                    expected_json = expected_response
                try:
                    actual_json = json.loads(response_text)
                except (json.JSONDecodeError, TypeError):
                    actual_json = response_text
                if expected_json != actual_json:
                    diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                   status_code, response_text, duration_ms)
                    return _fail(status_code, response_text, duration_ms,
                                 f"Response mismatch: expected={expected_json}, actual={actual_json}",
                                 response_headers, diag)

            # Run custom assertions
            for a in assertions:
                path = a.get("path", "")
                operator = a.get("operator", "equals")
                expected = a.get("value")
                try:
                    actual_val = json.loads(response_text)
                    for part in path.lstrip("$.").split("."):
                        if isinstance(actual_val, dict):
                            actual_val = actual_val.get(part)
                        elif isinstance(actual_val, list) and part.isdigit():
                            actual_val = actual_val[int(part)]
                        else:
                            actual_val = None
                            break
                except Exception:
                    actual_val = None
                if operator == "equals" and actual_val != expected:
                    diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                   status_code, response_text, duration_ms)
                    return _fail(status_code, response_text, duration_ms,
                                 f"Assertion failed: {path} {operator} {expected} (actual={actual_val})",
                                 response_headers, diag)
                if operator == "contains" and str(expected) not in str(actual_val or ""):
                    diag = self._build_diagnostics(http_method, url, headers, request_body,
                                                   status_code, response_text, duration_ms)
                    return _fail(status_code, response_text, duration_ms,
                                 f"Assertion failed: {path} contains {expected}",
                                 response_headers, diag)

            self.log(f"PASS ({duration_ms:.0f}ms)")
            return {
                "result": "pass", "status_code": status_code,
                "response_body": response_text, "response_headers": response_headers,
                "duration_ms": duration_ms, "detail": f"HTTP {status_code} ({duration_ms:.0f}ms)",
            }

        except urllib.error.HTTPError as e:
            duration_ms = (time.time() - start) * 1000
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""
            response_headers = dict(e.headers) if e.headers else {}
            # If the HTTP error code matches expected_status, treat as pass
            if expected_status > 0 and e.code == expected_status:
                self.log(f"PASS: HTTP {e.code} (expected) ({duration_ms:.0f}ms)")
                return {
                    "result": "pass", "status_code": e.code,
                    "response_body": error_body, "response_headers": response_headers,
                    "duration_ms": duration_ms,
                    "detail": f"HTTP {e.code} (expected) ({duration_ms:.0f}ms)",
                }
            self.log(f"FAIL: HTTP {e.code} {e.reason}")
            diag = self._build_diagnostics(http_method, url, headers, request_body,
                                           e.code, error_body, duration_ms)
            return _fail(e.code, error_body, duration_ms,
                         f"HTTP {e.code}: {e.reason}", response_headers, diag)
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            diag = self._build_diagnostics(http_method, url, headers, request_body,
                                           0, "", duration_ms)
            return _fail(0, "", duration_ms, str(e), response_headers, diag)

    def _build_diagnostics(self, method: str, url: str, headers: dict,
                           body, status_code: int, response_text: str,
                           duration_ms: float) -> dict:
        """Build failure diagnostics including cURL command."""
        header_str = " ".join(f'-H "{k}: {v}"' for k, v in (headers or {}).items())
        body_str = ""
        if body:
            if isinstance(body, dict):
                body_str = f" -d '{json.dumps(body, ensure_ascii=False)}'"
            elif isinstance(body, str) and body.strip():
                body_str = f" -d '{body}'"
        return {
            "curl_command": f"curl -X {method} '{url}' {header_str}{body_str}",
            "request": {
                "method": method, "url": url,
                "headers": headers, "body": body,
            },
            "response": {
                "status": status_code,
                "body": (response_text or "")[:2000],
            },
            "duration_ms": round(duration_ms, 1),
        }


def _fail(status_code: int, response_body: str, duration_ms: float,
          detail: str, response_headers: dict,
          diagnostics: dict | None = None) -> dict:
    result = {
        "result": "fail",
        "status_code": status_code,
        "response_body": response_body,
        "response_headers": response_headers,
        "duration_ms": round(duration_ms, 1),
        "detail": detail,
    }
    if diagnostics:
        result["diagnostics"] = diagnostics
    return result
