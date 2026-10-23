"""把结构化事件批量写入任务事件表、缩略图和小时用量。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from backend.apps.task_list import api, media_storage
from engines.agents.event_sink import current_run

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_BATCH = 50


class TaskEventSink:
    """平台侧接收方。没有 task_id 时丢弃，避免本地调试写库。"""

    def __init__(self) -> None:
        self._rows: list[dict] = []
        self._pending: dict | None = None
        self._seq = 0
        self._task_id = 0
        self._agent_id = 0
        self._ready = False

    def emit(self, record, image_b64: str = "") -> None:
        """收一条记录；连续增量先攒着，类型或步骤变化时落行。"""
        ctx = current_run()
        if not ctx.task_id:
            return
        self._ensure_task(ctx.task_id, ctx.agent_id)
        if self._can_fold(record, image_b64, ctx):
            self._fold(record)
            return
        self._close_pending()
        if record.is_delta and not image_b64:
            self._pending = _row(record, "", ctx, 0)
            return
        self._seq += 1
        self._append_row(_row(record, image_b64, ctx, self._seq))

    def flush(self) -> None:
        """把已结束的行写入数据库；未结束的增量段留在内存。"""
        if not self._rows or not self._task_id:
            self._rows.clear()
            return
        rows = list(self._rows)
        api.insert_task_events(self._task_id, rows)
        self._rows.clear()
        for row in rows:
            _add_usage(row, self._agent_id)

    def close(self) -> None:
        """收尾未结束的增量段，刷尾并回写任务费用。"""
        self._close_pending()
        self.flush()
        if self._task_id:
            api.rollup_task_cost(self._task_id)

    def _can_fold(self, record, image_b64: str, ctx) -> bool:
        """这条记录能否并入当前未结束的增量段。"""
        pending = self._pending
        if pending is None or not record.is_delta or image_b64:
            return False
        return (
            pending["event_type"] == record.event_type[:48]
            and pending["step_seq"] == ctx.step_seq
            and pending["attempt"] == ctx.attempt
        )

    def _fold(self, record) -> None:
        """累加当前增量段的条数与耗时。"""
        pending = self._pending
        if pending is None:
            return
        pending["delta_count"] += 1
        pending["payload"] = {"delta_count": pending["delta_count"]}
        ended = _naive(record.ended_at)
        first = pending["ended_at"]
        if ended is not None and first is not None:
            pending["duration_ms"] = max(int((ended - first).total_seconds() * 1000), 0)

    def _close_pending(self) -> None:
        """把未结束的增量段落成一行，序号在此时分配。"""
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        self._seq += 1
        pending["seq"] = self._seq
        self._append_row(pending)

    def _append_row(self, row: dict) -> None:
        """收下一行；满一批就落库。"""
        self._rows.append(row)
        if len(self._rows) >= _BATCH:
            self.flush()

    def _ensure_task(self, task_id: int, agent_id: int) -> None:
        if self._ready:
            return
        from backend.apps.task_list.models import TaskEvent

        last = (
            TaskEvent.objects.filter(task_id=task_id)
            .order_by("-seq")
            .values_list("seq", flat=True)
            .first()
        )
        self._seq = int(last or 0)
        self._task_id = task_id
        self._agent_id = int(agent_id or 0)
        self._ready = True


def _row(record, image_b64: str, ctx, seq: int) -> dict:
    """把一条记录收成事件表字段。"""
    payload = dict(record.payload or {})
    incoming = int(payload.get("input_tokens") or 0)
    outgoing = int(payload.get("output_tokens") or 0)
    hit = int(payload.get("cache_input_tokens") or 0)
    called_at = _naive(record.ended_at if record.event_type == "ModelCallEndEvent" else None)
    peak = None
    snapshot = _jsonable(record.pricing_snapshot) if record.pricing_snapshot else None
    if isinstance(snapshot, dict) and "peak" in snapshot:
        peak = bool(snapshot["peak"])
    media_id = _media_id(record, image_b64, ctx, seq) if image_b64 else None
    return {
        "case_title": (ctx.case_title or "")[:255],
        "step_seq": ctx.step_seq,
        "attempt": ctx.attempt,
        "seq": seq,
        "event_type": record.event_type[:48],
        "phase": record.phase[:8],
        "block_type": record.block_type[:16],
        "is_delta": bool(record.is_delta),
        "delta_count": 1,
        "role_name": (record.role_name or "")[:64],
        "role_kind": (record.role_kind or "")[:16],
        "model": (record.model or "")[:64],
        "status": str(payload.get("status") or "")[:16],
        "payload": payload,
        "started_at": _naive(record.started_at),
        "ended_at": _naive(record.ended_at),
        "duration_ms": int(record.duration_ms or 0),
        "called_at": called_at,
        "called_date": called_at.date() if called_at else None,
        "called_hour": called_at.hour if called_at else None,
        "is_peak": peak,
        "input_tokens": incoming,
        "cache_input_tokens": hit,
        "cache_miss_tokens": max(incoming - hit, 0),
        "output_tokens": outgoing,
        "cache_creation_tokens": int(payload.get("cache_creation_tokens") or 0),
        "cost_input": record.cost_input,
        "cost_cache": record.cost_cache,
        "cost_output": record.cost_output,
        "cost_total": record.cost_input + record.cost_cache + record.cost_output,
        "pricing_snapshot": snapshot,
        "media_id": media_id,
    }


def _add_usage(row: dict, agent_id: int) -> None:
    """事件写入成功后再累加小时用量，避免插入失败时重复计费。"""
    if row["event_type"] != "ModelCallEndEvent" or row["called_at"] is None:
        return
    called_at = row["called_at"]
    api.add_usage_hourly(
        {
            "stat_date": called_at.date(),
            "stat_hour": called_at.hour,
            "model": row["model"],
            "role_name": row["role_name"],
            "role_kind": row["role_kind"],
            "agent_id": agent_id,
            "is_peak": bool(row["is_peak"]),
        },
        {
            "input_tokens": row["input_tokens"],
            "cache_input_tokens": row["cache_input_tokens"],
            "cache_miss_tokens": row["cache_miss_tokens"],
            "output_tokens": row["output_tokens"],
            "cost_input": row["cost_input"],
            "cost_cache": row["cost_cache"],
            "cost_output": row["cost_output"],
            "cost_total": row["cost_total"],
        },
    )


def _media_id(record, image_b64: str, ctx, seq: int) -> int | None:
    """压成 720px WebP 后落盘并写元数据。坏图返回 None。"""
    packed = media_storage.encode(image_b64)
    if packed is None:
        return None
    return api.store_task_media(
        ctx.task_id,
        packed,
        {
            "event_seq": seq,
            "role_name": (record.role_name or "")[:64],
            "step_seq": ctx.step_seq,
            "attempt": ctx.attempt,
        },
    )


def _naive(moment: datetime | None) -> datetime | None:
    """带时区的时刻先换到北京时间，再存成无时区时间。"""
    if moment is None:
        return None
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(_SHANGHAI).replace(tzinfo=None)


def _jsonable(value):
    """快照里的 Decimal 写成 8 位小数字符串。"""
    if isinstance(value, Decimal):
        return f"{value:.8f}"
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
