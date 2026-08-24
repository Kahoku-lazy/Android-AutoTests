"""
Web adapter — executes web automation test cases using Playwright.

Uses Playwright's sync API via a dedicated single-thread executor to avoid:
1. The SelectorEventLoop subprocess limitation on Windows (Daphne forces
   WindowsSelectorEventLoopPolicy for Twisted compatibility, which does not
   support asyncio.create_subprocess_exec).
2. greenlet thread-affinity errors (Playwright sync API greenlets cannot
   switch across threads).
"""

import asyncio
import concurrent.futures
import logging
import os
import time

from collections.abc import Callable
from functools import partial
from typing import Any

logger = logging.getLogger(__name__)

# Dedicated single-thread executor for all Playwright sync API calls.
# All browser/page operations MUST use this executor because Playwright's
# sync API uses greenlets which are bound to their creation thread.
_PW_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="pw")


def _pw_run(func, *args, **kwargs):
    """Run a Playwright sync call on the dedicated executor thread.

    Returns an awaitable that resolves to the function's return value.
    Uses functools.partial when kwargs are present (loop.run_in_executor
    only supports positional args).
    """
    loop = asyncio.get_event_loop()
    if kwargs:
        return loop.run_in_executor(_PW_EXECUTOR, partial(func, *args, **kwargs))
    return loop.run_in_executor(_PW_EXECUTOR, func, *args)


def _as_locator(selector: str) -> str:
    """Prefix bare XPath expressions so Playwright parses them as XPath.

    Common step types (click/wait) may carry an XPath in the xpath field;
    Playwright otherwise treats the string as a CSS selector and fails.
    """
    s = (selector or "").strip()
    if s.startswith(("//", "(")):
        return f"xpath={s}"
    return s


