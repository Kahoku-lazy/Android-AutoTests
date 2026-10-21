"""把结构化事件批量写入任务事件表、缩略图和小时用量。"""

from __future__ import annotations

import base64
import hashlib

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

from PIL import Image

from backend.apps.task_list import api
from engines.agents.event_sink import current_run

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_BATCH = 50


class TaskEventSink:
    """平台侧接收方。没有 task_id 时丢弃，避免本地调试写库。"""

    def __init__(self) -> None:
        self._rows: list[dict] = []
        self._seq = 0
        self._task_id = 0
        self._agent_id = 0
        self._ready = False

    def emit(self, record, image_b64: str = "") -> None:
        """收一条记录。满 50 条就落库。"""
        ctx = current_run()
        if not ctx.task_id:
            return
        self._ensure_task(ctx.task_id, ctx.agent_id)
        self._seq += 1
        self._rows.append(_row(record, image_b64, ctx, self._seq))
        if len(self._rows) >= _BATCH:
            self.flush()

    def flush(self) -> None:
        """把缓冲写入数据库。"""
        if not self._rows or not self._task_id:
            self._rows.clear()
            return
        rows = list(self._rows)
        api.insert_task_events(self._task_id, rows)
        self._rows.clear()
        for row in rows:
            _add_usage(row, self._agent_id)

    def close(self) -> None:
        """刷尾并回写任务费用。"""
        self.flush()
        if self._task_id:
            api.rollup_task_cost(self._task_id)

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
    """原图转长边 720 的 JPEG 缩略图后入库。坏图跳过。"""
    packed = _thumbnail(image_b64)
    if packed is None:
        return None
    return api.store_task_media(
        ctx.task_id,
        packed["sha256"],
        {
            "event_seq": seq,
            "role_name": (record.role_name or "")[:64],
            "step_seq": ctx.step_seq,
            "attempt": ctx.attempt,
            "media_type": "image/jpeg",
            "byte_size": packed["byte_size"],
            "width": packed["width"],
            "height": packed["height"],
            "thumb_b64": packed["thumb_b64"],
        },
    )


def _thumbnail(image_b64: str) -> dict | None:
    """解码原图并压成缩略图。失败返回 None。"""
    try:
        raw = base64.b64decode(image_b64, validate=False)
        image = Image.open(BytesIO(raw))
        image = image.convert("RGB")
        image.thumbnail((720, 720))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=80)
    except Exception:
        return None
    if not raw:
        return None
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "width": image.size[0],
        "height": image.size[1],
        "thumb_b64": base64.b64encode(buffer.getvalue()).decode("ascii"),
    }


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
