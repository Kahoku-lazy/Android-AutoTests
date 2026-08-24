"""
WebExecutor — executes Web automation test case steps from steps_json.

Parses structured web step types (web_navigate, web_click, web_fill, etc.)
and dispatches to WebAdapter with step-level callbacks. Each step is
automatically screenshotted and annotated via PIL.
"""

import asyncio
import os

from django.conf import settings

from models.step_types import TestStep
from models.test_models import TestCaseDef

from .adapter import _pw_run
from .annotator import annotate_screenshot


class WebExecutor:
    """Executes Web automation test case steps sequentially."""

    def __init__(self, adapter):
        self.adapter = adapter
        self._step_callback = None
        self._step_started_callback = None
        # Per-run state: populated by execute_case()
        self._last_step_details: list[dict] = []
        self._run_id: str = ""

    async def execute_case(self, case: TestCaseDef, iteration: int = 1, run_id: str = "") -> str:
        """Execute a Web test case step by step. Populates self._last_step_details."""
        self._run_id = run_id
        self._last_step_details = []
        extra = getattr(case, "extra_data", {}) or {}

        if case.steps_data:
            steps: list[TestStep] = case.steps_data
        elif extra:
            steps = self._parse_text_steps(extra)
        else:
            self.adapter.log(f"Error: no steps for '{case.title}'")
            return "fail"

        if not steps:
            self.adapter.log(f"Error: no executable steps for '{case.title}'")
            return "fail"

        total = len(steps)

        for i, step in enumerate(steps):
            if self.adapter.stopped():
                return "stopped"

            # Run watchers before each step (popup/banner dismissal)
            if hasattr(self.adapter, "run_watchers") and self.adapter._watchers:
                try:
                    dismissed = await self.adapter.run_watchers()
                    if dismissed:
                        self.adapter.log(f"Watchers dismissed {dismissed} popup(s)")
                except Exception:
                    import logging

                    logging.getLogger("test_runner.web").exception(
                        "run_watchers dismissal failed — proceeding without watcher"
                    )

            step_desc = step.description or self._step_label(step)
            if self._step_started_callback:
                self._step_started_callback(i, total, step.type, step_desc[:100])

            error_msg = ""
            result = await self._dispatch(step)
            if result == "fail":
                error_msg = (
                    self.adapter.get_log_buffer()[-1]
                    if self.adapter.get_log_buffer()
                    else "Step failed"
                )

            if self._step_callback:
                self._step_callback(i, total, step.type, step_desc[:100], result)

            # ── Auto-screenshot + annotate ──
            ss_rel = await self._capture_step(
                i, total, step, step_desc, result, error_msg, iteration
            )
            self._last_step_details.append(
                {
                    "index": i,
                    "total": total,
                    "type": step.type,
                    "description": step_desc,
                    "result": result,
                    "screenshot": ss_rel,
                    "selector": step.selector or "",
                    "value": step.value or "",
                    "error": error_msg,
                    "iteration": iteration,
                }
            )

            if result == "fail":
                return "fail"
            if result == "stopped":
                return "stopped"

        # Skip redundant case-level _verify_expected_result when steps_data
        # already contains web_assert steps — the step-level assertions are
        # the authoritative verification.  The case-level check uses
        # extra_data.expected_result (a human-readable description) which
        # would never match literal page text.
        has_assert_step = any(s.type == "web_assert" for s in (case.steps_data or []))
        if has_assert_step:
            return "pass"

        return await self._verify_expected_result(case, run_id, total, iteration)

    async def _verify_expected_result(
        self, case: TestCaseDef, run_id: str, total: int, iteration: int
    ) -> str:
        """Verify expected_result against page content after all steps complete.

        Always appends a step_detail (with screenshot) for the verification,
        whether it passes or fails — so the step count is always N+1 when
        expected_result is set.
        """
        extra = case.extra_data or {}
        expected = extra.get("expected_result", "")
        if not expected:
            return "pass"

        verify_desc = f"Expected: {expected[:80]}"
        verify_index = total  # 0-based index after all manual steps

        if self._step_started_callback:
            self._step_started_callback(verify_index, total + 1, "web_assert", verify_desc)

        verify_result = "pass"
        verify_error = ""

        try:
            await self.adapter._ensure_browser()
            page_text = await _pw_run(self.adapter._page.content)
            if expected not in str(page_text)[:10000]:
                self.adapter.log("FAIL: expected text not found")
                verify_result = "fail"
                verify_error = "Expected text not found"
        except Exception as e:
            self.adapter.log(f"Assert error: {e}")
            verify_result = "fail"
            verify_error = str(e)[:200]

        if self._step_callback:
            self._step_callback(verify_index, total + 1, "web_assert", verify_desc, verify_result)

        ss_rel = await self._capture_step(
            verify_index,
            total + 1,
            TestStep(type="web_assert", expected_text=expected),
            verify_desc,
            verify_result,
            verify_error,
            iteration,
        )
        self._last_step_details.append(
            {
                "index": verify_index,
                "total": total + 1,
                "type": "web_assert",
                "description": verify_desc,
                "result": verify_result,
                "screenshot": ss_rel,
                "selector": "",
                "value": "",
                "error": verify_error,
                "iteration": iteration,
            }
        )

        return verify_result

    async def _capture_step(
        self,
        i: int,
        total: int,
        step: TestStep,
        desc: str,
        result: str,
        error: str = "",
        iteration: int = 1,
    ) -> str:
        """Capture, annotate, and save a step screenshot. Returns relative path."""
        if not self._run_id:
            return ""
        try:
            ss_dir = os.path.join(
                str(settings.SCREENSHOT_DIR),
                "step_screenshots",
                self._run_id,
                f"iter_{iteration}",
            )
            os.makedirs(ss_dir, exist_ok=True)
            filename = f"step_{i:02d}_{step.type}.png"
            abs_path = os.path.join(ss_dir, filename)

            await self.adapter._screenshot_to_path(abs_path)

            # Get element bounds for click/fill steps
            bounds = None
            selector = step.selector or getattr(step, "xpath", "") or ""
            if selector and step.type in (
                "web_click",
                "click",
                "web_fill",
                "web_type",
                "long_click",
            ):
                bounds = await self.adapter._element_bounds(selector)

            annotate_screenshot(abs_path, i, step.type, desc, result, bounds, error)

            return os.path.join("step_screenshots", self._run_id, f"iter_{iteration}", filename)
        except Exception:
            return ""

    def _parse_text_steps(self, extra: dict) -> list[TestStep]:
        """Convert legacy plain-text steps to structured TestStep list."""
        steps_text = extra.get("steps", "")
        if not steps_text:
            # Single navigate + verify from flat fields
            url = extra.get("url", "")
            expected = extra.get("expected_result", "")
            result = []
            if url:
                result.append(
                    TestStep(type="web_navigate", url=url, description=f"Navigate to {url}")
                )
            if expected:
                result.append(
                    TestStep(
                        type="web_assert",
                        expected_text=expected,
                        description=f"Verify: {expected[:80]}",
                    )
                )
            return result

        steps = []
        for line in steps_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            cmd = parts[0].lower() if parts else ""
            arg = parts[1] if len(parts) > 1 else ""
            steps.append(self._text_to_step(cmd, arg, line))
        return steps

    def _text_to_step(self, cmd: str, arg: str, raw: str) -> TestStep:
        """Map a legacy text command to a structured TestStep."""
        if cmd == "click":
            return TestStep(type="web_click", selector=arg, description=raw)
        elif cmd == "fill":
            selector, _, value = arg.partition(" ")
            return TestStep(
                type="web_fill", selector=selector, value=value.strip('"'), description=raw
            )
        elif cmd == "type":
            selector, _, value = arg.partition(" ")
            return TestStep(
                type="web_type", selector=selector, value=value.strip('"'), description=raw
            )
        elif cmd == "wait":
            try:
                ms = int(arg)
                return TestStep(type="web_wait", timeout=ms / 1000.0, description=raw)
            except ValueError:
                return TestStep(type="web_wait", selector=arg, timeout=10, description=raw)
        elif cmd == "screenshot":
            return TestStep(type="web_screenshot", description=arg or "screenshot")
        elif cmd == "navigate":
            return TestStep(type="web_navigate", url=arg, description=raw)
        else:
            return TestStep(type="web_step", selector=cmd, value=arg, description=raw)

    def _step_label(self, step: TestStep) -> str:
        target = step.selector or step.xpath or ""
        labels = {
            "web_navigate": f"Go to {step.url}",
            "web_fill": f"Fill {target} = {step.value}",
            "web_type": f"Type {target} = {step.value}",
            "web_assert": f"Verify {step.expected_text}",
            "web_screenshot": "Screenshot",
            # Legacy
            "web_click": f"Click {target}",
            "web_wait": f"Wait {target or f'{step.timeout}s'}",
            # Unified common names
            "click": f"Click {target}",
            "wait": f"Wait {target or f'{step.timeout}s'}",
            "sleep": f"Sleep {step.timeout or 0}s",
            "screenshot": "Screenshot",
        }
        return labels.get(step.type, step.description or step.type)

    async def _dispatch(self, step: TestStep) -> str:
        """Dispatch a web step to the adapter."""
        t = step.type
        try:
            if t == "web_navigate":
                self.adapter.log(f"Navigate: {step.url}")
                if not step.url:
                    self.adapter.log("Navigate FAIL: no url")
                    return "fail"
                await self.adapter._navigate(step.url)
                return "pass"

            elif t == "web_click" or t == "click":
                target = step.selector or step.xpath
                self.adapter.log(f"Click: {target}")
                if not target:
                    self.adapter.log("Click FAIL: no selector/xpath")
                    return "fail"
                await self.adapter._click(target)
                return "pass"

            elif t == "web_fill" or t == "web_type":
                self.adapter.log(
                    f"{'Fill' if t == 'web_fill' else 'Type'}: {step.selector} = {step.value}"
                )
                if not step.selector:
                    self.adapter.log(f"{'Fill' if t == 'web_fill' else 'Type'} FAIL: no selector")
                    return "fail"
                await self.adapter._fill(step.selector, step.value or "")
                return "pass"

            elif t == "web_wait" or t == "wait":
                target = step.selector or step.xpath
                if step.timeout and step.timeout > 0 and not target:
                    self.adapter.log(f"Wait: {step.timeout}s")
                    await asyncio.sleep(step.timeout)
                elif target:
                    self.adapter.log(f"Wait for: {target}")
                    await self.adapter._wait_for(target, step.timeout or 10)
                else:
                    self.adapter.log("Wait FAIL: no selector/xpath and no timeout")
                    return "fail"
                return "pass"

            elif t == "web_assert":
                self.adapter.log(f"Verify: {step.expected_text or step.selector}")
                if not step.expected_text:
                    self.adapter.log("Verify FAIL: no expected_text")
                    return "fail"
                await self.adapter._verify_text(step.expected_text)
                return "pass"

            elif t == "web_screenshot" or t == "screenshot":
                self.adapter.log(f"Screenshot: {step.description or 'web'}")
                await self.adapter._screenshot(step.description or "web")
                return "pass"

            elif t == "sleep":
                timeout = step.timeout if step.timeout is not None and step.timeout > 0 else 1
                self.adapter.log(f"Sleep: {timeout}s")
                await asyncio.sleep(timeout)
                return "pass"

            else:
                self.adapter.log(f"Unknown web step: {t}")
                return "fail"

        except Exception as e:
            self.adapter.log(f"Step failed: {e}")
            return "fail"