class WebAdapter:
    """Executes web automation test cases via Playwright (headless Chromium)."""

    def __init__(
        self,
        logger: Callable[[str], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ):
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._log_buffer: list[str] = []
        self._watchers: list[dict] = []  # per-instance watcher list
        self._browser: Any = None
        self._page: Any = None
        self._pw: Any = None

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
        """Lazy-init Playwright browser via sync API on the dedicated thread."""
        if self._browser is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        self.log("Starting Playwright Chromium (headless)...")

        def _start():
            # sync_playwright internally calls asyncio.new_event_loop() which
            # uses the globally-set policy. Daphne forces SelectorEventLoopPolicy
            # (for Twisted compat), but SelectorEventLoop doesn't support
            # subprocesses. Temporarily override to Proactor so Playwright can
            # spawn its driver process.
            import asyncio as _asyncio

            _old_policy = _asyncio.get_event_loop_policy()
            _asyncio.set_event_loop_policy(_asyncio.WindowsProactorEventLoopPolicy())
            try:
                pw = sync_playwright().start()
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                return pw, browser, page
            finally:
                _asyncio.set_event_loop_policy(_old_policy)

        self._pw, self._browser, self._page = await _pw_run(_start)

    async def reset_state(self):
        """Replace the current page with a fresh one (clears cookies/storage)."""
        await self._ensure_browser()

        def _reset():
            new_page = self._browser.new_page()
            self._page.close()
            self._page = new_page

        await _pw_run(_reset)

    async def close(self):
        if self._browser:
            await _pw_run(self._browser.close)
            self._browser = None
            self._page = None
        if self._pw:
            await _pw_run(self._pw.stop)
            self._pw = None

    def execute_case(self, case: dict) -> dict:
        """Execute a single web automation test case synchronously.

        Legacy entry point — prefer WebExecutor.execute_case() for async contexts.

        Args:
            case: dict with keys id, title, url, steps, expected_result
        Returns:
            {"result": "pass"|"fail", "duration_ms": float, "detail": str}
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._execute_case_async(case))
        raise RuntimeError(
            "WebAdapter.execute_case() cannot be called from within a running event loop. "
            "Use WebExecutor.execute_case() or call from a synchronous context."
        )

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

            await _pw_run(
                self._page.goto,
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Execute steps (line-by-line commands)
            if steps_text:
                for line in steps_text.strip().split("\n"):
                    line = line.strip()
                    if not line or self.stopped():
                        break
                    await self._execute_step(line)

            # Check expected result
            if expected:
                page_text = await _pw_run(self._page.content)
                if expected not in page_text:
                    duration_ms = (time.time() - start) * 1000
                    self.log("FAIL: expected text not found on page")
                    return {
                        "result": "fail",
                        "duration_ms": round(duration_ms, 1),
                        "detail": f"Expected text '{expected[:100]}' not found on page",
                    }

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
            await _pw_run(self._page.click, arg)
        elif cmd == "fill" and arg:
            selector, _, value = arg.partition(" ")
            await _pw_run(self._page.fill, selector, value.strip('"'))
        elif cmd == "type" and arg:
            selector, _, value = arg.partition(" ")
            await _pw_run(self._page.type, selector, value.strip('"'))
        elif cmd == "wait" and arg:
            try:
                ms = int(arg)
                await asyncio.sleep(ms / 1000)
            except ValueError:
                await _pw_run(
                    self._page.wait_for_selector,
                    arg,
                    timeout=10000,
                )
        elif cmd == "screenshot":
            pass  # could save screenshot for debugging
        elif cmd == "navigate" and arg:
            await _pw_run(
                self._page.goto,
                arg,
                wait_until="domcontentloaded",
                timeout=30000,
            )
        self.log(f"  step: {line}")

    # ── Structured step methods (called by WebExecutor) ──

    async def _navigate(self, url: str):
        """Navigate to URL."""
        await self._ensure_browser()
        await _pw_run(
            self._page.goto,
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

    async def _click(self, selector: str):
        """Click an element by selector."""
        await self._ensure_browser()
        await _pw_run(self._page.click, _as_locator(selector), timeout=10000)

    async def _fill(self, selector: str, value: str):
        """Fill an input field."""
        await self._ensure_browser()
        await _pw_run(self._page.fill, _as_locator(selector), value, timeout=10000)

    async def _wait_for(self, selector: str, timeout: float = 10):
        """Wait for a selector to appear."""
        await self._ensure_browser()
        await _pw_run(
            self._page.wait_for_selector,
            _as_locator(selector),
            timeout=timeout * 1000,
        )

    async def _verify_text(self, expected: str):
        """Verify expected text on page."""
        await self._ensure_browser()
        content = await _pw_run(self._page.content)
        if expected not in content:
            raise AssertionError(f"Expected text '{expected[:100]}' not found on page")

    async def _screenshot(self, name: str = "web"):
        """Take a screenshot."""
        await self._ensure_browser()
        screenshot_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "screenshots",
        )
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"web_{name}_{int(time.time() * 1000)}.png")
        await _pw_run(self._page.screenshot, path=path)
        self.log(f"Screenshot saved: {path}")

    async def _screenshot_to_path(self, path: str) -> str:
        """Take a screenshot and save to a specific path. Returns the path."""
        await self._ensure_browser()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        await _pw_run(self._page.screenshot, path=path, full_page=False)
        return path

    async def _element_bounds(self, selector: str) -> dict | None:
        """Get the bounding box of the first matching element.
        Returns {x, y, width, height} or None."""
        if not selector:
            return None
        await self._ensure_browser()

        def _get_bounds():
            try:
                el = self._page.locator(_as_locator(selector)).first
                box = el.bounding_box()
                if box:
                    return {
                        "x": box["x"],
                        "y": box["y"],
                        "width": box["width"],
                        "height": box["height"],
                    }
            except Exception:
                logger.debug("Web adapter operation failed, continuing")
            return None

        return await _pw_run(_get_bounds)

    # ── Watcher support (popup/banner handling) ──

    def register_watchers(self, watchers: list[dict]):
        """Register popup/banner watchers. Each: {selector, action: 'click'}."""
        self._watchers = list(watchers)

    def clear_watchers(self):
        self._watchers.clear()

    async def run_watchers(self):
        """Check and dismiss matching popups. Returns count dismissed."""
        if not self._watchers:
            return 0
        await self._ensure_browser()
        dismissed = 0
        for w in self._watchers:
            selector = w.get("selector", "")
            if not selector:
                continue

            def _check_and_dismiss():
                try:
                    self._page.wait_for_selector(selector, timeout=1000)
                except Exception:
                    return False
                action = w.get("action", "click")
                if action == "click":
                    self._page.click(selector)
                return True

            try:
                found = await asyncio.wait_for(_pw_run(_check_and_dismiss), timeout=2.0)
                if found:
                    self.log(f"Watcher: dismissed {selector[:60]}")
                    dismissed += 1
            except asyncio.TimeoutError:
                pass
            except Exception:
                logger.debug("Web adapter operation failed, continuing")
        return dismissed
