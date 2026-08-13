"""
ApiExecutorV2 — config_json-native API test executor.

Parses the unified config_json (case_info/steps/test_data/validation) and
executes each test data row through all steps with a 7-step pipeline:
  ① validation check → ② variable substitution → ③ request_schema check
  → ④ HTTP request → ⑤ extract variables → ⑥ response assertion
  → ⑦ row-level output assertion

Reuses the existing ApiAdapter.execute_step() for HTTP transport.
"""

import copy
import json
import logging
import re

from models.step_types import TestStep
from models.test_models import TestCaseDef

_log = logging.getLogger("test_runner.api_v2")


class ApiExecutorV2:
    """Executes API test cases from config_json with jsonschema validation."""

    def __init__(self, adapter):
        """
        Args:
            adapter: ApiAdapter instance (provides execute_step/log/stopped)
        """
        self.adapter = adapter
        self._variables: dict[str, str] = {}
        self._last_response: dict | None = None
        self._step_callback = None  # (step_index, total, type, description, result)
        self._step_started_callback = None  # (step_index, total, type, description)

    # ═══════════════════════════════════════════════════════════════
    # Public entry point
    # ═══════════════════════════════════════════════════════════════

    def execute_case(self, case: TestCaseDef, iteration: int = 1, run_id: str = "") -> str:
        """Execute an API test case from config_json.

        Auto-detects single (meta/request/cases) vs multi (case_info/steps/test_data)
        format and dispatches accordingly.
        """
        extra = getattr(case, "extra_data", {}) or {}
        config = extra.get("config_json", extra)  # support both raw config_json and legacy extra

        # ── Format detection: "meta" key → single-request format ──
        if "meta" in config and "cases" in config:
            return self._execute_single(config)

        # ── Multi-step legacy path ──
        steps_cfg = config.get("steps", [])
        test_data = config.get("test_data", [])
        validation = config.get("validation", [])

        if not steps_cfg:
            # Fall back to steps_data if no config_json steps (legacy compat)
            if case.steps_data:
                return self._execute_steps_legacy(case.steps_data, extra)
            self.adapter.log(f"Error: no steps for '{case.title}'")
            return "fail"

        if not test_data:
            # Single run — no variable injection from test_data
            return self._execute_row(steps_cfg, {}, None, validation)

        # ── Data-driven: iterate over each test_data row ──
        all_pass = True
        for ri, row in enumerate(test_data):
            if self.adapter.stopped():
                return "stopped"
            row_input = row.get("input", row) if isinstance(row, dict) else {}
            row_output = row.get("output_schema") if isinstance(row, dict) else None
            self.adapter.log(f"--- Data row {ri + 1}/{len(test_data)} ---")
            result = self._execute_row(steps_cfg, row_input, row_output, validation)
            if result != "pass":
                all_pass = False
        return "pass" if all_pass else "fail"

    # ═══════════════════════════════════════════════════════════════
    # Single-request execution — meta/request/cases format
    # ═══════════════════════════════════════════════════════════════

    def _execute_single(self, config: dict) -> str:
        """Execute a single-request data-driven API test case.

        Iterates over config["cases"], building one HTTP request per row
        from config["request"] template + row["input"] overrides.
        """
        meta = config.get("meta", {})
        req = config.get("request", {})
        cases = config.get("cases", [])

        base_url = meta.get("base_url", "")
        method = req.get("method", "GET")
        path = req.get("path", "")
        req_headers = dict(req.get("headers", {}))

        all_pass = True

        for idx, case_row in enumerate(cases):
            if self.adapter.stopped():
                return "stopped"

            case_id = case_row.get("id", f"row-{idx}")
            scenario = case_row.get("scenario", "")
            category = case_row.get("category", "")
            description = case_row.get("description", "")
            inp = case_row.get("input", {}) or {}
            expect = case_row.get("expect", {})

            # ── Build headers ──
            headers = {**req_headers}
            row_headers = inp.get("headers", {}) or {}
            headers.update(row_headers)

            # ── Build overridden step for _cfg_to_test_step ──
            step_cfg = {
                "method": method,
                "domain": base_url,
                "url": path,
                "headers": headers,
                "body": inp.get("body", {}) or {},
                "expected_status": expect.get("status", 0),
                "name": f"{case_id} {scenario}",
                "assert": True,
                "response_schema": expect.get("body_schema"),
                "extract": [],
                "request_schema": None,
            }

            # ── Row-level variable substitution ──
            row_input = inp.get("body", {}) or {}
            step_cfg = self._substitute_vars(step_cfg, row_input)

            # ── Log ──
            tags = f"[{category}] " if category else ""
            self.adapter.log(f"--- {case_id} {tags}{scenario} ---")
            if description:
                self.adapter.log(f"  {description}")

            # ── HTTP request ──
            test_step = self._cfg_to_test_step(step_cfg)
            http_result = self.adapter.execute_step(test_step)

            if not isinstance(http_result, dict):
                self.adapter.log(f"  FAIL: unexpected result type")
                all_pass = False
                continue

            status_code = http_result.get("status_code", 0)
            expected_status = expect.get("status", 0)
            response_body = http_result.get("response_body", "")

            # ── Status assertion ──
            if expected_status > 0 and status_code != expected_status:
                self.adapter.log(f"  FAIL: expected HTTP {expected_status}, got {status_code}")
                all_pass = False
                continue

            # ── Body schema assertion ──
            body_schema = expect.get("body_schema")
            if body_schema and isinstance(body_schema, dict):
                try:
                    body_obj = (
                        json.loads(response_body)
                        if isinstance(response_body, str)
                        else response_body
                    )
                except (json.JSONDecodeError, TypeError):
                    body_obj = response_body
                try:
                    import jsonschema

                    jsonschema.validate(body_obj, body_schema)
                except jsonschema.ValidationError as e:
                    self.adapter.log(f"  FAIL body_schema: {e.message}")
                    all_pass = False
                    continue
                except ImportError:
                    _log.warning("jsonschema not installed")

            self.adapter.log(f"  PASS (HTTP {status_code})")

        return "pass" if all_pass else "fail"

    # ═══════════════════════════════════════════════════════════════
    # Row execution
    # ═══════════════════════════════════════════════════════════════

    def _execute_row(
        self,
        steps_cfg: list[dict],
        row_input: dict,
        row_output_schema: dict | None,
        validation: list[dict],
    ) -> str:
        """Execute one test data row through all config_json steps."""
        self._variables = {}
        self._last_response = None

        for step_idx, step_cfg in enumerate(steps_cfg):
            if self.adapter.stopped():
                return "stopped"

            # ── ① Validation check (before request) ──
            pre_check = self._validate_before_request(step_cfg, step_idx, row_input, validation)
            if pre_check:
                self.adapter.log(f"Step {step_idx} validation FAIL: {pre_check}")
                return "fail"

            # ── ② Variable substitution (5 fields) ──
            step_cfg = self._substitute_vars(step_cfg, row_input)

            # ── ③ Request schema check ──
            request_schema = step_cfg.get("request_schema")
            if request_schema and isinstance(request_schema, dict):
                body = step_cfg.get("body", {})
                try:
                    import jsonschema

                    jsonschema.validate(body, request_schema)
                except jsonschema.ValidationError as e:
                    self.adapter.log(f"Step {step_idx} request_schema FAIL: {e.message}")
                    return "fail"
                except ImportError:
                    _log.warning("jsonschema not installed, skipping request_schema validation")

            # ── ④ HTTP request ──
            test_step = self._cfg_to_test_step(step_cfg)
            http_result = self.adapter.execute_step(test_step)

            if not isinstance(http_result, dict):
                self.adapter.log(f"Step {step_idx} HTTP FAIL: unexpected result type")
                return "fail"

            self._last_response = {
                "status_code": http_result.get("status_code", 0),
                "response_body": http_result.get("response_body", ""),
                "response_headers": http_result.get("response_headers", {}),
                "duration_ms": http_result.get("duration_ms", 0),
            }

            if http_result.get("result") != "pass":
                self.adapter.log(
                    f"Step {step_idx} FAIL: {http_result.get('detail', http_result.get('result'))}"
                )
                return "fail"

            # ── ⑤ Extract variables ──
            self._extract_variables_v2(step_cfg.get("extract", []))

            # ── ⑥ Response assertion (step-level JSON Schema) ──
            if step_cfg.get("assert", False):
                response_schema = step_cfg.get("response_schema")
                if response_schema and isinstance(response_schema, dict):
                    # response_schema may contain {{var}} — substitute before assertion
                    response_schema = self._substitute_in_value(response_schema, row_input)
                    response_body = http_result.get("response_body", "")
                    try:
                        body_obj = (
                            json.loads(response_body)
                            if isinstance(response_body, str)
                            else response_body
                        )
                    except (json.JSONDecodeError, TypeError):
                        body_obj = response_body
                    try:
                        import jsonschema

                        jsonschema.validate(body_obj, response_schema)
                    except jsonschema.ValidationError as e:
                        self.adapter.log(f"Step {step_idx} response_schema FAIL: {e.message}")
                        return "fail"
                    except ImportError:
                        _log.warning(
                            "jsonschema not installed, skipping response_schema validation"
                        )

        # ── ⑦ Row-level output assertion ──
        if row_output_schema and isinstance(row_output_schema, dict):
            target_step_idx = row_output_schema.get("step_index", -1)
            output_schema = row_output_schema.get("schema")
            if output_schema and isinstance(output_schema, dict) and self._last_response:
                response_body = self._last_response.get("response_body", "")
                try:
                    body_obj = (
                        json.loads(response_body)
                        if isinstance(response_body, str)
                        else response_body
                    )
                except (json.JSONDecodeError, TypeError):
                    body_obj = response_body
                try:
                    import jsonschema

                    jsonschema.validate(body_obj, output_schema)
                except jsonschema.ValidationError as e:
                    self.adapter.log(
                        f"Row output_schema FAIL (step {target_step_idx}): {e.message}"
                    )
                    return "fail"
                except ImportError:
                    pass

        return "pass"

    # ═══════════════════════════════════════════════════════════════
    # Legacy fallback — delegate to steps_data path
    # ═══════════════════════════════════════════════════════════════

    def _execute_steps_legacy(self, steps_data: list[TestStep], extra: dict) -> str:
        """Fallback: execute pre-built TestStep list (old format)."""
        from .executor import ApiExecutor

        legacy = ApiExecutor(self.adapter)
        # Inject callback wiring if set
        legacy._step_callback = self._step_callback
        legacy._step_started_callback = self._step_started_callback
        return legacy.execute_case(
            TestCaseDef(
                id="legacy",
                title="",
                task_type="api_testing",
                steps_data=steps_data,
                extra_data=extra,
            ),
        )

    # ═══════════════════════════════════════════════════════════════
    # Variable substitution (5-field)
    # ═══════════════════════════════════════════════════════════════

    def _substitute_vars(self, step_cfg: dict, row_input: dict) -> dict:
        """Deep-clone step_cfg and substitute {{var}} in 6 fields.

        Priority: row_input > extract_vars (row data wins on name collision).
        Fields substituted: url, headers, body, request_schema, response_schema, expected_status.
        """
        s = copy.deepcopy(step_cfg)
        all_vars = {**self._variables, **row_input}  # row_input overwrites

        def sub(val):
            if isinstance(val, str):
                return re.sub(
                    r"\{\{(.+?)\}\}",
                    lambda m: str(all_vars.get(m.group(1), m.group(0))),
                    val,
                )
            if isinstance(val, dict):
                return {kk: sub(vv) for kk, vv in val.items()}
            if isinstance(val, list):
                return [sub(vv) for vv in val]
            return val

        s["url"] = sub(s.get("url", ""))
        s["headers"] = sub(s.get("headers", {}))
        s["body"] = sub(s.get("body", {}))
        if s.get("request_schema"):
            s["request_schema"] = sub(s["request_schema"])
        if s.get("response_schema"):
            s["response_schema"] = sub(s["response_schema"])
        if s.get("expected_status") is not None:
            s["expected_status"] = sub(s["expected_status"])

        return s

    def _substitute_in_value(self, value, row_input: dict):
        """Substitute {{var}} in an arbitrary value using row_input + extract_vars."""
        all_vars = {**self._variables, **row_input}

        def sub(val):
            if isinstance(val, str):
                return re.sub(
                    r"\{\{(.+?)\}\}",
                    lambda m: str(all_vars.get(m.group(1), m.group(0))),
                    val,
                )
            if isinstance(val, dict):
                return {kk: sub(vv) for kk, vv in val.items()}
            if isinstance(val, list):
                return [sub(vv) for vv in val]
            return val

        return sub(value)

    # ═══════════════════════════════════════════════════════════════
    # Validation (before request)
    # ═══════════════════════════════════════════════════════════════

    def _validate_before_request(
        self, step_cfg: dict, step_idx: int, row_input: dict, validation: list[dict]
    ) -> str | None:
        """Check validation rules for this step. Returns error message or None."""
        for v in validation:
            if v.get("step_index") != step_idx or not v.get("enabled"):
                continue
            schema = v.get("schema")
            if not schema or not isinstance(schema, dict):
                continue
            body = step_cfg.get("body", {})
            try:
                import jsonschema

                jsonschema.validate(body, schema)
            except jsonschema.ValidationError as e:
                return f"validation[step={step_idx}] body schema mismatch: {e.message}"
            except ImportError:
                return None
        return None

    # ═══════════════════════════════════════════════════════════════
    # Variable extraction
    # ═══════════════════════════════════════════════════════════════

    def _extract_variables_v2(self, extract_rules: list[dict]):
        """Extract variables from the last API response using JSONPath rules.

        Args:
            extract_rules: [{"name": "token", "path": "$.data.token"}, ...]
        """
        if not extract_rules or not self._last_response:
            return
        response_body = self._last_response.get("response_body", "")
        response_headers = self._last_response.get("response_headers", {})

        for rule in extract_rules:
            var_name = rule.get("name", "")
            json_path = rule.get("path", "")
            if not var_name or not json_path:
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
        if path.startswith("$.headers."):
            header_key = path[len("$.headers.") :]
            return response_headers.get(header_key)

        try:
            body_obj = (
                json.loads(response_body) if isinstance(response_body, str) else response_body
            )
        except (json.JSONDecodeError, TypeError):
            return None

        if path == "$":
            return str(body_obj)

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

    # ═══════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _cfg_to_test_step(step_cfg: dict) -> TestStep:
        """Convert a config_json step dict to a TestStep for the adapter."""
        return TestStep(
            type="api_request",
            method=step_cfg.get("method", "GET"),
            url=(step_cfg.get("domain") or "") + (step_cfg.get("url") or ""),
            headers=step_cfg.get("headers", {}),
            body=step_cfg.get("body", {}),
            extract=step_cfg.get("extract", {}),
            assertions=step_cfg.get("assertions", []),
            expected_status=int(step_cfg.get("expected_status", 0) or 0),
            description=step_cfg.get("name", ""),
        )
