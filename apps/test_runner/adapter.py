"""
Device adapter — wraps DeviceManager to provide the interface
that StepExecutor expects (compatible with sku_stress_test's TestExecutor API).

This is the bridge between Android-AutoTests' DeviceManager and
the step execution engine from sku_stress_test.
"""
import time
import uiautomator2 as u2


class DeviceAdapter:
    """Provides element operation helpers compatible with StepExecutor.

    Wraps an existing uiautomator2 device instance (from DeviceManager)
    and adds logging + stop-control channels.
    """

    def __init__(self, device: u2.Device, package_name: str = "",
                 logger: callable = None,
                 should_stop: callable = None):
        """
        Args:
            device:       uiautomator2 device instance
            package_name: Target Android app package (e.g. "com.govee.home")
            logger:       Callable for log messages: log(msg: str)
            should_stop:  Callable that returns True when execution should abort
        """
        self.d = device
        self.PACKAGE_NAME = package_name
        self._emit_log = logger or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self._step_callback = None  # (step_index, total, type, description, result)
        self._log_buffer: list[str] = []

    # ---- Logging ----
    def log(self, msg: str):
        self._emit_log(msg)
        self._log_buffer.append(msg)

    def clear_log_buffer(self):
        self._log_buffer.clear()

    def get_log_buffer(self) -> list[str]:
        return list(self._log_buffer)

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

    # ---- Element existence ----
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

    def exists_indexed(self, xpath: str, index: int) -> bool:
        try:
            elements = self.d.xpath(xpath).all()
            return len(elements) > index
        except Exception:
            return False

    # ---- Element actions ----
    def click(self, xpath: str):
        self.d.xpath(xpath).click()

    def click_indexed(self, xpath: str, index: int) -> bool:
        try:
            elements = self.d.xpath(xpath).all()
            if len(elements) > index:
                elements[index].click()
                return True
            return False
        except Exception:
            return False

    def long_click(self, xpath: str, duration: float = 0.8):
        self.d.xpath(xpath).long_click(duration=duration)

    def swipe(self, direction: str, distance: int = 500):
        w, h = self.d.window_size()
        cx, cy = w // 2, h // 2
        dirs = {
            'up': (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
            'down': (cx, h // 4, cx, h // 4 + distance),
            'left': (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
            'right': (w // 4, cy, w // 4 + distance, cy),
        }
        x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
        self.d.swipe(x1, y1, x2, y2)

    def drag(self, xpath: str, direction: str, distance: int = 300):
        el = self.d.xpath(xpath).get()
        if el:
            x = (el.bounds[0] + el.bounds[2]) // 2
            y = (el.bounds[1] + el.bounds[3]) // 2
            dirs = {
                'up': (x, y, x, y - distance),
                'down': (x, y, x, y + distance),
                'left': (x, y, x - distance, y),
                'right': (x, y, x + distance, y),
            }
            x1, y1, x2, y2 = dirs.get(direction, (x, y, x, y - distance))
            self.d.swipe(x1, y1, x2, y2, duration=0.5)

    def get_text(self, xpath: str) -> str:
        try:
            el = self.d.xpath(xpath).get()
            return el.attrib.get("text", "") if el is not None else ""
        except Exception:
            return ""

    # ---- App lifecycle ----
    def kill_app(self, pkg: str):
        """Force-stop an app with fallback to ensure process termination.

        Uses am force-stop (primary) + am kill + pkill (fallback) to
        ensure the app is fully killed rather than just sent to background.
        """
        self.log(f"正在杀掉 App: {pkg}")
        # Primary: am force-stop via uiautomator2
        self.d.app_stop(pkg)
        # Fallback: kill any remaining background processes
        try:
            self.d.shell(["am", "kill", pkg])
        except Exception:
            pass
        try:
            self.d.shell(["pkill", "-f", pkg])
        except Exception:
            pass

    def kill_and_start(self, sleep_after_start: float = 3):
        pkg = self.PACKAGE_NAME
        self.kill_app(pkg)
        self.sleep(2)
        self.log(f"正在启动 App: {pkg}")
        self.d.app_start(pkg)
        self.sleep(sleep_after_start)

    # ---- Composite helpers ----
    def wait_for_either(self, xpath_a: str, xpath_b: str,
                        timeout: float = 30) -> str:
        """Poll two elements, return on first hit.
        Returns: 'a' | 'b' | 'timeout' | 'stopped'
        """
        self.log(f'轮询检查两个元素 (超时 {timeout}s)...')
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.stopped():
                return "stopped"
            if self.d.xpath(xpath_a).exists:
                return "a"
            if self.d.xpath(xpath_b).exists:
                return "b"
            self.sleep(0.3)
        return "timeout" if not self.stopped() else "stopped"

    def wait_for_either_indexed(self, xpath_a: str, idx_a: int,
                                 xpath_b: str, idx_b: int,
                                 timeout: float = 30) -> str:
        self.log(f'轮询等待二选一索引元素 (超时 {timeout}s)...')
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.stopped():
                return "stopped"
            if self.exists_indexed(xpath_a, idx_a):
                return "a"
            if self.exists_indexed(xpath_b, idx_b):
                return "b"
            self.sleep(0.3)
        return "timeout"

    def wait_for_toast(self, expected_text: str, timeout: float = 15) -> bool:
        self.log(f'等待Toast「{expected_text}」出现 (超时 {timeout}s)...')
        deadline = time.time() + timeout
        try:
            self.d.toast.reset()
        except Exception:
            pass
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
                pass
            self.sleep(0.3)
        return False

    def wait_appear_then_disappear(self, xpath: str,
                                    timeout: float = 30) -> bool:
        self.log(f'等待 "{xpath}" 出现后消失 (超时 {timeout}s)...')
        deadline = time.time() + timeout
        appeared = False
        while time.time() < deadline:
            if self.stopped():
                return False
            if self.d.xpath(xpath).exists:
                self.log('  元素已出现，等待消失...')
                appeared = True
                break
            self.sleep(0.3)
        if not appeared:
            self.log('  超时: 元素未出现')
            return False
        while time.time() < deadline:
            if self.stopped():
                return False
            if not self.d.xpath(xpath).exists:
                self.log('  元素已消失')
                return True
            self.sleep(0.3)
        self.log('  超时: 元素未消失')
        return False
