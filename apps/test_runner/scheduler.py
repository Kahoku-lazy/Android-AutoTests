"""
Scheduler -- 统一调度器：排队 + 并发控制 + 设备状态管理。

三种任务类型共享 BaseScheduler，仅 max_concurrent 和 executor_factory 不同。
设备状态变更的唯一入口。Executor 崩溃时 finally 兜底释放设备。
"""

import asyncio
import logging

from dataclasses import dataclass, field

_log = logging.getLogger("test_runner.scheduler")


# ═══════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════


@dataclass
class TaskSpec:
    """调度器传给执行器的统一任务描述"""

    run_id: str = ""
    task_type: str = ""  # ui_automation | api_testing | web_automation
    test_cases: list = field(default_factory=list)
    loop_count: int = 3
    interval_seconds: int = 5
    device_serial: str = ""  # 物理 serial 或虚拟 "api" / "web"
    client_task_id: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class SchedulerStatus:
    """调度器当前状态（供前端消费）"""

    task_type: str = ""
    max_concurrent: int = 0
    running: int = 0
    queued: int = 0
    running_ids: list = field(default_factory=list)
    queue_info: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "max_concurrent": self.max_concurrent,
            "running": self.running,
            "queued": self.queued,
            "running_ids": self.running_ids,
            "queue_info": self.queue_info,
        }


# ═══════════════════════════════════════════════════════
# 基础调度器
# ═══════════════════════════════════════════════════════


class BaseScheduler:
    """统一调度器基类 -- 排队 + 并发 + 设备状态。

    子类只需提供 max_concurrent 和 _make_runner(spec)。
    设备状态变更只在 submit 入口和 _run 出口/finally 中发生。
    """

    def __init__(self, max_concurrent: int, task_type: str):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._task_type = task_type
        self._max_concurrent = max_concurrent
        self._queue: list[TaskSpec] = []
        self._running: dict[str, asyncio.Task] = {}  # run_id -> asyncio.Task
        self._lock = asyncio.Lock()

    # ── 子类覆写 ──

    async def _make_runner(self, spec: TaskSpec):
        """子类覆写：根据 task_type 创建对应的 runner 实例。"""
        raise NotImplementedError

    async def _mark_device_busy(self, spec: TaskSpec):
        """子类覆写：标记设备 BUSY（仅 DeviceScheduler）"""

    async def _mark_device_idle(self, spec: TaskSpec):
        """子类覆写：标记设备 ONLINE（仅 DeviceScheduler）"""

    # ── 公共 API ──

    async def submit(self, spec: TaskSpec):
        """提交任务。有空位立即执行，否则排队。"""
        async with self._lock:
            if len(self._running) < self._max_concurrent:
                task = asyncio.create_task(self._run(spec))
                self._running[spec.run_id] = task
                task.add_done_callback(lambda t: self._running.pop(spec.run_id, None))
            else:
                self._queue.append(spec)
                _log.info(
                    "[%s] queued: %s (position %d)", self._task_type, spec.run_id, len(self._queue)
                )

    def stop(self, run_id: str) -> bool:
        """请求停止指定任务。返回是否找到。"""
        # 检查运行中
        if run_id in self._running:
            from .runner import stop_run

            return stop_run(run_id)
        # 检查排队中
        for i, spec in enumerate(self._queue):
            if spec.run_id == run_id:
                self._queue.pop(i)
                return True
        return False

    @property
    def status(self) -> SchedulerStatus:
        return SchedulerStatus(
            task_type=self._task_type,
            max_concurrent=self._max_concurrent,
            running=len(self._running),
            queued=len(self._queue),
            running_ids=list(self._running.keys()),
            queue_info=[
                {"client_task_id": s.client_task_id, "position": i + 1}
                for i, s in enumerate(self._queue)
            ],
        )

    # ── 内部管道 ──

    async def _run(self, spec: TaskSpec):
        """执行一个任务的完整管道。设备状态在入口/出口变更。"""
        serial = spec.device_serial
        _log.info("[%s] _run start: %s serial=%s", self._task_type, spec.run_id, serial)

        # ── 1. 入口：标记设备 BUSY ──
        await self._mark_device_busy(spec)

        try:
            # ── 2. 获取并发槽位 ──
            async with self._semaphore:
                # ── 3. 创建 runner 并执行 ──
                runner = await self._make_runner(spec)
                from .views.executor import _execute_tests

                await _execute_tests(
                    spec.run_id,
                    runner,
                    spec.test_cases,
                    spec.loop_count,
                    spec.interval_seconds,
                    serial,
                )

        except Exception:
            _log.exception("[%s] _run crashed: %s", self._task_type, spec.run_id)

        finally:
            # ── 4. 出口：标记设备 ONLINE（无论如何都执行）──
            await self._mark_device_idle(spec)
            _log.info("[%s] _run done: %s", self._task_type, spec.run_id)
            # ── 5. 释放槽位并尝试启动下一个排队任务 ──
            self._running.pop(spec.run_id, None)  # 在 done_callback 之前释放，解除死锁
            self._try_dequeue()

    def _try_dequeue(self):
        """从队列取下一个任务启动（非阻塞）。"""
        if self._queue and len(self._running) < self._max_concurrent:
            spec = self._queue.pop(0)
            _log.info(
                "[%s] dequeue: %s (remaining queue: %d)",
                self._task_type,
                spec.run_id,
                len(self._queue),
            )
            task = asyncio.create_task(self._run(spec))
            self._running[spec.run_id] = task
            task.add_done_callback(lambda t: self._running.pop(spec.run_id, None))


