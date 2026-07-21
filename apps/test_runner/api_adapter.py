"""
API adapter — executes HTTP requests for API test cases.
Provides a compatible interface for the test runner to use instead of DeviceAdapter.
"""
import time
import json
import urllib.request
import urllib.error


class ApiAdapter:
    """Executes API test cases via HTTP requests.

    Provides the minimal interface needed by the test runner:
    - execute_case(case_def) -> dict with result/status/duration/response
    """

    def __init__(self, logger: callable = None, should_stop: callable = None):
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._log_buffer: list[str] = []

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
            {"result": "pass"|"fail", "status_code": int, "response_body": str,
             "duration_ms": float, "detail": str}
        """
        if self.stopped():
            return {"result": "stopped", "status_code": 0, "response_body": "",
                    "duration_ms": 0, "detail": "Execution stopped"}

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

        try:
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method=http_method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                response_text = resp.read().decode("utf-8", errors="replace")

            duration_ms = (time.time() - start) * 1000

            # Check status code
            if status_code != expected_status:
                self.log(f"FAIL: expected status {expected_status}, got {status_code}")
                return {
                    "result": "fail",
                    "status_code": status_code,
                    "response_body": response_text[:2000],
                    "duration_ms": round(duration_ms, 1),
                    "detail": f"Expected HTTP {expected_status}, got {status_code}",
                }

            # Check response body
            if expected_response:
                try:
                    expected_obj = expected_response if isinstance(expected_response, dict) else json.loads(expected_response)
                    actual_obj = json.loads(response_text)
                    if expected_obj != actual_obj:
                        self.log(f"FAIL: response body mismatch")
                        return {
                            "result": "fail",
                            "status_code": status_code,
                            "response_body": response_text[:2000],
                            "duration_ms": round(duration_ms, 1),
                            "detail": "Response body does not match expected",
                        }
                except json.JSONDecodeError:
                    if response_text.strip() != str(expected_response).strip():
                        return {
                            "result": "fail",
                            "status_code": status_code,
                            "response_body": response_text[:2000],
                            "duration_ms": round(duration_ms, 1),
                            "detail": "Response text does not match expected",
                        }

            # Custom assertions
            for a in assertions:
                a_type = a.get("type", "")
                path = a.get("path", "")
                expected = a.get("expected", "")
                operator = a.get("operator", "equals")
                if a_type == "response_time" and duration_ms > float(expected or 5000):
                    self.log(f"FAIL: response time {duration_ms:.0f}ms > {expected}ms")
                    return {
                        "result": "fail", "status_code": status_code,
                        "response_body": response_text[:2000], "duration_ms": round(duration_ms, 1),
                        "detail": f"Response time {duration_ms:.0f}ms exceeds {expected}ms",
                    }

            self.log(f"PASS: {http_method} {url} -> {status_code} ({duration_ms:.0f}ms)")
            return {
                "result": "pass",
                "status_code": status_code,
                "response_body": response_text[:2000],
                "duration_ms": round(duration_ms, 1),
                "detail": "",
            }

        except urllib.error.HTTPError as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: HTTP {e.code} {e.reason}")
            return {
                "result": "fail",
                "status_code": e.code,
                "response_body": str(e.read())[:2000],
                "duration_ms": round(duration_ms, 1),
                "detail": f"HTTP {e.code}: {e.reason}",
            }
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            return {
                "result": "fail",
                "status_code": 0,
                "response_body": "",
                "duration_ms": round(duration_ms, 1),
                "detail": str(e),
            }
