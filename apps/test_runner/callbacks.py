"""TestRunnerCallback bridge → Channels consumers."""
import json
from .runner import TestRunnerCallback


class WsTestCallback(TestRunnerCallback):
    """Bridges TestRunnerCallback events to Django Channels WebSocket consumers."""

    def __init__(self):
        self.clients: dict[str, set] = {}

    def register(self, run_id: str, consumer):
        if run_id not in self.clients:
            self.clients[run_id] = set()
        self.clients[run_id].add(consumer)

    def unregister(self, run_id: str, consumer):
        if run_id in self.clients:
            self.clients[run_id].discard(consumer)

    async def _broadcast(self, run_id: str, msg: dict):
        dead = []
        if run_id in self.clients:
            for consumer in self.clients[run_id]:
                try:
                    await consumer.send(text_data=json.dumps(msg, ensure_ascii=False))
                except Exception:
                    dead.append(consumer)
            for consumer in dead:
                self.unregister(run_id, consumer)

    async def on_log(self, run_id: str, message: str):
        await self._broadcast(run_id, {"type": "log", "run_id": run_id, "message": message})

    async def on_case_started(self, run_id: str, case_id: str, case_title: str, loop_count: int):
        await self._broadcast(run_id, {"type": "case_started", "run_id": run_id,
                                        "case_id": case_id, "case_title": case_title,
                                        "loop_count": loop_count})

    async def on_iteration_result(self, run_id: str, case_id: str,
                                   iteration: int, result: str, duration_ms: float):
        await self._broadcast(run_id, {"type": "iteration_result", "run_id": run_id,
                                        "case_id": case_id, "iteration": iteration,
                                        "result": result, "duration_ms": duration_ms})

    async def on_case_finished(self, run_id: str, case_id: str,
                                pass_count: int, fail_count: int, rate: str):
        await self._broadcast(run_id, {"type": "case_finished", "run_id": run_id,
                                        "case_id": case_id, "pass": pass_count,
                                        "fail": fail_count, "rate": rate})

    async def on_step_started(self, run_id: str, case_id: str,
                               iteration: int, step_index: int, total_steps: int,
                               step_type: str, description: str):
        await self._broadcast(run_id, {
            "type": "step_started", "run_id": run_id,
            "case_id": case_id, "iteration": iteration,
            "step_index": step_index, "total_steps": total_steps,
            "step_type": step_type, "description": description,
        })

    async def on_step_result(self, run_id: str, case_id: str,
                              iteration: int, step_index: int, total_steps: int,
                              step_type: str, description: str, result: str):
        await self._broadcast(run_id, {
            "type": "step_result", "run_id": run_id,
            "case_id": case_id, "iteration": iteration,
            "step_index": step_index, "total_steps": total_steps,
            "step_type": step_type, "description": description,
            "result": result,
        })

    async def on_run_finished(self, run_id: str, summary: dict,
                               csv_path: str, log_path: str):
        await self._broadcast(run_id, {"type": "run_finished", "run_id": run_id,
                                        "summary": summary, "csv_path": csv_path,
                                        "log_path": log_path})

    async def on_device_error(self, run_id: str, error: str):
        await self._broadcast(run_id, {"type": "device_error", "run_id": run_id, "error": error})


test_callbacks = WsTestCallback()
