"""TestRunnerCallback bridge → Channels consumers.

TREP v1.0 Protocol 3: Scheduler → Frontend WebSocket events.
- gather + timeout 并发广播，慢客户端不拖垮其他人
- seq 递增序号，前端检测 gap → 触发对账
- heartbeat 每 5s，前端 15s 无心跳 → 连接丢失指示
"""

import asyncio
import json

from .runner import TestRunnerCallback


class WsTestCallback(TestRunnerCallback):
    """Bridges TestRunnerCallback events to Django Channels WebSocket consumers.

    TREP v1.0: 每条消息带 seq 递增序号，广播用 gather + 2s 超时。
    """

    def __init__(self):
        self.clients: dict[str, set] = {}
        self._seq: dict[str, int] = {}  # run_id → next sequence number

    def register(self, run_id: str, consumer):
        if run_id not in self.clients:
            self.clients[run_id] = set()
        self.clients[run_id].add(consumer)

    def unregister(self, run_id: str, consumer):
        if run_id in self.clients:
            self.clients[run_id].discard(consumer)

    def _next_seq(self, run_id: str) -> int:
        """Return next monotonic seq for run_id, starting from 1."""
        n = self._seq.get(run_id, 0) + 1
        self._seq[run_id] = n
        return n

    async def _broadcast(self, run_id: str, msg: dict, timeout: float = 2.0):
        """并发广播到所有注册的 consumer，每个 send 最多等 timeout 秒。

        TREP v1.0: gather + timeout — 慢客户端不拖垮其他人。
        """
        if run_id not in self.clients or not self.clients[run_id]:
            return
        msg["seq"] = self._next_seq(run_id)
        consumers = list(self.clients[run_id])

        async def _send_one(consumer):
            try:
                await asyncio.wait_for(
                    consumer.send(text_data=json.dumps(msg, ensure_ascii=False)),
                    timeout=timeout,
                )
            except (asyncio.TimeoutError, Exception):
                self.clients[run_id].discard(consumer)

        await asyncio.gather(*[_send_one(c) for c in consumers], return_exceptions=True)

    async def on_log(self, run_id: str, message: str):
        await self._broadcast(run_id, {"type": "log", "run_id": run_id, "message": message})

    async def on_run_started(self, run_id: str):
        """预检通过、正式进入执行 —— 前端据此从「准备中」切到「执行中」。"""
        await self._broadcast(run_id, {"type": "run_started", "run_id": run_id})

    async def on_case_started(self, run_id: str, case_id: str, case_title: str, loop_count: int):
        await self._broadcast(
            run_id,
            {
                "type": "case_started",
                "run_id": run_id,
                "case_id": case_id,
                "case_title": case_title,
                "loop_count": loop_count,
            },
        )

    async def on_iteration_result(
        self, run_id: str, case_id: str, iteration: int, result: str, duration_ms: float
    ):
        await self._broadcast(
            run_id,
            {
                "type": "iteration_result",
                "run_id": run_id,
                "case_id": case_id,
                "iteration": iteration,
                "result": result,
                "duration_ms": duration_ms,
            },
        )

    async def on_case_finished(
        self, run_id: str, case_id: str, pass_count: int, fail_count: int, rate: str
    ):
        await self._broadcast(
            run_id,
            {
                "type": "case_finished",
                "run_id": run_id,
                "case_id": case_id,
                "pass": pass_count,
                "fail": fail_count,
                "rate": rate,
            },
        )

    async def on_step_started(
        self,
        run_id: str,
        case_id: str,
        iteration: int,
        step_index: int,
        total_steps: int,
        step_type: str,
        description: str,
    ):
        await self._broadcast(
            run_id,
            {
                "type": "step_started",
                "run_id": run_id,
                "case_id": case_id,
                "iteration": iteration,
                "step_index": step_index,
                "total_steps": total_steps,
                "step_type": step_type,
                "description": description,
            },
        )

    async def on_step_result(
        self,
        run_id: str,
        case_id: str,
        iteration: int,
        step_index: int,
        total_steps: int,
        step_type: str,
        description: str,
        result: str,
    ):
        await self._broadcast(
            run_id,
            {
                "type": "step_result",
                "run_id": run_id,
                "case_id": case_id,
                "iteration": iteration,
                "step_index": step_index,
                "total_steps": total_steps,
                "step_type": step_type,
                "description": description,
                "result": result,
            },
        )

    async def on_run_finished(self, run_id: str, summary: dict, log_path: str):
        await self._broadcast(
            run_id,
            {"type": "run_finished", "run_id": run_id, "summary": summary, "log_path": log_path},
        )
        self._seq.pop(run_id, None)  # 清理 seq 计数器
        self.clients.pop(run_id, None)  # 清理 clients 集合

    async def on_device_error(self, run_id: str, error: str):
        await self._broadcast(run_id, {"type": "device_error", "run_id": run_id, "message": error})

    async def on_heartbeat(self, run_id: str):
        """每 5s 心跳 — 前端据此检测连接存活（15s 无心跳 → 连接丢失）。"""
        await self._broadcast(run_id, {"type": "heartbeat", "run_id": run_id})


test_callbacks = WsTestCallback()
