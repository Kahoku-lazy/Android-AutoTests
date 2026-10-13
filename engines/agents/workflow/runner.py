"""一次 SOP 运行：事件上屏、对话稿与按次计费。状态只保存 SOPRunState。"""

from __future__ import annotations

import asyncio
import time

from datetime import datetime
from zoneinfo import ZoneInfo

from agentscope.console import ConsoleRenderer
from agentscope.message import Msg, UserMsg
from agentscope.sop import SOP, SOPEngine, SOPPhase, SOPRunState

from ..billing import DeepSeekBilling
from ..messaging import DialogueLog

_SHANGHAI = ZoneInfo("Asia/Shanghai")
SCOPE_STANDALONE = "独立运行"


def _moment(stamp: object) -> datetime:
    """事件时间戳 → 计费时刻。

    Args:
        stamp: 事件的 created_at（ISO 字符串）。

    Returns:
        datetime；带时区时由计费器换算到北京时间，解析不了时取当前北京时间。
    """
    text = str(stamp or "").strip()
    if text:
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            # 明确忽略：时间戳格式不认识就退回当前时刻
            pass
    return datetime.now(_SHANGHAI)


class SopRunner:
    """驱动一次 SOP 运行：事件实时上屏，同时按角色写进对话稿。"""

    def __init__(
        self,
        sop: SOP,
        *,
        model: str = "",
        provider: str = "deepseek",
        state: SOPRunState | None = None,
        dialogue: DialogueLog | None = None,
        dialogue_enabled: bool = True,
    ) -> None:
        self.sop = sop
        self.model = str(model or "")
        self.provider = str(provider or "")
        self._started = time.monotonic()
        if not dialogue_enabled:
            self.dialogue = None
        elif dialogue is not None:
            self.dialogue = dialogue
        else:
            self.dialogue = DialogueLog(model=self.model)
        self.engine = SOPEngine(sop, state)
        self._scope = SCOPE_STANDALONE
        self._billing = DeepSeekBilling() if self.provider.strip().lower() == "deepseek" else None
        self._calls = 0
        self._usage = [0, 0, 0]
        self._cost = [0.0, 0.0, 0.0]
        self._per_agent: dict[str, dict] = {}
        self._agent = ""
        self._call_model = self.model

    @property
    def phase(self) -> SOPPhase:
        """整次运行的当前阶段。"""
        return self.engine.phase

    def run(self, content: str) -> SOPPhase:
        """跑一次流程，跑到全部完成或挂起为止。

        Args:
            content: 交给第一步的输入文本。

        Returns:
            推进后的运行阶段。
        """
        return asyncio.run(self.run_stream(content))

    async def run_stream(self, content: str) -> SOPPhase:
        """流式跑一次流程。

        Args:
            content: 交给第一步的输入文本。

        Returns:
            推进后的运行阶段。
        """
        return await self._drive(UserMsg(name="user", content=content))

    def resume(self, event) -> SOPPhase:
        """把外部答复交回挂起的那一步，接着往下跑。

        Args:
            event: UserConfirmResultEvent / ExternalExecutionResultEvent / UserInterruptEvent。

        Returns:
            推进后的运行阶段。
        """
        return asyncio.run(self.resume_stream(event))

    async def resume_stream(self, event) -> SOPPhase:
        """流式恢复挂起的那一步。

        Args:
            event: 外部答复事件。

        Returns:
            推进后的运行阶段。
        """
        return await self._drive(event)

    def dump_state(self) -> str:
        """导出 SOPRunState JSON。

        只含开场输入、每步阶段、交付与历次结论，不含执行者与验收者的对话上下文。

        Returns:
            运行状态 JSON 字符串。
        """
        return self.engine.state.model_dump_json()

    @classmethod
    def resume_from(
        cls,
        sop: SOP,
        saved_state: str,
        *,
        model: str = "",
        provider: str = "deepseek",
        dialogue: DialogueLog | None = None,
        dialogue_enabled: bool = True,
    ) -> SopRunner:
        """用存下来的 SOPRunState 重建运行器。

        智能体上下文不在这份 JSON 里，以重新传入的流程所带角色为准。

        Args:
            sop: 同一份流程定义，步骤数必须与状态一致。
            saved_state: dump_state() 存下的 JSON。
            model: 写进对话稿的模型名。
            provider: 模型提供商（只对 deepseek 计费）。
            dialogue: 对话稿；省略时按 `logs/agent_logs` 新建一份。
            dialogue_enabled: 为 False 时不写对话稿。

        Returns:
            接着跑的 SopRunner。
        """
        return cls(
            sop,
            model=model,
            provider=provider,
            state=SOPRunState.model_validate_json(saved_state),
            dialogue=dialogue,
            dialogue_enabled=dialogue_enabled,
        )

    def summary(self) -> list[dict]:
        """逐步汇总阶段与最后一条验收结论。

        Returns:
            与步骤同序的 [{subject, phase, passed, message, verifier}]。
        """
        rows: list[dict] = []
        for step, record in zip(self.sop.steps, self.engine.state.steps, strict=True):
            last = record.verifications[-1] if record.verifications else None
            rows.append(
                {
                    "subject": step.subject,
                    "phase": record.phase.value,
                    "passed": None if last is None else last.passed,
                    "message": "" if last is None else last.message,
                    "verifier": "" if last is None else last.verifier,
                }
            )
        return rows

    def run_usage(self) -> tuple[int, int, int]:
        """整次运行的累计用量。

        Returns:
            (输入 token, 输出 token, 缓存命中 token)。
        """
        return self._usage[0], self._usage[1], self._usage[2]

    def run_cost(self) -> tuple[float, float, float]:
        """整次运行的累计费用：每次模型调用分别计费后求和。

        Returns:
            (输入费用, 输出费用, 缓存命中费用)，元，各保留 4 位小数。
        """
        return round(self._cost[0], 4), round(self._cost[1], 4), round(self._cost[2], 4)

    def cost_report(self) -> dict:
        """整次运行的用量与费用明细。

        Returns:
            {calls, input_tokens, output_tokens, cache_hit_tokens, input_cost,
            output_cost, cache_hit_cost, total_cost, per_agent}；
            per_agent 按角色给出同名字段。
        """
        return {
            "calls": self._calls,
            "input_tokens": self._usage[0],
            "output_tokens": self._usage[1],
            "cache_hit_tokens": self._usage[2],
            "input_cost": round(self._cost[0], 4),
            "output_cost": round(self._cost[1], 4),
            "cache_hit_cost": round(self._cost[2], 4),
            "total_cost": round(sum(self._cost), 4),
            "per_agent": {
                name: {
                    "calls": data["calls"],
                    "input_tokens": data["usage"][0],
                    "output_tokens": data["usage"][1],
                    "cache_hit_tokens": data["usage"][2],
                    "input_cost": round(data["cost"][0], 4),
                    "output_cost": round(data["cost"][1], 4),
                    "cache_hit_cost": round(data["cost"][2], 4),
                    "total_cost": round(sum(data["cost"]), 4),
                }
                for name, data in self._per_agent.items()
            },
        }

    async def _drive(self, inputs) -> SOPPhase:
        """消费一次 engine.reply_stream：实时上屏 + 按事件切角色写对话稿。

        Args:
            inputs: 启动输入或外部答复事件。

        Returns:
            推进后的运行阶段。
        """
        if self.dialogue is not None and isinstance(inputs, Msg) and inputs.role == "user":
            self.dialogue.write_user(
                role="sop",
                content=inputs.get_text_content() or "",
                scope=self._scope,
            )
        renderer = ConsoleRenderer(verbosity="debug")
        async for event in self.engine.reply_stream(inputs):
            self._observe(event)
            renderer.render(event)
        self._write_dialogue_summary()
        return self.engine.phase

    def _observe(self, event) -> None:
        """按事件类型切换阶段标识，并累计用量与费用。"""
        kind = type(event).__name__
        if kind == "ReplyStartEvent":
            self._agent = str(getattr(event, "name", "") or "")
            if self.dialogue is not None:
                self.dialogue.begin_reply()
            return
        if kind == "CustomEvent":
            self._on_custom(event)
            return
        cost = None
        if kind == "ModelCallStartEvent":
            self._call_model = str(getattr(event, "model_name", "") or self.model)
        elif kind == "ModelCallEndEvent":
            cost = self._record_call(event)
        if self.dialogue is not None:
            self.dialogue.consume(event, role=self._agent or "-", scope=self._scope, cost=cost)

    def _on_custom(self, event) -> None:
        """处理 SOP 步骤起止事件：收尾上一段记录并换阶段标识。"""
        name = str(getattr(event, "name", ""))
        if name not in ("SOP_STEP_STARTED", "SOP_STEP_ENDED"):
            return
        value = getattr(event, "value", None) or {}
        tail = (
            f"第 {value.get('attempt', 1)} 次"
            if name == "SOP_STEP_STARTED"
            else str(value.get("phase", ""))
        )
        self._scope = f"{SCOPE_STANDALONE} · {value.get('step', '')} · {tail}"
        if name == "SOP_STEP_STARTED" and self.dialogue is not None:
            step = str(value.get("step", "") or "")
            attempt = value.get("attempt", 1)
            self.dialogue.write_user(
                role="sop",
                content=f"{step} · 第 {attempt} 次",
                scope=self._scope,
            )

    def _record_call(self, event) -> float:
        """记一次模型调用的用量与费用（按该次调用的时刻与模型名分别计费）。"""
        input_tokens = int(getattr(event, "input_tokens", 0) or 0)
        output_tokens = int(getattr(event, "output_tokens", 0) or 0)
        hit_tokens = int(getattr(event, "cache_input_tokens", 0) or 0)
        tokens = (input_tokens, output_tokens, hit_tokens)
        part = self._call_cost(input_tokens, output_tokens, hit_tokens, event)
        bucket = self._per_agent.setdefault(
            self._agent or "-",
            {"calls": 0, "usage": [0, 0, 0], "cost": [0.0, 0.0, 0.0]},
        )
        self._calls += 1
        bucket["calls"] += 1
        for index in range(3):
            self._usage[index] += tokens[index]
            self._cost[index] += part[index]
            bucket["usage"][index] += tokens[index]
            bucket["cost"][index] += part[index]
        return round(sum(part), 4)

    def _write_dialogue_summary(self) -> None:
        """运行未挂起时，把用量、费用与墙钟耗时写入对话稿汇总块。"""
        if self.dialogue is None or self.engine.phase is SOPPhase.AWAITING:
            return
        self.dialogue.finish()
        report = self.cost_report()
        self.dialogue.write_summary(
            calls=report["calls"],
            tokens={
                "input": report["input_tokens"],
                "output": report["output_tokens"],
                "cache_hit": report["cache_hit_tokens"],
            },
            cost=report["total_cost"],
            duration_sec=round(time.monotonic() - self._started, 2),
            role="sop",
            scope="运行汇总",
        )

    def _call_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        hit_tokens: int,
        event,
    ) -> tuple[float, float, float]:
        """算这一次模型调用的费用。

        Args:
            input_tokens: 本次输入 token。
            output_tokens: 本次输出 token。
            hit_tokens: 本次缓存命中 token。
            event: 本次调用的结束事件（取 created_at 作为计费时刻）。

        Returns:
            (输入费用, 输出费用, 缓存命中费用)；无计费器时全为 0.0。
        """
        if self._billing is None:
            return 0.0, 0.0, 0.0
        return self._billing.cost(
            self._call_model,
            input_tokens,
            output_tokens,
            hit_tokens,
            _moment(getattr(event, "created_at", "")),
        )
