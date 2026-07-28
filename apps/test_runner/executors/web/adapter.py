"""
Web adapter — executes web automation test cases using Playwright.
"""
import time
import asyncio


class WebAdapter:
    """Executes web automation test cases via Playwright (headless Chromium)."""

    def __init__(self, logger: callable = None, should_stop: callable = None):
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._log_buffer: list[str] = []
        self._watchers: list[dict] = []  # per-instance watcher list
        self._browser = None
        self._page = None

    def log(self, msg: str):
        self._emit_log(msg)
        self._log_buffer.append(msg)

    def clear_log_buffer(self):
        self._log_buffer.clear()

    def get_log_buffer(self) -> list[str]:
        return list(self._log_buffer)

    def stopped(self) -> bool:
        return self._should_stop()

    async def _ensure_browser(self):
        """Lazy-init Playwright browser."""
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")
        self.log("Starting Playwright Chromium (headless)...")
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._page = await self._browser.new_page()

    async def close(self):
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_pw'):
            await self._pw.stop()

    def execute_case(self, case: dict) -> dict:
        """Execute a single web automation test case synchronously.

        Args:
            case: dict with keys id, title, url, steps, expected_result
        Returns:
            {"result": "pass"|"fail", "duration_ms": float, "detail": str}
        """
        return asyncio.run(self._execute_case_async(case))

    async def _execute_case_async(self, case: dict) -> dict:
        url = case.get("url", "")
        steps_text = case.get("steps", "")
        expected = case.get("expected_result", "")
        title = case.get("title", case.get("id", ""))

        if not url:
            self.log(f"FAIL: no URL for '{title}'")
            return {"result": "fail", "duration_ms": 0, "detail": "No URL specified"}

        start = time.time()
        try:
            await self._ensure_browser()
            self.log(f"Navigating to {url}")
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Execute steps (line-by-line commands)
            if steps_text:
                for line in steps_text.strip().split("\n"):
                    line = line.strip()
                    if not line or self.stopped():
                        break
                    await self._execute_step(line)

            # Check expected result
            if expected:
                page_text = await self._page.content()
                if expected not in page_text:
                    duration_ms = (time.time() - start) * 1000
                    self.log(f"FAIL: expected text not found on page")
                    return {"result": "fail", "duration_ms": round(duration_ms, 1),
                            "detail": f"Expected text '{expected[:100]}' not found on page"}

            duration_ms = (time.time() - start) * 1000
            self.log(f"PASS: {url} ({duration_ms:.0f}ms)")
            return {"result": "pass", "duration_ms": round(duration_ms, 1), "detail": ""}

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log(f"FAIL: {str(e)}")
            return {"result": "fail", "duration_ms": round(duration_ms, 1), "detail": str(e)}

    async def _execute_step(self, line: str):
        """Execute a single web automation step command string."""
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "click" and arg:
            await self._page.click(arg)
        elif cmd == "fill" and arg:
            selector, _, value = arg.partition(" ")
            await self._page.fill(selector, value.strip('"'))
        elif cmd == "type" and arg:
            selector, _, value = arg.partition(" ")
            await self._page.type(selector, value.strip('"'))
        elif cmd == "wait" and arg:
            try:
                ms = int(arg)
                await asyncio.sleep(ms / 1000)
            except ValueError:
                await self._page.wait_for_selector(arg, timeout=10000)
        elif cmd == "screenshot":
            pass  # could save screenshot for debugging
        elif cmd == "navigate" and arg:
            await self._page.goto(arg, wait_until="domcontentloaded", timeout=30000)
        self.log(f"  step: {line}")

    # ── Structured step methods (called by WebExecutor) ──

    async def _navigate(self, url: str):
        """Navigate to URL."""
        await self._ensure_browser()
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)

    async def _click(self, selector: str):
        """Click an element by selector."""
        await self._ensure_browser()
        await self._page.click(selector, timeout=10000)

    async def _fill(self, selector: str, value: str):
        """Fill an input field."""
        await self._ensure_browser()
        await self._page.fill(selector, value, timeout=10000)

    async def _wait_for(self, selector: str, timeout: float = 10):
        """Wait for a selector to appear."""
        await self._ensure_browser()
        await self._page.wait_for_selector(selector, timeout=timeout * 1000)

    async def _verify_text(self, expected: str):
        """Verify expected text on page."""
        await self._ensure_browser()
        content = await self._page.content()
        if expected not in content:
            raise AssertionError(f"Expected text '{expected[:100]}' not found on page")

    async def _screenshot(self, name: str = "web"):
        """Take a screenshot."""
        await self._ensure_browser()
        import os
        screenshot_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "screenshots",
        )
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"web_{name}_{int(time.time() * 1000)}.png")
        await self._page.screenshot(path=path)
        self.log(f"Screenshot saved: {path}")

    async def _screenshot_to_path(self, path: str) -> str:
        """Take a screenshot and save to a specific path. Returns the path."""
        await self._ensure_browser()
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        await self._page.screenshot(path=path, full_page=False)
        return path

    async def _element_bounds(self, selector: str) -> dict | None:
        """Get the bounding box of the first matching element. Returns {x, y, width, height} or None."""
        if not selector:
            return None
        await self._ensure_browser()
        try:
            el = self._page.locator(selector).first
            box = await el.bounding_box()
            if box:
                return {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}
        except Exception:
            pass
        return None

    # ── Watcher support (popup/banner handling) ──

    def register_watchers(self, watchers: list[dict]):
        """Register popup/banner watchers. Each: {selector, action: 'click'}."""
        self._watchers = list(watchers)

    def clear_watchers(self):
        self._watchers.clear()

    async def run_watchers(self):
        if not self._watchers:
            return 0
        """Check and dismiss matching popups. Returns count dismissed."""
        await self._ensure_browser()
        dismissed = 0
        for w in self._watchers:
            selector = w.get("selector", "")
            if not selector:
                continue
            try:
                try:
                    await asyncio.wait_for(
                        self._page.wait_for_selector(selector, timeout=1000),
                        timeout=1.5,
                    )
                except (asyncio.TimeoutError, Exception):
                    continue
                action = w.get("action", "click")
                if action == "click":
                    await self._page.click(selector)
                self.log(f"Watcher: dismissed {selector[:60]}")
                dismissed += 1
            except Exception:
                pass
        return dismissed
