"""
API adapter — executes HTTP requests for API test cases.
Provides a compatible interface for the test runner to use instead of DeviceAdapter.
"""
import time
import json
import requests as _requests
from models.step_types import TestStep


class ApiAdapter:
    """Executes API test cases via HTTP requests.

    Provides the minimal interface needed by the test runner:
    - execute_case(case_def) -> dict with result/status/duration/response
    - log(), stopped(), get_log_buffer(), clear_log_buffer()
    """

    def __init__(self, base_url: str = "", logger: callable = None, should_stop: callable = None):
        self.base_url = base_url
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._log_buffer: list[str] = []
        self._step_callback = None
        self._step_started_callback = None

    def _resolve_url(self, url: str) -> str:
        """If url is relative, prepend base_url. Absolute URLs pass through."""
        if not url:
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base = self.base_url.rstrip("/") if self.base_url else ""
        return f"{base}{url}" if url.startswith("/") else f"{base}/{url}"

    def log(self, msg: str):
        self._emit_log(msg)
        self._log_buffer.append(msg)

    def clear_log_buffer(self):
        self._log_buffer.clear()

    def get_log_buffer(self) -> list[str]:
        return list(self._log_buffer)

    def stopped(self) -> bool:
        return self._should_stop()

    def _http_request(self, http_method: str, url: str, headers: dict,
                      body_bytes: bytes | None, timeout: int = 30) -> tuple:
        """Perform HTTP request, return (status_code, response_text, response_headers_dict)."""
        resp = _requests.request(
            method=http_method, url=url, headers=headers,
            data=body_bytes, timeout=timeout, allow_redirects=True,
        )
        return resp.status_code, resp.text, dict(resp.headers)

    def execute_case(self, case: dict) -> dict:
        """Execute a single API test case (legacy dict interface)."""
        if self.stopped():
            return {"result": "stopped", "status_code": 0, "response_body": "",
                    "response_headers": {}, "duration_ms": 0, "detail": "Execution stopped"}

        http_method = case.get("http_method", "GET").upper()
        url = self._resolve_url(case.get("url", ""))
        headers = case.get("headers", {}) or {}
        query_params = case.get("query_params", {}) or {}
        request_body = case.get("request_body", {}) or {}
        expected_status = case.get("expected_status", 200)
        expected_response = case.get("expected_response", {}) or {}
        assertions = case.get("assertions", []) or []

        if query_params:
            from urllib.parse import urlencode
            sep = "&" if "?" in url else "?"
            url = url + sep + urlencode(query_params)

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
            status_code, response_text, response_headers = self._http_request(
                http_method, url, headers, body_bytes)
            duration_ms = (time.time() - start) * 1000

            if expected_status > 0 and status_code != expected_status:
                self.log(f"FAIL: expected status {expected_status}, got {status_code}")
                return _fail(status_code, response_text[:2000], duration_ms,
                             f"Expected HTTP {expected_status}, got {status_code}", response_headers,
                             self._build_diagnostics(http_method, url, headers, request_body,
                                                     status_code, response_text, duration_ms))

            if expected_response:
                try:
                    expected_obj = (expected_response if isinstance(expected_response, dict)
                                    else json.loads(expected_response))
                    actual_obj = json.loads(response_text)
                    if expected_obj != actual_obj:
                        self.log("FAIL: response body mismatch")
                        return _fail(status_code, response_text[:2000], duration_ms,
                                     "Response body does not match expected", response_headers,
                                     self._build_diagnostics(http_method, url, headers, request_body,
                                                             status_code, response_text, duration_ms))
                except json.JSONDecodeError:
                    if response_text.strip() != str(expected_response).strip():
                        return _fail(status_code, response_text[:2000], duration_ms,
                                     "Response text does not match expected", response_headers,
                                     self._build_diagnostics(http_method, url, headers, request_body,
                                                             status_code, response_text, duration_ms))

            for a in assertions:
                a_type = a.get("type", "")
                expected = a.get("expect") if "expect" in a else a.get("expected", "")
                if a_type == "response_time" and duration_ms > float(expected or 5000):
                    self.log(f"FAIL: response time {duration_ms:.0f}ms > {expected}ms")
                    return _fail(status_code, response_text[:2000], duration_ms,
                                 f"Response time {duration_ms:.0f}ms exceeds {expected}ms",
                                 response_headers,
                                 self._build_diagnostics(http_method, url, headers, request_body,
                                                         status_code, response_text, duration_ms))

            self.log(f"PASS: {http_method} {url} -> {status_code} ({duration_ms:.0f}ms)")
            return {"result": "pass", "status_code": status_code, "response_body": response_text[:2000],
                    "response_headers": response_headers, "duration_ms": round(duration_ms, 1), "detail": ""}

        except _requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: Connection error - {e}")
            return _fail(0, "", duration_ms, f"Connection failed: {e}", {},
                         self._build_diagnostics(http_method, url, headers, request_body, 0, "", duration_ms))
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            return _fail(0, "", duration_ms, str(e), {},
                         self._build_diagnostics(http_method, url, headers, request_body, 0, "", duration_ms))

    def execute_step(self, step: TestStep) -> dict:
        """Execute a single API request from a TestStep object (canonical interface)."""
        if self.stopped():
            return {"result": "stopped", "status_code": 0, "response_body": "",
                    "response_headers": {}, "duration_ms": 0, "detail": "Execution stopped"}

        http_method = (step.method or "GET").upper()
        url = self._resolve_url(step.url or step.xpath)
        headers = dict(step.headers) if step.headers else {}
        request_body = dict(step.body) if step.body else {}
        expected_status = step.expected_status
        expected_response = step.expected_text or ""
        assertions = list(step.assertions) if step.assertions else []

        body_bytes = None
        if http_method in ("POST", "PUT", "PATCH") and request_body:
            body_bytes = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        self.log(f"API {http_method} {url}")
        start = time.time()
        response_headers = {}

        try:
            status_code, response_text, response_headers = self._http_request(
                http_method, url, headers, body_bytes)
            duration_ms = (time.time() - start) * 1000

            if expected_status > 0 and status_code != expected_status:
                self.log(f"FAIL: expected status {expected_status}, got {status_code}")
                return _fail(status_code, response_text, duration_ms,
                             f"Status mismatch: expected {expected_status} got {status_code}",
                             response_headers,
                             self._build_diagnostics(http_method, url, headers, request_body,
                                                     status_code, response_text, duration_ms))

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
                    return _fail(status_code, response_text, duration_ms,
                                 f"Response mismatch: expected={expected_json}, actual={actual_json}",
                                 response_headers,
                                 self._build_diagnostics(http_method, url, headers, request_body,
                                                         status_code, response_text, duration_ms))

            for a in assertions:
                path = a.get("path", "")
                operator = a.get("op") or a.get("operator", "equals")
                expected = a.get("expect") if "expect" in a else a.get("value") if "value" in a else a.get("expected", "")
                try:
                    actual_val = json.loads(response_text)
                    for part in path.lstrip("$.").split("."):
                        if isinstance(actual_val, dict): actual_val = actual_val.get(part)
                        elif isinstance(actual_val, list) and part.isdigit(): actual_val = actual_val[int(part)]
                        else: actual_val = None; break
                except Exception:
                    actual_val = None
                if operator == "equals" and str(actual_val) != str(expected):
                    return _fail(status_code, response_text, duration_ms,
                                 f"Assertion failed: {path} {operator} {expected} (actual={actual_val})",
                                 response_headers,
                                 self._build_diagnostics(http_method, url, headers, request_body,
                                                         status_code, response_text, duration_ms))
                if operator == "contains" and str(expected) not in str(actual_val or ""):
                    return _fail(status_code, response_text, duration_ms,
                                 f"Assertion failed: {path} contains {expected}",
                                 response_headers,
                                 self._build_diagnostics(http_method, url, headers, request_body,
                                                         status_code, response_text, duration_ms))

            self.log(f"PASS ({duration_ms:.0f}ms)")
            return {"result": "pass", "status_code": status_code, "response_body": response_text,
                    "response_headers": response_headers, "duration_ms": duration_ms,
                    "detail": f"HTTP {status_code} ({duration_ms:.0f}ms)"}

        except _requests.exceptions.HTTPError as e:
            duration_ms = (time.time() - start) * 1000
            status_code = e.response.status_code if e.response is not None else 0
            error_body = e.response.text if e.response is not None else ""
            response_headers = dict(e.response.headers) if e.response is not None else {}
            if expected_status > 0 and status_code == expected_status:
                self.log(f"PASS: HTTP {status_code} (expected) ({duration_ms:.0f}ms)")
                return {"result": "pass", "status_code": status_code, "response_body": error_body,
                        "response_headers": response_headers, "duration_ms": duration_ms,
                        "detail": f"HTTP {status_code} (expected) ({duration_ms:.0f}ms)"}
            self.log(f"FAIL: HTTP {status_code} {e}")
            return _fail(status_code, error_body, duration_ms, f"HTTP {status_code}: {e}",
                         response_headers,
                         self._build_diagnostics(http_method, url, headers, request_body,
                                                 status_code, error_body, duration_ms))
        except _requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: Connection error - {e}")
            return _fail(0, "", duration_ms, f"Connection failed: {e}", {},
                         self._build_diagnostics(http_method, url, headers, request_body, 0, "", duration_ms))
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            return _fail(0, "", duration_ms, str(e), {},
                         self._build_diagnostics(http_method, url, headers, request_body, 0, "", duration_ms))

    def _build_diagnostics(self, method: str, url: str, headers: dict,
                           body, status_code: int, response_text: str,
                           duration_ms: float) -> dict:
        header_str = " ".join(f'-H "{k}: {v}"' for k, v in (headers or {}).items())
        body_str = ""
        if body:
            if isinstance(body, dict): body_str = f" -d '{json.dumps(body, ensure_ascii=False)}'"
            elif isinstance(body, str) and body.strip(): body_str = f" -d '{body}'"
        return {
            "curl_command": f"curl -X {method} '{url}' {header_str}{body_str}",
            "request": {"method": method, "url": url, "headers": headers, "body": body},
            "response": {"status": status_code, "body": (response_text or "")[:2000]},
            "duration_ms": round(duration_ms, 1),
        }


def _fail(status_code: int, response_body: str, duration_ms: float,
          detail: str, response_headers: dict, diagnostics: dict | None = None) -> dict:
    result = {"result": "fail", "status_code": status_code, "response_body": response_body,
              "response_headers": response_headers, "duration_ms": round(duration_ms, 1), "detail": detail}
    if diagnostics: result["diagnostics"] = diagnostics
    return result
