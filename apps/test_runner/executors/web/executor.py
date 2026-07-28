"""
WebExecutor — executes Web automation test case steps from steps_json.

Parses structured web step types (web_navigate, web_click, web_fill, etc.)
and dispatches to WebAdapter with step-level callbacks.
"""
import asyncio
import time
from models.step_types import TestStep
from models.test_models import TestCaseDef


# ── Recognised web step types ──
_WEB_STEP_TYPES = {
    "web_navigate", "web_click", "web_fill", "web_type",
    "web_wait", "web_assert", "web_screenshot",
    # Legacy text-based fallback
    "web_step",
}


class WebExecutor:
    """Executes Web automation test case steps sequentially."""

    def __init__(self, adapter):
        self.adapter = adapter
        self._step_callback = None
        self._step_started_callback = None

    async def execute_case(self, case: TestCaseDef, iteration: int = 1) -> str:
        """Execute a Web test case step by step."""
        extra = getattr(case, 'extra_data', {}) or {}

        if case.steps_data:
            steps: list[TestStep] = case.steps_data
        elif extra:
            steps = self._parse_text_steps(extra)
        else:
            self.adapter.log(f"Error: no steps for '{case.title}'")
            return "fail"

        total = len(steps)

        for i, step in enumerate(steps):
            if self.adapter.stopped():
                return "stopped"

            # Run watchers before each step (popup/banner dismissal)
            if hasattr(self.adapter, 'run_watchers') and self.adapter._watchers:
                try:
                    dismissed = await self.adapter.run_watchers()
                    if dismissed:
                        self.adapter.log(f"Watchers dismissed {dismissed} popup(s)")
                except Exception:
                    pass

            step_desc = step.description or self._step_label(step)
            if self._step_started_callback:
                self._step_started_callback(i, total, step.type, step_desc[:100])

            result = await self._dispatch(step)

            if self._step_callback:
                self._step_callback(i, total, step.type, step_desc[:100], result)

            if result == "fail":
                return "fail"
            if result == "stopped":
                return "stopped"

        # Final assertion: expected_result check
        expected = extra.get("expected_result", "")
        if expected:
            if self._step_started_callback:
                self._step_started_callback(total, total + 1, "web_assert",
                                            f"Expected: {expected[:100]}")
            try:
                await self.adapter._ensure_browser()
                page_text = await self.adapter._page.content()
                if expected not in str(page_text)[:10000]:
                    self.adapter.log("FAIL: expected text not found")
                    if self._step_callback:
                        self._step_callback(total, total + 1, "web_assert",
                                            f"Expected: {expected[:100]}", "fail")
                    return "fail"
                if self._step_callback:
                    self._step_callback(total, total + 1, "web_assert",
                                        f"Expected: {expected[:100]}", "pass")
            except Exception as e:
                self.adapter.log(f"Assert error: {e}")

        return "pass"

    def _parse_text_steps(self, extra: dict) -> list[TestStep]:
        """Convert legacy plain-text steps to structured TestStep list."""
        steps_text = extra.get("steps", "")
        if not steps_text:
            # Single navigate + verify from flat fields
            url = extra.get("url", "")
            expected = extra.get("expected_result", "")
            result = []
            if url:
                result.append(TestStep(type="web_navigate", url=url,
                                       description=f"Navigate to {url}"))
            if expected:
                result.append(TestStep(type="web_assert", expected_text=expected,
                                       description=f"Verify: {expected[:80]}"))
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
            return TestStep(type="web_fill", selector=selector,
                            value=value.strip('"'), description=raw)
        elif cmd == "type":
            selector, _, value = arg.partition(" ")
            return TestStep(type="web_type", selector=selector,
                            value=value.strip('"'), description=raw)
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
        labels = {
            "web_navigate": f"Go to {step.url}",
            "web_click": f"Click {step.selector}",
            "web_fill": f"Fill {step.selector} = {step.value}",
            "web_type": f"Type {step.selector} = {step.value}",
            "web_wait": f"Wait {step.selector or f'{step.timeout}s'}",
            "web_assert": f"Verify {step.expected_text}",
            "web_screenshot": f"Screenshot {step.description or ''}",
        }
        return labels.get(step.type, step.description or step.type)

    async def _dispatch(self, step: TestStep) -> str:
        """Dispatch a web step to the adapter."""
        t = step.type
        try:
            if t == "web_navigate":
                self.adapter.log(f"Navigate: {step.url}")
                if step.url:
                    await self.adapter._navigate(step.url)
                return "pass"

            elif t == "web_click":
                self.adapter.log(f"Click: {step.selector}")
                if step.selector:
                    await self.adapter._click(step.selector)
                return "pass"

            elif t == "web_fill" or t == "web_type":
                self.adapter.log(f"{'Fill' if t == 'web_fill' else 'Type'}: "
                                 f"{step.selector} = {step.value}")
                if step.selector:
                    await self.adapter._fill(step.selector, step.value or "")
                return "pass"

            elif t == "web_wait":
                if step.timeout and step.timeout > 0 and not step.selector:
                    self.adapter.log(f"Wait: {step.timeout}s")
                    await asyncio.sleep(step.timeout)
                elif step.selector:
                    self.adapter.log(f"Wait for: {step.selector}")
                    await self.adapter._wait_for(step.selector, step.timeout or 10)
                return "pass"

            elif t == "web_assert":
                self.adapter.log(f"Verify: {step.expected_text or step.selector}")
                if step.expected_text:
                    await self.adapter._verify_text(step.expected_text)
                return "pass"

            elif t == "web_screenshot":
                self.adapter.log(f"Screenshot: {step.description or 'web'}")
                await self.adapter._screenshot(step.description or "web")
                return "pass"

            else:
                self.adapter.log(f"Unknown web step: {t}")
                return "fail"

        except Exception as e:
            self.adapter.log(f"Step failed: {e}")
            return "fail"
