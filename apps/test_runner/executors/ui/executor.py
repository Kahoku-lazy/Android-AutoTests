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
            "swipe": self._do_swipe,
            "wait": self._do_wait,
            "wait_disappear": self._do_wait_disappear,
            "verify_text": self._do_verify_text,
            "poll_text": self._do_poll_text,
            "sleep": self._do_sleep,
            "start_app": self._do_start_app,
            "kill_app": self._do_kill_app,
            "perf_element_time": self._do_perf_element_time,
            "wait_toast": self._do_wait_toast,
            "if_element_appear": self._do_if_appear,
            "if_element_disappear": self._do_if_disappear,
            "loop_n": self._do_loop_n,
            "loop_elements": self._do_loop_elements,
        }

        handler = handlers.get(t)
        if handler:
            return handler(step)
        self.exe.log(f"未知步骤类型: {t}")
        return "fail"

    def execute_all(self, steps: list[TestStep], depth: int = 0) -> str:
        """Execute a sequence of steps. Returns status of first failure, or 'pass'.

        Supports hierarchical steps: if/loop containers recursively execute their
        children. Watcher checks are run before each leaf step.
        """
        total = len(steps)
        prefix = "  " * depth
        for i, step in enumerate(steps):
            # ── Watcher check before each step ──
            self.exe.run_watchers()

            desc = step.description or step.xpath or step.expected_text or ''
            self.exe.log(f'{prefix}── 步骤 {i+1}/{total} [{step.type}] {desc[:80]}')
            # Notify step started before execution
            if self.exe._step_started_callback:
                self.exe._step_started_callback(i, total, step.type, desc[:100])

            # ── Container steps: execute children recursively ──
            is_container = step.type in ("if_element_appear", "if_element_disappear", "loop_n", "loop_elements")
            if is_container:
                result = self.execute(step)
                if result == "pass" and step.children:
                    child_result = self.execute_all(step.children, depth + 1)
                    if child_result != "pass":
                        self.exe.log(f'{prefix}    ↳ 子步骤失败')
                        if self.exe._step_callback:
                            self.exe._step_callback(i, total, step.type, desc[:100], child_result)
                        return child_result
                if self.exe._step_callback:
                    self.exe._step_callback(i, total, step.type, desc[:100], result)
                if result not in ("pass", "skip"):
                    self.exe.log(f'{prefix}    ↳ 失败 ({result})')
                    return result
                self.exe.log(f'{prefix}    ↳ 通过')
                continue

            result = self.execute(step)
            # Notify step result after execution
            if self.exe._step_callback:
                self.exe._step_callback(i, total, step.type, desc[:100], result)
            if result != "pass":
                self.exe.log(f'{prefix}    ↳ 失败 ({result})')
                return result
            self.exe.log(f'{prefix}    ↳ 通过')
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

    def _do_wait(self, s: TestStep) -> str:
        interval = (s.index if s.index > 0 else 0.5)
        self.exe.log(f'等待: {s.description or s.xpath} (超时 {s.timeout}s, 间隔 {interval}s)')
        deadline = time.time() + s.timeout
        while time.time() < deadline:
            if self.exe.stopped():
                return "stopped"
            if self.exe.exists(s.xpath, timeout=0):
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
        start_time = time.time()
        deadline = start_time + s.timeout
        last_text = ""
        while time.time() < deadline:
            if self.exe.stopped():
                return "stopped"
            if self.exe.exists(s.xpath, timeout=0):
                text = self.exe.get_text(s.xpath)
                if text != last_text:
                    self.exe.log(f'  当前: "{text}"')
                    last_text = text
                if text == s.expected_text:
                    elapsed = time.time() - start_time
                    self.exe.log(f'轮询文本 "{s.expected_text}" 在第 {elapsed:.1f} 秒出现')
                    return "pass"
            self.exe.sleep(interval)
        elapsed = time.time() - start_time
        self.exe.log(f'错误: {s.timeout}s 超时，轮询文本 "{s.expected_text}" 已等待 {elapsed:.1f} 秒, 最后: "{last_text}"')
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

    def _do_perf_element_time(self, s: TestStep) -> str:
        desc = s.description or s.xpath
        timeout = s.timeout if s.timeout > 0 else 10
        self.exe.log(f'等待元素出现耗时: 开始计时 "{desc}" (超时 {timeout}s)')
        start_time = time.time()
        deadline = start_time + timeout
        while time.time() < deadline:
            if self.exe.stopped():
                return "stopped"
            if self.exe.exists(s.xpath, timeout=0):
                elapsed = time.time() - start_time
                self.exe.log(f'等待元素出现耗时: "{desc}" 出现耗时 {elapsed:.2f}s')
                self.exe._perf_results.append({
                    "description": desc,
                    "duration": round(elapsed, 3),
                })
                return "pass"
            self.exe.sleep(0.2)
        if self.exe.stopped():
            return "stopped"
        self.exe.log(f'错误: {timeout}s 内未找到 "{desc}"')
        return "fail"

    def _do_wait_toast(self, s: TestStep) -> str:
        desc = s.expected_text or s.description
        timeout = s.timeout if s.timeout > 0 else 10
        self.exe.log(f'等待Toast: "{desc}" (超时 {timeout}s)')
        if self.exe.wait_for_toast(desc, timeout=timeout):
            return "pass"
        if self.exe.stopped():
            return "stopped"
        self.exe.log(f'错误: {timeout}s 内未出现Toast「{desc}」')
        return "fail"

    def _do_if_appear(self, s: TestStep) -> str:
        desc = s.description or s.xpath
        self.exe.log(f'判断: 如果 "{desc}" 出现')
        if self.exe.exists(s.xpath, timeout=s.timeout if s.timeout > 0 else 5):
            self.exe.log(f'  条件满足 — "{desc}" 已出现，执行子步骤 ({len(s.children)}个)')
            return "pass"
        self.exe.log(f'  条件不满足 — "{desc}" 未出现，跳过子步骤')
        return "skip"

    def _do_if_disappear(self, s: TestStep) -> str:
        desc = s.description or s.xpath
        self.exe.log(f'判断: 如果 "{desc}" 消失')
        if not self.exe.exists(s.xpath, timeout=0):
            self.exe.log(f'  条件满足 — "{desc}" 已消失，执行子步骤 ({len(s.children)}个)')
            return "pass"
        self.exe.log(f'  条件不满足 — "{desc}" 仍存在，跳过子步骤')
        return "skip"

    def _do_loop_n(self, s: TestStep) -> str:
        n = s.index if s.index > 0 else 1
        desc = s.description or f'循环{n}次'
        self.exe.log(f'循环: {desc}')
        for i in range(n):
            if self.exe.stopped():
                return "stopped"
            self.exe.log(f'  ── 第 {i+1}/{n} 次 ──')
            child_result = self.execute_all(s.children, depth=1)
            if child_result and child_result not in ("pass", "skip"):
                return child_result
        return "pass"

    def _do_loop_elements(self, s: TestStep) -> str:
        xpaths = [x.strip() for x in (s.xpath or '').split('|') if x.strip()]
        if not xpaths:
            self.exe.log('错误: 未指定元素列表（多个XPath用 | 分隔）')
            return 'fail'
        # Support indexed clicking: if index > 0, click each element by index
        use_index = s.index if s.index > 0 else 0
        self.exe.log(f'遍历元素列表: {len(xpaths)} 个元素')
        for idx, xp in enumerate(xpaths):
            if self.exe.stopped():
                return "stopped"
            self.exe.log(f'  ── 第 {idx+1}/{len(xpaths)} 个: {xp[:60]} ──')
            if use_index:
                if not self.exe.click_indexed(xp, use_index - 1):
                    self.exe.log(f'  错误: 点击第{use_index}个元素失败')
                    return "fail"
            else:
                self.exe.click(xp)
            # Execute child steps after each click (e.g. wait for page transition)
            if s.children:
                child_result = self.execute_all(s.children, depth=1)
                if child_result and child_result not in ("pass", "skip"):
                    return child_result
        return "pass"

