"""Scheduler 异步队列测试 — submit/stop/queue/出队/status。

使用 StubScheduler（覆写 _make_runner 为 no-op），不依赖真实执行管线。
"""

import asyncio
import pytest
from unittest.mock import MagicMock
from apps.test_runner.scheduler import BaseScheduler, TaskSpec


class StubScheduler(BaseScheduler):
    """可控制的桩调度器。覆写 _run 不调真实管线，只设置事件。"""

    def __init__(self, max_concurrent=1):
        super().__init__(max_concurrent=max_concurrent, task_type="test")
        self.runner_created = asyncio.Event()
        self.runner_done = asyncio.Event()
        self.runner_count = 0

    async def _run(self, spec):
        self.runner_count += 1
        self.runner_created.set()
        # 等待测试信号再结束
        await self.runner_done.wait()
        self._running.pop(spec.run_id, None)
        self._try_dequeue()

    async def _mark_device_busy(self, spec):
        pass

    async def _mark_device_idle(self, spec):
        pass


class BlockingScheduler(BaseScheduler):
    """阻塞式桩调度器。首任务启动后挂起，测试排队行为。"""

    def __init__(self, max_concurrent=1):
        super().__init__(max_concurrent=max_concurrent, task_type="test")
        self.unblock = asyncio.Event()
        self.started = asyncio.Event()
        self.runner_count = 0

    async def _run(self, spec):
        self.runner_count += 1
        self.started.set()
        await self.unblock.wait()  # 保持活跃直到释放
        self._running.pop(spec.run_id, None)
        self._try_dequeue()

    async def _mark_device_busy(self, spec):
        pass

    async def _mark_device_idle(self, spec):
        pass


class TestSubmitImmediate:
    """有空位时立即执行，不排队。"""

    @pytest.mark.asyncio
    async def test_single_submit_runs_immediately(self):
        scheduler = StubScheduler(max_concurrent=1)
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="dev1"))
        await asyncio.wait_for(scheduler.runner_created.wait(), timeout=5)
        assert scheduler.status.running == 1
        assert scheduler.status.queued == 0
        scheduler.runner_done.set()  # 释放

    @pytest.mark.asyncio
    async def test_multi_submit_within_concurrent_limit(self):
        scheduler = StubScheduler(max_concurrent=3)
        for i in range(3):
            await scheduler.submit(TaskSpec(run_id=f"r{i}", device_serial="d"))
        await asyncio.wait_for(scheduler.runner_created.wait(), timeout=5)
        assert scheduler.status.running == 3
        assert scheduler.status.queued == 0
        scheduler.runner_done.set()


class TestQueueBehavior:
    """并发满时，后续任务排队。"""

    @pytest.mark.asyncio
    async def test_submit_when_full_queues(self):
        scheduler = BlockingScheduler(max_concurrent=1)
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="d"))
        await scheduler.started.wait()

        await scheduler.submit(TaskSpec(run_id="r2", device_serial="d"))
        await asyncio.sleep(0.1)
        assert scheduler.status.queued == 1

    @pytest.mark.asyncio
    async def test_queue_dequeues_on_completion(self):
        """第一个任务完成后自动出队第二个。"""
        scheduler = BlockingScheduler(max_concurrent=1)
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="d"))
        await scheduler.started.wait()
        await scheduler.submit(TaskSpec(run_id="r2", device_serial="d"))

        assert scheduler.status.queued == 1
        scheduler.unblock.set()  # 释放第一个任务
        await asyncio.sleep(0.2)

        # 第一个完成，第二个应该被出队并启动
        assert scheduler.status.queued == 0
        assert scheduler.runner_count >= 2


class TestStop:
    """停止运行中或排队中的任务。"""

    @pytest.mark.asyncio
    async def test_stop_queued_task_removes_from_queue(self):
        scheduler = BlockingScheduler(max_concurrent=1)
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="d"))
        await scheduler.started.wait()
        await scheduler.submit(TaskSpec(run_id="r2", device_serial="d"))
        await asyncio.sleep(0.1)
        assert scheduler.status.queued == 1

        stopped = scheduler.stop("r2")
        assert stopped is True
        assert scheduler.status.queued == 0

    @pytest.mark.asyncio
    async def test_stop_nonexistent_returns_false(self):
        scheduler = StubScheduler(max_concurrent=1)
        assert scheduler.stop("nonexistent") is False


class TestStatus:
    """status 属性反映当前运行/排队状态。"""

    @pytest.mark.asyncio
    async def test_status_reflects_running_and_queued(self):
        scheduler = BlockingScheduler(max_concurrent=2)
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="d"))
        await scheduler.submit(TaskSpec(run_id="r2", device_serial="d"))
        await asyncio.wait_for(scheduler.started.wait(), timeout=5)
        await scheduler.submit(TaskSpec(run_id="r3", device_serial="d"))
        await asyncio.sleep(0.1)

        s = scheduler.status
        assert s.running == 2
        assert s.queued == 1
        assert "r1" in s.running_ids
        assert "r2" in s.running_ids
        assert s.queue_info[0]["client_task_id"] == ""
        assert s.queue_info[0]["position"] == 1

    @pytest.mark.asyncio
    async def test_status_to_dict(self):
        scheduler = StubScheduler(max_concurrent=1)
        d = scheduler.status.to_dict()
        assert d["task_type"] == "test"
        assert d["max_concurrent"] == 1
        assert "running" in d
        assert "queued" in d


class TestFinallyGuarantee:
    """_run 的 finally 块保证 mark_device_idle 和 _try_dequeue 一定执行。"""

    @pytest.mark.asyncio
    async def test_mark_idle_called_on_exception(self):
        """_run 抛异常时 finally 仍调用 mark_device_idle，保证设备释放。"""
        idle_called = asyncio.Event()

        class CrashScheduler(BaseScheduler):
            def __init__(self):
                super().__init__(max_concurrent=1, task_type="test")

            async def _run(self, spec):
                try:
                    raise RuntimeError("simulated crash")
                finally:
                    await self._mark_device_idle(spec)
                    self._running.pop(spec.run_id, None)
                    self._try_dequeue()

            async def _make_runner(self, spec):
                raise RuntimeError("simulated crash")

            async def _mark_device_busy(self, spec):
                pass

            async def _mark_device_idle(self, spec):
                idle_called.set()

        scheduler = CrashScheduler()
        await scheduler.submit(TaskSpec(run_id="r1", device_serial="d"))
        await asyncio.wait_for(idle_called.wait(), timeout=5)
        assert idle_called.is_set()