# ═══════════════════════════════════════════════════════
# 三个子类（仅配置差异 + 设备状态管理）
# ═══════════════════════════════════════════════════════


class DeviceScheduler(BaseScheduler):
    """设备调度器：每 serial 一个实例，max_concurrent=1。

    设备状态变更的唯一入口：
    - submit() → mark_device_busy + dp_acquire_device
    - _run() finally → mark_device_idle + dp_release_device + _schedule_next_queued
    """

    def __init__(self, serial: str):
        super().__init__(max_concurrent=1, task_type="ui_automation")
        self._serial = serial

    async def _make_runner(self, spec: TaskSpec):
        """创建 TestRunner: 设备连接 → 预检 → 返回 runner"""
        from .callbacks import test_callbacks
        from .executors.ui.connect import DeviceCheckError, check_and_connect_async
        from .runner import TestRunner
        from .runner import _device_executor as _u2_executor

        _log.info("[DeviceScheduler] connecting to %s", self._serial)
        try:
            d = await check_and_connect_async(
                self._serial, spec.run_id, test_callbacks, _u2_executor
            )
        except DeviceCheckError as e:
            raise ConnectionError(f"Device {self._serial} not available: {e}") from e

        pkg = spec.extra.get("package_name", "")
        return TestRunner(d, pkg, callback=test_callbacks)

    async def _mark_device_busy(self, spec: TaskSpec):
        """设备状态 → BUSY（DB + 内存）"""
        from asgiref.sync import sync_to_async

        from apps.device_pool.api import acquire_device as dp_acquire_device

        from .runner import mark_device_busy

        try:
            await sync_to_async(dp_acquire_device)(
                self._serial, user_id=f"runner-{self._serial}", timeout=3600
            )
        except ValueError:
            _log.warning(
                "[DeviceScheduler] dp_acquire_device failed for %s (already locked?)", self._serial
            )
        mark_device_busy(self._serial)

    async def _mark_device_idle(self, spec: TaskSpec):
        """设备状态 → ONLINE（DB + 内存），并触发队列调度"""
        from asgiref.sync import sync_to_async

        from apps.device_pool.api import release_device as dp_release_device

        from .runner import mark_device_idle
        from .views.helpers import _schedule_next_queued

        mark_device_idle(self._serial)
        try:
            await sync_to_async(dp_release_device)(self._serial, reason="manual")
        except Exception:
            _log.exception("[DeviceScheduler] dp_release_device failed for %s", self._serial)
        _schedule_next_queued(self._serial)


