"""WsTestCallback 广播测试 — register/unregister/seq/事件类型/超时丢弃。

Mock Django Channels Consumer（AsyncMock），不依赖真实 WebSocket。
"""

import json
import asyncio
import pytest
from unittest.mock import AsyncMock
from apps.test_runner.callbacks import WsTestCallback


class TestRegisterUnregister:
    def test_register_adds_consumer(self):
        cb = WsTestCallback()
        consumer = AsyncMock()
        cb.register("run-1", consumer)
        assert "run-1" in cb.clients
        assert consumer in cb.clients["run-1"]

    def test_unregister_removes_consumer(self):
        cb = WsTestCallback()
        consumer = AsyncMock()
        cb.register("run-1", consumer)
        cb.unregister("run-1", consumer)
        assert consumer not in cb.clients["run-1"]

    def test_multiple_consumers_same_run(self):
        """一个运行可以有多个前端连接（如多标签页打开）。"""
        cb = WsTestCallback()
        c1, c2 = AsyncMock(), AsyncMock()
        cb.register("run-1", c1)
        cb.register("run-1", c2)
        assert len(cb.clients["run-1"]) == 2


class TestSeq:
    def test_first_seq_is_one(self):
        cb = WsTestCallback()
        assert cb._next_seq("run-1") == 1

    def test_seq_increments(self):
        cb = WsTestCallback()
        assert cb._next_seq("run-1") == 1
        assert cb._next_seq("run-1") == 2
        assert cb._next_seq("run-1") == 3

    def test_seq_per_run_independent(self):
        """不同 run_id 的 seq 互相独立。"""
        cb = WsTestCallback()
        assert cb._next_seq("run-1") == 1
        assert cb._next_seq("run-2") == 1
        assert cb._next_seq("run-1") == 2


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_consumers(self):
        cb = WsTestCallback()
        c1, c2 = AsyncMock(), AsyncMock()
        cb.register("run-1", c1)
        cb.register("run-1", c2)

        await cb._broadcast("run-1", {"type": "log", "message": "hello"})

        c1.send.assert_called_once()
        c2.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_injects_seq(self):
        cb = WsTestCallback()
        consumer = AsyncMock()
        cb.register("run-1", consumer)

        await cb._broadcast("run-1", {"type": "log", "message": "test"})

        call_args = consumer.send.call_args[1]["text_data"]
        msg = json.loads(call_args)
        assert msg["seq"] == 1
        assert msg["type"] == "log"

    @pytest.mark.asyncio
    async def test_broadcast_no_consumers_does_nothing(self):
        cb = WsTestCallback()
        # 不注册任何 consumer，广播不报错
        await cb._broadcast("run-1", {"type": "log"})

    @pytest.mark.asyncio
    async def test_slow_consumer_discarded_on_timeout(self):
        """慢 consumer 被超时丢弃，不影响其他 consumer。"""
        cb = WsTestCallback()
        fast = AsyncMock()
        slow = AsyncMock()

        async def slow_send(*args, **kwargs):
            await asyncio.sleep(10)

        slow.send = slow_send
        cb.register("run-1", fast)
        cb.register("run-1", slow)

        # 用 0.1s 超时 → slow 被丢弃，fast 正常收到
        await cb._broadcast("run-1", {"type": "log"}, timeout=0.1)

        fast.send.assert_called_once()
        # slow 已从 clients 中移除
        assert slow not in cb.clients.get("run-1", set())


class TestEventTypes:
    """10 种事件类型的消息格式。"""

    @pytest.mark.asyncio
    async def test_run_started(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_run_started("r1")
        msg = json.loads(c.send.call_args[1]["text_data"])
        assert msg["type"] == "run_started"

    @pytest.mark.asyncio
    async def test_case_started(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_case_started("r1", "TC-1", "Login", 3)
        msg = json.loads(c.send.call_args[1]["text_data"])
        assert msg["case_id"] == "TC-1"
        assert msg["loop_count"] == 3

    @pytest.mark.asyncio
    async def test_step_started_and_result(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_step_started("r1", "TC-1", 2, 3, 5, "click", "btn")
        await cb.on_step_result("r1", "TC-1", 2, 3, 5, "click", "btn", "pass")

        assert c.send.call_count == 2
        result_msg = json.loads(c.send.call_args_list[1][1]["text_data"])
        assert result_msg["result"] == "pass"

    @pytest.mark.asyncio
    async def test_iteration_result(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_iteration_result("r1", "TC-1", 2, "pass", 1500.0)
        msg = json.loads(c.send.call_args[1]["text_data"])
        assert msg["iteration"] == 2
        assert msg["duration_ms"] == 1500.0

    @pytest.mark.asyncio
    async def test_run_finished_clears_seq(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        cb._next_seq("r1")  # seq = 1
        cb._next_seq("r1")  # seq = 2
        assert cb._seq.get("r1") == 2

        await cb.on_run_finished("r1", {"total": 1}, "/logs/r1.log")
        # seq 计数器在 on_run_finished 中被清除
        assert "r1" not in cb._seq

    @pytest.mark.asyncio
    async def test_device_error(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_device_error("r1", "Device disconnected")
        msg = json.loads(c.send.call_args[1]["text_data"])
        assert msg["error"] == "Device disconnected"

    @pytest.mark.asyncio
    async def test_heartbeat(self):
        cb = WsTestCallback()
        c = AsyncMock()
        cb.register("r1", c)
        await cb.on_heartbeat("r1")
        msg = json.loads(c.send.call_args[1]["text_data"])
        assert msg["type"] == "heartbeat"
