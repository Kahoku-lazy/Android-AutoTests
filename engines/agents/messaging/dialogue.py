"""对话稿：把一次运行的助手 / 工具 / 用户 / 上下文按块追加成 JSONL。

落在 `logs/agent_logs/<run-id>.jsonl`，一行一块。助手块在该次模型调用结束时写出，
并带上调用方传入的费用。写入失败只记 warning，不打断模型执行。
"""

from __future__ import annotations

import json
import logging
import re
import threading

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .messages import sanitize_tool_output_text

logger = logging.getLogger(__name__)

_SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_DIR = "logs/agent_logs"
KIND_ASSISTANT = "助手"
KIND_TOOL = "工具"
KIND_USER = "用户"
KIND_CONTEXT = "上下文"
KIND_SUMMARY = "汇总"
_CONTEXT_TAGS = re.compile(
    r"<(tool-instructions|system-reminder)>(.*?)</\1>",
    re.DOTALL,
)


def _run_stamp() -> str:
    """运行标识里的北京时间（YYYYMMDD-HHMMSS）。"""
    return datetime.now(_SHANGHAI).strftime("%Y%m%d-%H%M%S")


def _stamp() -> str:
    """当前北京时间，毫秒精度。"""
    return datetime.now(_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _parse_moment(stamp: object) -> datetime | None:
    """解析事件上的时刻；空或无法解析时返回 None。"""
    text = str(stamp or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _safe_run_id(run_id: str) -> str:
    """去掉路径分隔符，避免 run-id 逃出目录。"""
    cleaned = re.sub(r"[^\w.\-]+", "_", str(run_id or "").strip()).strip("._")
    return cleaned or f"sop-{_run_stamp()}"


def _split_context(text: str) -> tuple[str, list[str]]:
    """从返回文本里抽出工具说明和系统提醒，剩下的留给工具块。"""
    found: list[str] = []

    def _take(match: re.Match[str]) -> str:
        inner = match.group(2).strip()
        if inner:
            found.append(inner)
        return ""

    cleaned = _CONTEXT_TAGS.sub(_take, text or "")
    return cleaned.strip(), found


def _round_cost(cost: float) -> float:
    """费用保留小数点后 4 位。"""
    return round(float(cost or 0.0), 4)


def _round_seconds(seconds: float | None) -> float | None:
    """耗时保留小数点后 2 位；没有时刻时保持 null。"""
    if seconds is None:
        return None
    return round(max(float(seconds), 0.0), 2)


def _seconds_between(start: datetime, end: datetime) -> float:
    """两个时刻的秒差。一边带时区时都换算到北京时间。"""
    if start.tzinfo is not None or end.tzinfo is not None:
        if start.tzinfo is None:
            start = start.replace(tzinfo=_SHANGHAI)
        if end.tzinfo is None:
            end = end.replace(tzinfo=_SHANGHAI)
        start = start.astimezone(_SHANGHAI)
        end = end.astimezone(_SHANGHAI)
    return (end - start).total_seconds()


class DialogueLog:
    """一次运行一份 JSONL：组块、追加写、自动建目录。"""

    def __init__(
        self,
        directory: str = DEFAULT_DIR,
        *,
        run_id: str = "",
        model: str = "",
        enabled: bool = True,
    ) -> None:
        self.directory = Path(str(directory or DEFAULT_DIR))
        self.run_id = _safe_run_id(run_id or f"sop-{_run_stamp()}")
        self.path = self.directory / f"{self.run_id}.jsonl"
        self.model = str(model or "")
        self.enabled = bool(enabled)
        self._lock = threading.Lock()
        self._prepared = False
        self._role = "-"
        self._scope = ""
        self._call_model = self.model
        self._saw_start = False
        self._call_started: datetime | None = None
        self._call_started_local: datetime | None = None
        self._assistant_parts: list[str] = []
        self._thinking_parts: dict[str, list[str]] = {}
        self._text_parts: dict[str, list[str]] = {}
        self._call_names: dict[str, str] = {}
        self._call_parts: dict[str, list[str]] = {}
        self._pending: dict[str, dict] = {}
        self._result_parts: dict[str, list[str]] = {}

    def write_user(self, *, role: str, content: str, scope: str = "") -> None:
        """写一块用户记录。"""
        self._append(self._base(KIND_USER, role, scope, content=str(content or "")))

    def write_context(self, *, role: str, content: str, scope: str = "") -> None:
        """写一块上下文记录。"""
        self._append(self._base(KIND_CONTEXT, role, scope, content=str(content or "")))

    def write_assistant(
        self,
        *,
        role: str,
        content: str,
        model: str,
        tokens: dict,
        cost: float,
        duration_sec: float | None,
        scope: str = "",
    ) -> None:
        """写一块助手记录，附带模型、用量、费用与耗时。"""
        self._append(
            self._base(
                KIND_ASSISTANT,
                role,
                scope,
                content=str(content or ""),
                model=str(model or "-"),
                tokens=self._tokens(tokens),
                cost=_round_cost(cost),
                duration_sec=_round_seconds(duration_sec),
            )
        )

    def write_tool(
        self,
        *,
        role: str,
        name: str,
        tool_input: object,
        state: str,
        output: str,
        scope: str = "",
    ) -> None:
        """写一块工具记录（入参与返回已合成）。"""
        self._append(
            self._base(
                KIND_TOOL,
                role,
                scope,
                name=str(name or "未知工具"),
                input=tool_input if tool_input is not None else {},
                state=str(state or "-"),
                output=str(output or ""),
            )
        )

    def write_summary(
        self,
        *,
        calls: int,
        tokens: dict,
        cost: float,
        duration_sec: float | None,
        role: str = "sop",
        scope: str = "",
    ) -> None:
        """写运行结束时的汇总块。"""
        self._append(
            self._base(
                KIND_SUMMARY,
                role,
                scope,
                calls=int(calls or 0),
                tokens=self._tokens(tokens),
                cost=_round_cost(cost),
                duration_sec=_round_seconds(duration_sec),
            )
        )

    def consume(
        self,
        event: object,
        *,
        role: str,
        scope: str = "",
        cost: float | None = None,
    ) -> None:
        """消费一个事件。模型调用结束时写出助手块；费用由调用方传入。"""
        self._role = str(role or "-")
        self._scope = str(scope or "")
        name = type(event).__name__
        handler = getattr(self, f"_on_{name}", None)
        if handler is None:
            return
        try:
            handler(event, cost)
        except Exception:  # noqa: BLE001 - 组块失败不得打断模型执行
            logger.warning("对话稿组块失败：%s", name, exc_info=True)

    def begin_reply(self) -> None:
        """新一轮回复开始：收尾上一轮未返回的工具，并清掉未结束的助手缓冲。"""
        self.finish()
        self._assistant_parts.clear()
        self._thinking_parts.clear()
        self._text_parts.clear()
        self._saw_start = False
        self._call_started = None
        self._call_started_local = None

    def finish(self) -> None:
        """把还没收到返回的工具调用写成状态 `-`。"""
        for call_id in list(self._pending):
            pending = self._pending.pop(call_id)
            self._call_names.pop(call_id, None)
            output = "".join(self._result_parts.pop(call_id, []))
            self._emit_tool(pending, state="-", output=output)
        for call_id, name in list(self._call_names.items()):
            raw = "".join(self._call_parts.pop(call_id, [])).strip()
            output = "".join(self._result_parts.pop(call_id, []))
            self._emit_tool(
                {
                    "role": self._role,
                    "scope": self._scope,
                    "name": name or "未知工具",
                    "input": self._parse_input(raw),
                },
                state="-",
                output=output,
            )
        self._call_names.clear()
        self._call_parts.clear()
        self._result_parts.clear()

    # ── 模型调用与文本 ──

    def _on_ModelCallStartEvent(self, event, cost: float | None) -> None:
        del cost
        self._saw_start = True
        self._call_started = _parse_moment(getattr(event, "created_at", ""))
        self._call_started_local = datetime.now(_SHANGHAI)
        self._call_model = str(getattr(event, "model_name", "") or self.model or "-")
        self._assistant_parts.clear()

    def _on_ModelCallEndEvent(self, event, cost: float | None) -> None:
        self._flush_text_buffers()
        content = "\n".join(part for part in self._assistant_parts if part).strip()
        self._assistant_parts.clear()
        self.write_assistant(
            role=self._role,
            content=content,
            model=self._call_model or self.model or "-",
            tokens={
                "input": int(getattr(event, "input_tokens", 0) or 0),
                "output": int(getattr(event, "output_tokens", 0) or 0),
                "cache_hit": int(getattr(event, "cache_input_tokens", 0) or 0),
            },
            cost=0.0 if cost is None else cost,
            duration_sec=self._duration(getattr(event, "created_at", "")),
            scope=self._scope,
        )
        self._saw_start = False
        self._call_started = None
        self._call_started_local = None

    def _on_ThinkingBlockDeltaEvent(self, event, cost: float | None) -> None:
        del cost
        self._thinking_parts.setdefault(str(event.block_id), []).append(str(event.delta or ""))

    def _on_ThinkingBlockEndEvent(self, event, cost: float | None) -> None:
        del cost
        parts = self._thinking_parts.pop(str(event.block_id), [])
        text = "".join(parts).strip()
        if text:
            self._assistant_parts.append(text)

    def _on_TextBlockDeltaEvent(self, event, cost: float | None) -> None:
        del cost
        self._text_parts.setdefault(str(event.block_id), []).append(str(event.delta or ""))

    def _on_TextBlockEndEvent(self, event, cost: float | None) -> None:
        del cost
        parts = self._text_parts.pop(str(event.block_id), [])
        text = "".join(parts).strip() or str(getattr(event, "text", "") or "").strip()
        if text:
            self._assistant_parts.append(text)

    def _duration(self, end_stamp: object) -> float | None:
        """有开始时刻才计算耗时；否则为 null。"""
        if not self._saw_start or self._call_started_local is None:
            return None
        end = _parse_moment(end_stamp)
        if self._call_started is not None and end is not None:
            return _seconds_between(self._call_started, end)
        return _seconds_between(self._call_started_local, datetime.now(_SHANGHAI))

    def _flush_text_buffers(self) -> None:
        """调用结束时，把只收到增量、没收到结束事件的文本补进助手正文。"""
        for block_id, parts in list(self._thinking_parts.items()):
            self._thinking_parts.pop(block_id, None)
            text = "".join(parts).strip()
            if text:
                self._assistant_parts.append(text)
        for block_id, parts in list(self._text_parts.items()):
            self._text_parts.pop(block_id, None)
            text = "".join(parts).strip()
            if text:
                self._assistant_parts.append(text)

    # ── 工具 ──

    def _on_ToolCallStartEvent(self, event, cost: float | None) -> None:
        del cost
        self._call_names[str(event.tool_call_id)] = str(event.tool_call_name or "")

    def _on_ToolCallDeltaEvent(self, event, cost: float | None) -> None:
        del cost
        self._call_parts.setdefault(str(event.tool_call_id), []).append(str(event.delta or ""))

    def _on_ToolCallEndEvent(self, event, cost: float | None) -> None:
        del cost
        call_id = str(event.tool_call_id)
        raw = "".join(self._call_parts.pop(call_id, [])).strip()
        self._pending[call_id] = {
            "role": self._role,
            "scope": self._scope,
            "name": self._call_names.get(call_id) or "未知工具",
            "input": self._parse_input(raw),
            "output": "",
        }

    def _on_ToolResultTextDeltaEvent(self, event, cost: float | None) -> None:
        del cost
        self._result_parts.setdefault(str(event.tool_call_id), []).append(str(event.delta or ""))

    def _on_ToolResultDataDeltaEvent(self, event, cost: float | None) -> None:
        """图片二进制不入文件。"""
        del event, cost

    def _on_ToolResultEndEvent(self, event, cost: float | None) -> None:
        del cost
        call_id = str(event.tool_call_id)
        name = self._call_names.pop(call_id, "") or "未知工具"
        pending = self._pending.pop(call_id, None)
        if pending is None:
            raw = "".join(self._call_parts.pop(call_id, [])).strip()
            pending = {
                "role": self._role,
                "scope": self._scope,
                "name": name,
                "input": self._parse_input(raw),
            }
        output = "".join(self._result_parts.pop(call_id, []))
        self._emit_tool(pending, state=str(getattr(event, "state", "") or "-"), output=output)

    def _emit_tool(self, pending: dict, *, state: str, output: str) -> None:
        cleaned = sanitize_tool_output_text(output) if output else ""
        body, contexts = _split_context(cleaned)
        role = str(pending.get("role") or self._role or "-")
        scope = str(pending.get("scope") or "")
        records = [
            self._base(
                KIND_TOOL,
                role,
                scope,
                name=str(pending.get("name") or "未知工具"),
                input=pending.get("input") if pending.get("input") is not None else {},
                state=str(state or "-"),
                output=body,
            )
        ]
        records.extend(self._base(KIND_CONTEXT, role, scope, content=piece) for piece in contexts)
        self._append_many(records)

    @staticmethod
    def _parse_input(raw: str) -> object:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    # ── 落盘 ──

    def _base(self, kind: str, role: str, scope: str, **fields: object) -> dict:
        record = {
            "kind": kind,
            "ts": _stamp(),
            "role": str(role or "-"),
            "scope": str(scope or ""),
        }
        record.update(fields)
        return record

    @staticmethod
    def _tokens(tokens: dict | None) -> dict:
        source = tokens or {}
        return {
            "input": int(source.get("input", 0) or 0),
            "output": int(source.get("output", 0) or 0),
            "cache_hit": int(source.get("cache_hit", 0) or 0),
        }

    def _prepare(self) -> None:
        """写入前建目录与文件。"""
        if self._prepared:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
        self._prepared = True
        logger.info("对话稿已创建：%s", self.path)

    def _append(self, record: dict) -> None:
        self._append_many([record])

    def _append_many(self, records: list[dict]) -> None:
        if not self.enabled or not records:
            return
        payload = "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in records)
        try:
            with self._lock:
                self._prepare()
                with open(self.path, "a", encoding="utf-8") as handle:
                    handle.write(payload + "\n")
                    handle.flush()
        except Exception:  # noqa: BLE001 - 对话稿写入失败不得打断模型执行
            logger.warning("对话稿写入失败：%s", self.path)
