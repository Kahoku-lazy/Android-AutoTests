"""
文件名: ➡️ record.py 🏁
路径: ➡️ engines/ae_harness/event/record.py 🏁
模块功能：➡️ 订阅 reply_stream 事件，产出一轮运行的结构化记录 🏁
Python 调试：➡️ python -m engines.ae_harness.event.record 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. StepRecord / RunRecord: 一轮运行里「一步」与「整轮」的数据结构。
2. AgentEventRecorder: 喂事件进来，按轮次落 JSONL，最后产出 RunRecord。
3. 本模块不认识任何具体工具，也不调用 Agent 的回复接口。
🏁
关联模块：➡️
1. agentscope.event: 事件对象来源，只按类型名与通用字段读取。
2. engines.ae_harness.event.render: 消费 RunRecord 生成页面（调用方串联）。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor。
🏁
"""

from __future__ import annotations

import json
import re
import time

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from .usage import TokenUsage, summarize

__all__ = ["AgentEventRecorder", "RunRecord", "StepRecord"]

# 单个文本字段的落盘上限。
_MAX_TEXT = 4000

# 阶段标记的默认正则；别的角色可以传自己的。
_DEFAULT_PHASE_PATTERN = r"###\s*目标[：:]\s*([^\s。，,；;]{1,24})"


def _shrink(value: object, limit: int | None = _MAX_TEXT) -> object:
    """
    截断过长的文本，非字符串原样返回。

    Args:
        value: 待处理的值。
        limit: 保留的最大字符数；None 表示不截断。

    Returns:
        截断后的值。
    """
    if limit is None:
        return value
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"...(共 {len(value)} 字符)"
    return value


def _jsonable(value: object) -> object:
    """
    把元数据转成可 JSON 序列化的形态。

    Args:
        value: 原始值。

    Returns:
        可序列化的值；不可序列化时退回截断后的 repr。
    """
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)[:500]


@dataclass
class StepRecord:
    """
    一次工具调用的记录。

    Attributes:
        index: 在本轮里的序号，从 1 开始。
        tool: 工具名。
        phase: 所属阶段；没有阶段标记时为空串。
        t_ms: 相对本轮开始的毫秒数。
        state: 工具结果状态。
        input: 工具入参原文。
        output: 工具结果原文。
        note: 该步之前最近一段文本或思考。
        images: 本步返回的图片 base64 列表，只在内存里。
        round_index: 属于第几轮模型调用，从 1 开始。
        span_ms: 工具执行耗时（入参确定到结果返回）。
        agent_role: 发起这次调用的角色名；推断不出时为空串。
        sop_step: 所属 SOP 步骤名；不在流程里跑时为空串。
    """

    index: int
    tool: str
    phase: str
    t_ms: float
    state: str
    input: str
    output: str
    note: str
    images: list[str] = field(default_factory=list)
    round_index: int = 0
    span_ms: float = 0.0
    agent_role: str = ""
    sop_step: str = ""


@dataclass
class RunRecord:
    """
    一轮运行的完整记录。

    Attributes:
        task: 本轮任务描述。
        cost_s: 本轮耗时秒数。
        steps: 工具调用记录。
        events: 全部事件，按到达顺序。
        summary: 汇总统计。
        final_text: 最终回复正文。
        directory: 本轮产物目录。
        log_path: JSONL 文件路径。
        html_path: 报告文件路径。
        schemas: 工具名到 schema 的映射，供详情面板展示。
        spans: 时间轴数据，模型与工具各一段。
        sop_steps: SOP 步骤定义（subject + description），供报告展示验收事项。
        usages: 逐次模型调用的用量记录，一次调用一条。
        api_key_env: 本次运行的密钥环境变量名；未传标签时为空串。
        observations: 观测中间件采到的记录（已落盘的行），顺序与发生顺序一致。
    """

    task: str
    cost_s: float
    steps: list[StepRecord]
    events: list[dict]
    summary: dict
    final_text: str
    directory: Path
    log_path: Path
    html_path: Path
    schemas: dict[str, dict] = field(default_factory=dict)
    spans: list[dict] = field(default_factory=list)
    sop_steps: list[dict] = field(default_factory=list)
    usages: list[TokenUsage] = field(default_factory=list)
    api_key_env: str = ""
    observations: list[dict] = field(default_factory=list)


