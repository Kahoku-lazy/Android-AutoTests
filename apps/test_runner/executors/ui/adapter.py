"""
Device adapter — wraps DeviceConnection to provide the interface
that StepExecutor expects (compatible with sku_stress_test's TestExecutor API).

Airtest Android handles device actions (swipe, app lifecycle, shell).
uiautomator2 is kept ONLY for XPath element operations.
"""

import logging
import time

from .connect import DeviceConnection

logger = logging.getLogger(__name__)


class DeviceAdapter:
    """Provides element operation helpers compatible with StepExecutor.

    Receives a DeviceConnection (Airtest + u2) and routes:
      - Actions (swipe, app start/stop) → Airtest
      - XPath queries (exists, click, get_text) → uiautomator2
    """

    def __init__(
        self,
        device_conn: DeviceConnection,
        package_name: str = "",
        logger: callable = None,
        should_stop: callable = None,
    ):
        """
        Args:
            device_conn:   DeviceConnection with .airtest (Android) and .u2 (uiautomator2)
            package_name:  Target Android app package (e.g. "com.govee.home")
            logger:        Callable for log messages: log(msg: str)
            should_stop:   Callable that returns True when execution should abort
        """
        self.d = device_conn.u2  # u2 device for xpath (keep attribute name)
        self.ad = device_conn.airtest  # airtest device for actions
        self.PACKAGE_NAME = package_name
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._step_callback = None  # (step_index, total, type, description, result)
        self._step_started_callback = None  # (step_index, total, type, description)
        self._log_buffer: list[str] = []
        self._perf_results: list[dict] = []  # {"description": str, "duration": float}
        self._watchers: list[dict] = []  # per-instance watcher list

    # ---- Logging ----
    def log(self, msg: str):
        self._emit_log(msg)
        self._log_buffer.append(msg)

    def clear_log_buffer(self):
        self._log_buffer.clear()

    def get_log_buffer(self) -> list[str]:
        return list(self._log_buffer)

    def clear_perf_results(self):
        self._perf_results.clear()

    def get_perf_results(self) -> list[dict]:
        return list(self._perf_results)

    # ---- Watcher (popup monitor) ----

    def register_watchers(self, watchers: list[dict]):
        """Register popup watchers. Each: {xpath, action: 'click'}."""
        self._watchers = list(watchers)

    def clear_watchers(self):
        self._watchers.clear()

    def run_watchers(self):
        if not self._watchers:
            return 0
        """Check all watchers and dismiss any matching popups.
        Returns the number of popups dismissed.
        """
        dismissed = 0
        for w in self._watchers:
            xpath = w.get("xpath", "")
            if not xpath:
                continue
            try:
                if self.d.xpath(xpath).exists:
                    action = w.get("action", "click")
                    if action == "click":
                        self.d.xpath(xpath).click()
                        self.log(f"Watcher: 已关闭弹窗 {xpath[:60]}")
                        dismissed += 1
            except Exception:
                logger.debug("Watcher popup dismiss failed: %s", xpath[:60])
        return dismissed

    # ---- Stop / Sleep ----
    def stopped(self) -> bool:
        return self._should_stop()

    def sleep(self, seconds: float):
        """Interruptible sleep — checks stop flag every 100ms."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            if self.stopped():
                return
            time.sleep(0.1)

    # ---- Element existence (u2 XPath) ----
    def exists(self, xpath: str, timeout: float = 0) -> bool:
        """Check element existence. timeout<=0: immediate; timeout>0: poll."""
        try:
            if timeout <= 0:
                return self.d.xpath(xpath).exists
            else:
                deadline = time.time() + timeout
                while time.time() < deadline:
                    if self.stopped():
                        return False
                    if self.d.xpath(xpath).exists:
                        return True
                    remain = min(0.5, deadline - time.time())
                    if remain > 0:
                        time.sleep(remain)
                return False
        except Exception:
            return False

    # ---- Element actions (u2 XPath) ----
    def click(self, xpath: str):
        try:
            self.d.xpath(xpath).click()
        except Exception as e:
            # u2 hang/timeout raised here; logged, re-raised for upper-layer u2 crash detection
            self.log(f"Click failed: {e}")
            raise

    # ---- Gesture actions (Airtest) ----
    def long_click(self, xpath: str, duration: float = 0.8):
        try:
            self.d.xpath(xpath).long_click(duration=duration)
        except Exception as e:
            self.log(f"Long click failed: {e}")
            raise

    def swipe(self, direction: str, distance: int = 500):
        try:
            w, h = self.ad.get_current_resolution()
            cx, cy = w // 2, h // 2
            dirs = {
                "up": (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
                "down": (cx, h // 4, cx, h // 4 + distance),
                "left": (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
                "right": (w // 4, cy, w // 4 + distance, cy),
            }
            x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
            self.ad.swipe((x1, y1), (x2, y2))
        except Exception as e:
            self.log(f"Swipe failed: {e}")
            raise

    def click_indexed(self, xpath: str, index: int) -> bool:
        try:
            elements = self.d.xpath(xpath).all()
            if len(elements) > index:
                elements[index].click()
                return True
            return False
        except Exception as e:
            self.log(f"Indexed click failed: {e}")
            raise

    # ---- Toast detection ----
    def wait_for_toast(self, expected_text: str, timeout: float = 15) -> bool:
        self.log(f'Waiting for toast "{expected_text}" (timeout {timeout}s)...')
        deadline = time.time() + timeout
        try:
            self.d.toast.reset()
        except Exception:
            logger.debug("Toast reset failed, continuing")
        while time.time() < deadline:
            if self.stopped():
                return False
            if self.d.xpath(f'//*[@text="{expected_text}"]').exists:
                return True
            try:
                msg = self.d.toast.get_message(0)
                if msg and expected_text in str(msg):
                    return True
            except Exception:
                logger.debug("Adapter operation failed, continuing")
            self.sleep(0.3)
        return False

    # ---- Text retrieval (u2 XPath) ----
    def get_text(self, xpath: str) -> str:
        try:
            el = self.d.xpath(xpath).get()
            return el.attrib.get("text", "") if el is not None else ""
        except Exception:
            return ""

    # ---- App lifecycle (Airtest) ----
    def kill_app(self, pkg: str):
        """Force-stop an app using Airtest with am kill + pkill fallbacks."""
        self.log(f"Killing app: {pkg}")
        try:
            self.ad.stop_app(pkg)
        except Exception:
            logger.debug("stop_app failed for %s, will try fallback", pkg)
        # Fallback: kill any remaining background processes
        try:
            self.ad.shell(f"am kill {pkg}")
        except Exception:
            logger.debug("am kill failed for %s, trying pkill", pkg)
        try:
            self.ad.shell(f"pkill -f {pkg}")
        except Exception:
            logger.debug("pkill failed for %s, continuing", pkg)

    # ---- Composite helpers (u2 XPath) ----
    def wait_appear_then_disappear(self, xpath: str, timeout: float = 30) -> bool:
        self.log(f'Waiting for "{xpath}" to appear then disappear (timeout {timeout}s)...')
        deadline = time.time() + timeout
        appeared = False
        while time.time() < deadline:
            if self.stopped():
                return False
            if self.d.xpath(xpath).exists:
                self.log("  Element appeared, waiting for disappear...")
                appeared = True
                break
            self.sleep(0.3)
        if not appeared:
            self.log("  Timeout: element did not appear")
            return False
        while time.time() < deadline:
            if self.stopped():
                return False
            if not self.d.xpath(xpath).exists:
                self.log("  Element disappeared")
                return True
            self.sleep(0.3)
        self.log("  Timeout: element did not disappear")
        return False
