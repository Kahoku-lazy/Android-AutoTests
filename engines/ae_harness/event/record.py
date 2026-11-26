from __future__ import annotations

import json
import re
import time

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from .usage import TokenUsage, summarize

__all__ = ["AgentEventRecorder", "RunRecord", "StepRecord"]

_MAX_TEXT = 4000

_DEFAULT_PHASE_PATTERN = r"###\s*目标[：:]\s*([^\s。，,；;]{1,24})"


def _shrink(value: object, limit: int | None = _MAX_TEXT) -> object:
    if limit is None:
        return value
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"...(共 {len(value)} 字符)"
    return value


def _jsonable(value: object) -> object:
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)[:500]


@dataclass
class StepRecord:
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
    sop_attempt: int = 0


@dataclass
class RunRecord:
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
    def __init__(
        self,
        out_dir: Path,
        role: str,
        *,
        phase_pattern: str = _DEFAULT_PHASE_PATTERN,
        api_key_env: str = "",
        role_api_keys: dict[str, str] | None = None,
        role_models: dict[str, str] | None = None,
        sop_roles: dict[str, str] | None = None,
        observations: list | None = None,
        observation_sink: Callable[[object], None] | None = None,
        full: bool = True,
    ) -> None:
        self.out_dir = out_dir
        self.role = role
        self.phase_re = re.compile(phase_pattern)
        self._api_key_env = str(api_key_env or "")
        self._role_api_keys = dict(role_api_keys or {})
        self._role_models = dict(role_models or {})
        self._sop_roles = dict(sop_roles or {})
        self._observations = observations if observations is not None else []
        self._observation_sink = observation_sink
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
        self._sop_attempt = 0
        self._reply_in_step = 0
        self._reply_role: dict[str, str] = {}
        self._sop_steps: list[dict] = []
        self._usages: list[TokenUsage] = []
        self._wall_start: datetime | None = None
        self._reply_label: dict[str, str] = {}
        self._reply_model: dict[str, str] = {}

    def _make_paths(self) -> None:
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
        self._events.append(row)
        if self._handle is None:
            return
        self._handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._handle.flush()

    def _now(self) -> float:
        return round((time.perf_counter() - self._begin) * 1000, 1)

    def _absolute(self, offset_ms: float) -> str:
        if self._wall_start is None:
            return ""
        moment = self._wall_start + timedelta(milliseconds=offset_ms)
        return moment.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]

    def _usage_row(self, event: object, end_ms: float, label: str, model: str = "") -> TokenUsage:
        return TokenUsage(
            api_key_env=label,
            round_index=self._round,
            started_at=self._absolute(self._model_start),
            ended_at=self._absolute(end_ms),
            input_tokens=int(getattr(event, "input_tokens", 0) or 0),
            output_tokens=int(getattr(event, "output_tokens", 0) or 0),
            cache_input_tokens=int(getattr(event, "cache_input_tokens", 0) or 0),
            cache_creation_input_tokens=int(getattr(event, "cache_creation_input_tokens", 0) or 0),
            model=model,
        )

    def _new_row(self, kind: str, event: object) -> dict:
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
        while self._observations:
            record = self._observations.pop(0)
            payload = record.as_dict() if hasattr(record, "as_dict") else dict(record)
            row = {"event": "observation", "t_ms": self._now(), **payload}
            self._write(row)
            self._observed.append(payload)
            if self._observation_sink is not None:
                self._observation_sink(record)

    def begin(
        self,
        task: str,
        schemas: dict[str, dict] | None = None,
        sop_steps: list[dict] | None = None,
    ) -> None:
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
        self._sop_attempt = 0
        self._reply_in_step = 0
        self._reply_role = {}
        self._usages = []
        self._observed = []
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
                    sop_attempt=self._sop_attempt,
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
            reply_id = str(getattr(event, "reply_id", "") or "")
            label = self._reply_label.get(reply_id, self._api_key_env)
            row["api_key_env"] = label
            row["model"] = self._reply_model.get(reply_id, "")
            self._tokens["input"] += event.input_tokens or 0
            self._tokens["output"] += event.output_tokens or 0
            self._tokens["cache_hit"] += getattr(event, "cache_input_tokens", 0) or 0
            self._tokens["cache_creation"] += getattr(event, "cache_creation_input_tokens", 0) or 0
            end_ms = self._now()
            self._usages.append(
                self._usage_row(event, end_ms, label, self._reply_model.get(reply_id, ""))
            )
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
                self._sop_step = str(value.get("step", ""))
                self._sop_attempt = int(value.get("attempt", 0) or 0)
                self._reply_in_step = 0

        elif kind == "ReplyEndEvent":
            row["finished_reason"] = getattr(event, "finished_reason", None)
            row["error"] = getattr(event, "error", None)
            if self._full and getattr(event, "session_id", None):
                row["session_id"] = str(event.session_id)

        elif kind == "ReplyStartEvent":
            reply_id = str(getattr(event, "reply_id", "") or "")
            agent_name = str(getattr(event, "name", "") or "")
            self._reply_label[reply_id] = self._role_api_keys.get(agent_name, self._api_key_env)
            self._reply_model[reply_id] = self._role_models.get(agent_name, "")

            if not self._sop_step:
                return
            self._reply_in_step += 1
            role = self._sop_roles.get(agent_name)
            if role is None:
                role = "executor" if self._reply_in_step % 2 == 1 else "verifier"
            self._reply_role[event.reply_id] = role
            row["reply_id"] = event.reply_id
            row["agent_name"] = agent_name
            row["role"] = role
            if self._full and getattr(event, "session_id", None):
                row["session_id"] = str(event.session_id)

        self._write(row)

    def finish(self, cost_s: float) -> RunRecord:
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
            "api_key_env": self._api_key_env,
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