class AgentEventRecorder:
    """
    把 reply_stream 的事件记成一轮结构化数据，并按轮次落盘。

    一个实例只管一轮：begin 建新目录与文件，finish 收尾。多轮请新建实例。
    """

    def __init__(
        self,
        out_dir: Path,
        role: str,
        *,
        phase_pattern: str = _DEFAULT_PHASE_PATTERN,
        api_key_env: str = "",
        role_api_keys: dict[str, str] | None = None,
        observations: list | None = None,
        full: bool = True,
    ) -> None:
        """
        记录输出位置、阶段识别规则、角色到密钥的绑定与观测来源。

        Args:
            out_dir: 产物根目录；本轮会在其下新建时间戳目录。
            role: 角色名，写进产物文件名。
            phase_pattern: 识别阶段标记的正则，第一个分组是阶段名。
            api_key_env: 兜底标签；某个角色没登记绑定时用它，不传则为空串。
            role_api_keys: 角色名（agent 名）到密钥环境变量名的绑定。密钥绑在角色上，
                每次调用按 `reply_id` 反查发起它的角色再取标签。
            observations: 观测中间件的记录队列；记录器按到达顺序取出并落盘。
                传进来的是同一个列表对象，取出即从队列移除，避免重复写。
            full: 全量模式，默认开启。开启时补齐框架提供的公共字段
                （`created_at` / `event_id` / `metadata` / `session_id` / `source`），
                并取消思考与工具输出的长度截断；仍按块级折叠，不逐条落 delta。
        """
        self.out_dir = out_dir
        self.role = role
        self.phase_re = re.compile(phase_pattern)
        self._api_key_env = str(api_key_env or "")
        self._role_api_keys = dict(role_api_keys or {})
        self._observations = observations if observations is not None else []
        self._observed: list[dict] = []
        self._full = bool(full)
        self.directory = out_dir
        self.log_path = out_dir / "run.jsonl"
        self.html_path = out_dir / "report.html"
        self._handle = None
        self._begin = 0.0
        self._buf: dict[str, str] = {}
        self._names: dict[str, str] = {}
        self._inputs: dict[str, str] = {}
        self._images: dict[str, dict[str, str]] = {}
        self._steps: list[StepRecord] = []
        self._events: list[dict] = []
        self._spans: list[dict] = []
        self._calls: list[str] = []
        self._failed = 0
        self._screens = 0
        self._final = ""
        self._note = ""
        self._phase = ""
        self._task = ""
        self._schemas: dict[str, dict] = {}
        self._round = 0
        self._model_start = 0.0
        self._model_name = "model"
        self._tool_start: dict[str, float] = {}
        self._tokens = {"input": 0, "output": 0, "cache_hit": 0, "cache_creation": 0}
        self._sop_step = ""
        self._reply_in_step = 0
        self._reply_role: dict[str, str] = {}
        self._sop_steps: list[dict] = []
        self._usages: list[TokenUsage] = []
        self._wall_start: datetime | None = None
        self._reply_label: dict[str, str] = {}

    def _make_paths(self) -> None:
        """按当前时间建本轮目录，同名时追加序号。"""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.out_dir / stamp
        suffix = 1
        while target.exists():
            suffix += 1
            target = self.out_dir / f"{stamp}_{suffix}"
        target.mkdir(parents=True)
        self.directory = target
        self.log_path = target / f"{target.name}_{self.role}.jsonl"
        self.html_path = target / f"{target.name}_{self.role}.html"

    def _write(self, row: dict) -> None:
        """
        追加一行事件，同时在内存留一份。

        Args:
            row: 要写入的记录。
        """
        self._events.append(row)
        if self._handle is None:
            return
        self._handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._handle.flush()

    def _now(self) -> float:
        """
        本轮已经过的毫秒数。

        Returns:
            毫秒，保留一位小数。
        """
        return round((time.perf_counter() - self._begin) * 1000, 1)

    def _absolute(self, offset_ms: float) -> str:
        """
        把相对本轮开始的偏移换成绝对时刻。

        本轮起点未知时不伪造绝对时间，返回空串。

        Args:
            offset_ms: 相对本轮开始的毫秒偏移。

        Returns:
            `YYYY-MM-DD_HH-MM-SS.mmm` 形式的绝对时刻；无锚点时为空串。
        """
        if self._wall_start is None:
            return ""
        moment = self._wall_start + timedelta(milliseconds=offset_ms)
        return moment.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]

    def _usage_row(self, event: object, end_ms: float, label: str) -> TokenUsage:
        """
        把一条模型调用结束事件收成用量记录。

        Args:
            event: 模型调用结束事件。
            end_ms: 本次调用的结束偏移（毫秒），由调用方算好避免重复取时间。
            label: 本次调用的密钥环境变量名，由发起它的角色决定。

        Returns:
            一条用量记录；角色未登记绑定时标签为兜底值。
        """
        return TokenUsage(
            api_key_env=label,
            round_index=self._round,
            started_at=self._absolute(self._model_start),
            ended_at=self._absolute(end_ms),
            input_tokens=int(getattr(event, "input_tokens", 0) or 0),
            output_tokens=int(getattr(event, "output_tokens", 0) or 0),
            cache_input_tokens=int(getattr(event, "cache_input_tokens", 0) or 0),
            cache_creation_input_tokens=int(getattr(event, "cache_creation_input_tokens", 0) or 0),
        )

    def _new_row(self, kind: str, event: object) -> dict:
        """
        建一条事件行；全量模式下补框架提供的公共字段。

        取不到的字段不写，避免产物里出现成片的空串。

        Args:
            kind: 事件类型名。
            event: 原始事件对象。

        Returns:
            待各分支继续填充的事件行。
        """
        row: dict = {"event": kind, "t_ms": self._now()}
        if not self._full:
            return row
        for key, attribute in (("created_at", "created_at"), ("event_id", "id")):
            value = getattr(event, attribute, None)
            if value:
                row[key] = str(value)
        metadata = getattr(event, "metadata", None)
        if metadata:
            row["metadata"] = _jsonable(metadata)
        return row

    def _drain_observations(self) -> None:
        """
        把观测中间件已采到的记录写进事件流。

        观测记录由中间件在 hook 里产生，先进入调用方传入的队列；
        这里按到达顺序取出并落盘，取出即从队列移除，避免重复写。

        Returns:
            无。
        """
        while self._observations:
            record = self._observations.pop(0)
            payload = record.as_dict() if hasattr(record, "as_dict") else dict(record)
            row = {"event": "observation", "t_ms": self._now(), **payload}
            self._write(row)
            self._observed.append(payload)

    def begin(
        self,
        task: str,
        schemas: dict[str, dict] | None = None,
        sop_steps: list[dict] | None = None,
    ) -> None:
        """
        开始新的一轮，建目录、开文件、重置缓冲。

        Args:
            task: 本轮任务描述。
            schemas: 工具名到 schema 的映射，供详情面板展示；不传则不展示。
            sop_steps: SOP 步骤定义（subject + description），供报告展示验收事项。
        """
        self._make_paths()
        self._handle = self.log_path.open("w", encoding="utf-8")
        self._begin = time.perf_counter()
        self._buf.clear()
        self._names.clear()
        self._inputs.clear()
        self._images.clear()
        self._steps = []
        self._events = []
        self._spans = []
        self._calls = []
        self._failed = 0
        self._screens = 0
        self._final = ""
        self._note = ""
        self._phase = ""
        self._task = task
        self._schemas = dict(schemas or {})
        self._sop_steps = list(sop_steps or [])
        self._round = 0
        self._model_start = 0.0
        self._model_name = "model"
        self._tool_start = {}
        self._tokens = {"input": 0, "output": 0, "cache_hit": 0, "cache_creation": 0}
        self._sop_step = ""
        self._reply_in_step = 0
        self._reply_role = {}
        self._usages = []
        self._observed = []
        # 本轮起始墙钟：用量记录的绝对时刻由它加相对偏移算出；没调用 begin 时为 None。
        self._wall_start = datetime.now()
        self._reply_label = {}
        self._write(
            {
                "event": "reply_start",
                "timestamp": self._wall_start.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3],
                "task": task,
            }
        )

    def on_event(self, event: object) -> None:
        """
        处理一个事件，按需落盘并在内存累积步骤。

        Args:
            event: agentscope 的事件对象。
        """
        self._drain_observations()
        kind = type(event).__name__
        row = self._new_row(kind, event)

        if kind == "ToolCallStartEvent":
            self._names[event.tool_call_id] = event.tool_call_name
            row["name"] = event.tool_call_name

        elif kind == "ToolCallDeltaEvent":
            key = f"call:{event.tool_call_id}"
            self._buf[key] = self._buf.get(key, "") + str(event.delta)
            return

        elif kind == "ToolCallEndEvent":
            row["name"] = self._names.get(event.tool_call_id, "")
            # 关联键与开关无关：调用与结果靠它配对，不能只靠顺序
            row["tool_call_id"] = str(event.tool_call_id)
            row["input"] = _shrink(
                self._buf.pop(f"call:{event.tool_call_id}", ""), None if self._full else _MAX_TEXT
            )
            self._inputs[event.tool_call_id] = row["input"]
            self._tool_start[event.tool_call_id] = self._now()
            if row["name"]:
                self._calls.append(row["name"])
                if "screenshot" in row["name"]:
                    self._screens += 1

        elif kind == "ToolResultStartEvent":
            row["name"] = event.tool_call_name

        elif kind == "ToolResultTextDeltaEvent":
            key = f"res:{event.tool_call_id}"
            self._buf[key] = self._buf.get(key, "") + str(event.delta)
            return

        elif kind == "ToolResultDataDeltaEvent":
            data = getattr(event, "data", "") or ""
            row["media_type"] = getattr(event, "media_type", None)
            row["base64_chars"] = len(data)
            call = getattr(event, "tool_call_id", "") or ""
            block = getattr(event, "block_id", "") or ""
            if call and block:
                bucket = self._images.setdefault(call, {})
                bucket[block] = bucket.get(block, "") + data

        elif kind == "ToolResultEndEvent":
            row["name"] = self._names.get(event.tool_call_id, "")
            row["tool_call_id"] = str(event.tool_call_id)
            row["state"] = event.state
            output = self._buf.pop(f"res:{event.tool_call_id}", "")
            row["output"] = _shrink(output, None if self._full else _MAX_TEXT)
            if isinstance(event.state, str) and event.state.lower() not in {"success", "ok"}:
                self._failed += 1
            images = list(self._images.pop(event.tool_call_id, {}).values())
            start = self._tool_start.pop(event.tool_call_id, None)
            span_ms = round(row["t_ms"] - start, 1) if start is not None else 0.0
            self._spans.append(
                {
                    "name": row["name"],
                    "kind": "tool",
                    "start_ms": start if start is not None else row["t_ms"],
                    "end_ms": row["t_ms"],
                    "round": self._round,
                    "step": len(self._steps) + 1,
                    "state": str(event.state),
                }
            )
            self._steps.append(
                StepRecord(
                    index=len(self._steps) + 1,
                    tool=row["name"],
                    phase=self._phase,
                    t_ms=row["t_ms"],
                    state=str(event.state),
                    input=self._inputs.pop(event.tool_call_id, ""),
                    output=str(row["output"]),
                    note=self._note,
                    images=images,
                    round_index=self._round,
                    span_ms=span_ms,
                    agent_role=self._reply_role.get(getattr(event, "reply_id", ""), ""),
                    sop_step=self._sop_step,
                )
            )

        elif kind == "ModelCallStartEvent":
            self._round += 1
            self._model_start = self._now()
            self._model_name = getattr(event, "model_name", "") or "model"
            row["model"] = event.model_name
            row["round"] = self._round

        elif kind == "ModelCallEndEvent":
            row["input_tokens"] = event.input_tokens
            row["output_tokens"] = event.output_tokens
            row["cache_input_tokens"] = getattr(event, "cache_input_tokens", 0)
            row["cache_creation_input_tokens"] = getattr(event, "cache_creation_input_tokens", 0)
            row["finished_reason"] = event.finished_reason
            # 密钥绑角色：按 reply_id 找出这次调用的角色绑了哪把密钥，并落进事件行
            label = self._reply_label.get(
                str(getattr(event, "reply_id", "") or ""), self._api_key_env
            )
            row["api_key_env"] = label
            self._tokens["input"] += event.input_tokens or 0
            self._tokens["output"] += event.output_tokens or 0
            self._tokens["cache_hit"] += getattr(event, "cache_input_tokens", 0) or 0
            self._tokens["cache_creation"] += getattr(event, "cache_creation_input_tokens", 0) or 0
            end_ms = self._now()
            # 一次调用一条：同一轮的多次调用各自成条，不合并
            self._usages.append(self._usage_row(event, end_ms, label))
            self._spans.append(
                {
                    "name": self._model_name,
                    "kind": "model",
                    "start_ms": self._model_start,
                    "end_ms": end_ms,
                    "round": self._round,
                    "step": 0,
                    "state": str(getattr(event, "finished_reason", "") or ""),
                }
            )

        elif kind == "ThinkingBlockDeltaEvent":
            key = f"think:{event.block_id}"
            self._buf[key] = self._buf.get(key, "") + str(event.delta)
            return

        elif kind == "ThinkingBlockEndEvent":
            row["block_id"] = str(event.block_id)
            thinking = self._buf.pop(f"think:{event.block_id}", "")
            row["thinking"] = _shrink(thinking, None if self._full else 600)
            if thinking:
                self._note = thinking

        elif kind == "TextBlockDeltaEvent":
            key = f"text:{event.block_id}"
            self._buf[key] = self._buf.get(key, "") + str(event.delta)
            return

        elif kind == "TextBlockEndEvent":
            row["block_id"] = str(event.block_id)
            text = self._buf.pop(f"text:{event.block_id}", "") or getattr(event, "text", "") or ""
            marker = self.phase_re.search(text)
            if marker:
                self._phase = marker.group(1).strip()
                self._write({"event": "phase", "t_ms": row["t_ms"], "phase": self._phase})
                remainder = self.phase_re.sub("", text, count=1).strip()
                if not remainder:
                    return
                row["text"] = _shrink(remainder, None if self._full else _MAX_TEXT)
                self._final = remainder
                self._note = remainder
                self._write(row)
                return
            row["text"] = _shrink(text, None if self._full else _MAX_TEXT)
            if text:
                self._final = text
                self._note = text

        elif kind == "HintBlockEvent":
            row["hint"] = _shrink(getattr(event, "hint", ""), None if self._full else 200)
            if self._full and getattr(event, "source", None):
                row["source"] = str(event.source)

        elif kind in {"TextBlockStartEvent", "ThinkingBlockStartEvent"}:
            return

        elif kind.startswith("DataBlock"):
            return

        elif kind == "CustomEvent":
            name = str(getattr(event, "name", ""))
            value = getattr(event, "value", None) or {}
            row["name"] = name
            row["value"] = value
            if name == "SOP_STEP_STARTED":
                # 进入新步骤：重置本步内的 reply 计数，后续按奇偶推断角色。
                self._sop_step = str(value.get("step", ""))
                self._reply_in_step = 0

        elif kind == "ReplyEndEvent":
            row["finished_reason"] = getattr(event, "finished_reason", None)
            row["error"] = getattr(event, "error", None)
            if self._full and getattr(event, "session_id", None):
                row["session_id"] = str(event.session_id)

        elif kind == "ReplyStartEvent":
            # 密钥绑在角色上：先按 agent 名登记这次回复该用哪把密钥，供模型调用按 reply_id 反查。
            reply_id = str(getattr(event, "reply_id", "") or "")
            agent_name = str(getattr(event, "name", "") or "")
            self._reply_label[reply_id] = self._role_api_keys.get(agent_name, self._api_key_env)

            # 只在 SOP 步骤内推断执行者 / 验收者：每步第一次 reply 是执行者，第二次是验收者。
            if not self._sop_step:
                return
            self._reply_in_step += 1
            role = "executor" if self._reply_in_step % 2 == 1 else "verifier"
            self._reply_role[event.reply_id] = role
            row["reply_id"] = event.reply_id
            row["agent_name"] = agent_name
            row["role"] = role
            if self._full and getattr(event, "session_id", None):
                row["session_id"] = str(event.session_id)

        self._write(row)

    def finish(self, cost_s: float) -> RunRecord:
        """
        收尾：写汇总、关文件、返回整轮记录。

        Args:
            cost_s: 本轮耗时秒数。

        Returns:
            本轮完整记录。
        """
        self._drain_observations()
        summary = {
            "event": "summary",
            "t_ms": self._now(),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3],
            "task": self._task,
            "cost_s": cost_s,
            "tool_calls": len(self._calls),
            "by_tool": {},
            "failed": self._failed,
            "screenshots": self._screens,
            "tokens": dict(self._tokens),
            # 密钥标签落到汇总行：事后审计不必再依赖内存对象
            "api_key_env": self._api_key_env,
            # 混跑时一把密钥一个名字都写下来，消费方不必再回到内存里算
            "by_api_key_env": summarize(self._usages).by_api_key_env,
        }
        for name in self._calls:
            summary["by_tool"][name] = summary["by_tool"].get(name, 0) + 1
        self._write(summary)
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        return RunRecord(
            task=self._task,
            cost_s=cost_s,
            steps=self._steps,
            events=self._events,
            summary=summary,
            final_text=self._final,
            directory=self.directory,
            log_path=self.log_path,
            html_path=self.html_path,
            schemas=self._schemas,
            spans=self._spans,
            sop_steps=self._sop_steps,
            usages=self._usages,
            api_key_env=self._api_key_env,
            observations=self._observed,
        )