class VirtualScheduler(BaseScheduler):
    """虚拟调度器：API / Web 共用。仅 max_concurrent 和 runner 工厂不同。"""

    def __init__(self, max_concurrent, task_type, runner_factory):
        super().__init__(max_concurrent=max_concurrent, task_type=task_type)
        self._runner_factory = runner_factory

    async def _make_runner(self, spec: TaskSpec):
        from .views.execution import _bridge_ws_log

        return self._runner_factory(spec, _bridge_ws_log)


def _make_api_runner(spec, bridge_log):
    import asyncio

    from .callbacks import test_callbacks
    from .executors.api.adapter import ApiAdapter
    from .executors.api.executor import ApiExecutor
    from .remote_runner import RemoteTestRunner

    base_url = spec.extra.get("base_url", "")
    loop = asyncio.get_event_loop()
    adapter = ApiAdapter(
        base_url=base_url,
        logger=lambda msg, l=loop: bridge_log(spec.run_id, msg, l),
        should_stop=lambda: False,
    )
    return RemoteTestRunner(
        adapter, ApiExecutor(adapter), device_label="api", callback=test_callbacks
    )


def _make_web_runner(spec, bridge_log):
    import asyncio

    from .callbacks import test_callbacks
    from .executors.web.adapter import WebAdapter
    from .executors.web.executor import WebExecutor
    from .remote_runner import RemoteTestRunner

    loop = asyncio.get_event_loop()
    adapter = WebAdapter(
        logger=lambda msg, l=loop: bridge_log(spec.run_id, msg, l), should_stop=lambda: False
    )
    return RemoteTestRunner(
        adapter,
        WebExecutor(adapter),
        device_label="web",
        callback=test_callbacks,
        is_async_executor=True,
        cleanup=adapter.close,
    )


class ApiScheduler(VirtualScheduler):
    def __init__(self):
        super().__init__(
            max_concurrent=10, task_type="api_testing", runner_factory=_make_api_runner
        )


class WebScheduler(VirtualScheduler):
    def __init__(self):
        super().__init__(
            max_concurrent=3, task_type="web_automation", runner_factory=_make_web_runner
        )


# ═══════════════════════════════════════════════════════
# 全局注册表
# ═══════════════════════════════════════════════════════


class SchedulerRegistry:
    """调度器注册表 -- 管理所有调度器实例的生命周期。

    用法:
        registry = SchedulerRegistry()
        scheduler = registry.get("ui_automation", "emulator-5554")
        await scheduler.submit(spec)
    """

    def __init__(self):
        self._device_schedulers: dict[str, DeviceScheduler] = {}
        self._api = ApiScheduler()
        self._web = WebScheduler()

    def get(self, task_type: str, serial: str = "") -> BaseScheduler:
        """根据任务类型路由到正确的调度器实例。"""
        if task_type == "ui_automation":
            if not serial:
                raise ValueError("device_serial required for ui_automation tasks")
            if serial not in self._device_schedulers:
                self._device_schedulers[serial] = DeviceScheduler(serial)
            return self._device_schedulers[serial]
        elif task_type == "api_testing":
            return self._api
        elif task_type == "web_automation":
            return self._web
        raise ValueError(f"Unknown task_type: {task_type}")

    def stop_all(self):
        """停止所有正在执行的任务。"""
        for sched in self._device_schedulers.values():
            for rid in list(sched._running.keys()):
                sched.stop(rid)
        for rid in list(self._api._running.keys()):
            self._api.stop(rid)
        for rid in list(self._web._running.keys()):
            self._web.stop(rid)

    @property
    def global_status(self) -> dict:
        return {
            "api": self._api.status.to_dict(),
            "web": self._web.status.to_dict(),
            "devices": {s: sch.status.to_dict() for s, sch in self._device_schedulers.items()},
        }


# 模块级单例
registry = SchedulerRegistry()
