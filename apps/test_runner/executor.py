"""
Step executor — interprets TestStep sequences and calls DeviceAdapter methods.
Migrated from sku_stress_test, adapted to use DeviceAdapter instead of TestExecutor.
"""
import time
from models.step_types import TestStep


class StepExecutor:
    """Executes a sequence of TestSteps using a DeviceAdapter instance."""

    def __init__(self, adapter):
        """
        Args:
            adapter: DeviceAdapter instance (wraps u2 device + logging + stop control)
        """
        self.exe = adapter

    def execute(self, step: TestStep) -> str:
        """Execute one step. Returns 'pass' | 'fail' | 'stopped'."""
        t = step.type
        if self.exe.stopped():
            return "stopped"

        handlers = {
            "click": self._do_click,
            "long_click": self._do_long_click,
            "click_indexed": self._do_click_indexed,
            "swipe": self._do_swipe,
            "drag": self._do_drag,
            "wait": self._do_wait,
            "wait_disappear": self._do_wait_disappear,
            "wait_either": self._do_wait_any,
            "wait_any": self._do_wait_any,
            "wait_toast": self._do_wait_toast,
            "verify_text": self._do_verify_text,
            "poll_text": self._do_poll_text,
            "sleep": self._do_sleep,
            "kill_app": self._do_kill_app,
            "start_app": self._do_start_app,
            "restart_app": self._do_restart_app,
            "retry_click": self._do_retry_click,
            "log": self._do_log,
        }

        handler = handlers.get(t)
        if handler:
            return handler(step)
        self.exe.log(f"未知步骤类型: {t}")
        return "fail"

    def execute_all(self, steps: list[TestStep]) -> str:
        """Execute a sequence of steps. Returns status of first failure, or 'pass'."""
        total = len(steps)
        for i, step in enumerate(steps):
            desc = step.description or step.xpath or step.expected_text or ''
            self.exe.log(f'── 步骤 {i+1}/{total} [{step.type}] {desc[:80]}')
            result = self.execute(step)
            # Notify via adapter callback
            if self.exe._step_callback:
                self.exe._step_callback(i, total, step.type, desc[:100], result)
            if result != "pass":
                self.exe.log(f'    ↳ 失败 ({result})')
                return result
            self.exe.log(f'    ↳ 通过')
        return "pass"

    # ---- Implementations ----

    def _do_click(self, s: TestStep) -> str:
        self.exe.log(f'点击: {s.description or s.xpath}')
        self.exe.click(s.xpath)
        return "pass"

    def _do_long_click(self, s: TestStep) -> str:
        dur = s.timeout if s.timeout > 0 else 0.8
        self.exe.log(f'长按 {dur}s: {s.description or s.xpath}')
        self.exe.long_click(s.xpath, dur)
        return "pass"

    def _do_swipe(self, s: TestStep) -> str:
        self.exe.log(f'滑动: {s.direction} {s.distance}px')
        self.exe.swipe(s.direction, s.distance)
        return "pass"

    def _do_drag(self, s: TestStep) -> str:
        self.exe.log(f'拖动: {s.description or s.xpath} → {s.direction} {s.distance}px')
        self.exe.drag(s.xpath, s.direction, s.distance)
        return "pass"

    def _do_click_indexed(self, s: TestStep) -> str:
        self.exe.log(f'点击第{s.index+1}个: {s.description or s.xpath}')
        if self.exe.click_indexed(s.xpath, s.index):
            return "pass"
        self.exe.log(f'错误: 点击第{s.index+1}个元素失败')
        return "fail"

    def _do_wait(self, s: TestStep) -> str:
        interval = (s.index if s.index > 0 else 0.5)
        self.exe.log(f'等待: {s.description or s.xpath} (超时 {s.timeout}s, 间隔 {interval}s)')
        deadline = time.time() + s.timeout
        while time.time() < deadline:
            if self.exe.stopped():
                return "stopped"
            if self.exe.d.xpath(s.xpath).exists:
                return "pass"
            self.exe.sleep(interval)
        if self.exe.stopped():
            return "stopped"
        self.exe.log(f'错误: {s.timeout}s 内未找到 {s.description or s.xpath}')
        return "fail"

    def _do_wait_disappear(self, s: TestStep) -> str:
        if self.exe.wait_appear_then_disappear(s.xpath, timeout=s.timeout):
            return "pass"
        if self.exe.stopped():
            return "stopped"
        self.exe.log(f'错误: {s.description or s.xpath} 未出现或未消失')
        return "fail"

    def _do_wait_any(self, s: TestStep) -> str:
        # Support multiple XPaths separated by | (e.g. "xpath1|xpath2|xpath3")
        xpaths = [x.strip() for x in (s.xpath or '').split('|') if x.strip()]
        if not xpaths:
            self.exe.log('错误: 未指定元素')
            return 'fail'
        self.exe.log(f'等待 {len(xpaths)} 个元素中任意一个出现 (超时 {s.timeout}s)...')
        deadline = time.time() + s.timeout
        while time.time() < deadline:
            if self.exe.stopped():
                return 'stopped'
            for xp in xpaths:
                if self.exe.exists(xp):
                    self.exe.log(f'  元素已出现: {xp[:60]}')
                    return 'pass'
            self.exe.sleep(0.3)
        self.exe.log(f'错误: {s.timeout}s 内无元素出现')
        return 'fail'

    def _do_wait_toast(self, s: TestStep) -> str:
        if self.exe.wait_for_toast(s.expected_text, timeout=s.timeout):
            return "pass"
        if self.exe.stopped():
            return "stopped"
        self.exe.log(f'错误: {s.timeout}s 内未出现Toast「{s.expected_text}」')
        return "fail"

    def _do_verify_text(self, s: TestStep) -> str:
        text = self.exe.get_text(s.xpath)
        self.exe.log(f'文本: "{text}" (期望: "{s.expected_text}")')
        if text == s.expected_text:
            return "pass"
        self.exe.log(f'错误: 文本不匹配')
        return "fail"

    def _do_poll_text(self, s: TestStep) -> str:
        interval = (s.index if s.index > 0 else 0.5)
        self.exe.log(f'轮询等待文本变为 "{s.expected_text}" (超时 {s.timeout}s, 间隔 {interval}s)...')
        deadline = time.time() + s.timeout
        last_text = ""
        while time.time() < deadline:
            if self.exe.stopped():
                return "stopped"
            if self.exe.d.xpath(s.xpath).exists:
                text = self.exe.get_text(s.xpath)
                if text != last_text:
                    self.exe.log(f'  当前: "{text}"')
                    last_text = text
                if text == s.expected_text:
                    return "pass"
            self.exe.sleep(interval)
        self.exe.log(f'错误: {s.timeout}s 内文本未变为 "{s.expected_text}", 最后: "{last_text}"')
        return "fail"

    def _do_sleep(self, s: TestStep) -> str:
        self.exe.log(f'等待 {s.timeout}s...')
        self.exe.sleep(s.timeout)
        return "stopped" if self.exe.stopped() else "pass"

    def _do_kill_app(self, s: TestStep = None) -> str:
        pkg = (s.xpath if s and s.xpath else self.exe.PACKAGE_NAME)
        if not pkg:
            self.exe.log('错误: 未指定包名（请在步骤中填写 xpath="com.example.app" 或用例中设置包名）')
            return "fail"
        self.exe.kill_app(pkg)
        self.exe.sleep(2)
        return "pass"

    def _do_start_app(self, s: TestStep = None) -> str:
        pkg = (s.xpath if s and s.xpath else self.exe.PACKAGE_NAME)
        if not pkg:
            self.exe.log('错误: 未指定包名（请在步骤中填写 xpath="com.example.app" 或用例中设置包名）')
            return "fail"
        self.exe.log(f"正在启动 App: {pkg}")
        self.exe.d.app_start(pkg)
        self.exe.sleep(3)
        return "pass"

    def _do_restart_app(self, s: TestStep) -> str:
        pkg = (s.xpath if s.xpath else self.exe.PACKAGE_NAME)
        if not pkg:
            self.exe.log('错误: 未指定包名（请在步骤中填写 xpath="com.example.app" 或用例中设置包名）')
            return "fail"
        kill_wait = (s.index if s.index > 0 else 2)
        start_wait = (s.timeout if s.timeout > 0 else 3)
        self.exe.kill_app(pkg)
        self.exe.log(f'等待 {kill_wait}s...')
        self.exe.sleep(kill_wait)
        self.exe.log(f"正在启动 App: {pkg}")
        self.exe.d.app_start(pkg)
        self.exe.log(f'等待 {start_wait}s...')
        self.exe.sleep(start_wait)
        return "pass"

    def _do_retry_click(self, s: TestStep) -> str:
        max_attempts = s.index if s.index > 0 else 5
        self.exe.log(f'点击 {s.description or s.xpath} (最多重试{max_attempts}次, 每次{s.timeout}s)')
        for attempt in range(1, max_attempts + 1):
            if self.exe.stopped():
                return "stopped"
            self.exe.log(f'  第{attempt}/{max_attempts}次: 点击')
            self.exe.click(s.xpath)
            if self.exe.exists(s.xpath2, timeout=s.timeout):
                self.exe.log(f'  成功')
                return "pass"
            self.exe.log(f'  未在 {s.timeout}s 内出现, 重试...')
        self.exe.log(f'错误: {max_attempts}次点击后仍未成功')
        return "fail"

    def _do_log(self, s: TestStep) -> str:
        self.exe.log(s.description or s.xpath)
        return "pass"
