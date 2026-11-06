"""把结构化事件批量写入任务事件表、缩略图和小时用量。"""

from __future__ import annotations

import asyncio
import json
import uuid

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from backend.apps.task_list import api, media_storage
from engines.agents.event_sink import current_run
from utils.logs import backend_log

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_BATCH = 50
# 单批字节上限，远低于 MySQL max_allowed_packet（本机实测 64MB），留足余量。
_MAX_BATCH_BYTES = 8 * 1024 * 1024
# 写失败后留在缓冲里等待重试的行数上限；超过就丢最旧的并告警，避免长故障吃光内存。
_RETRY_MAX_ROWS = 500


def in_async_context() -> bool:
    """当前是否处在事件循环线程里。

    Django 禁止在这种上下文里直接访问 ORM（会抛 SynchronousOnlyOperation），
    所以在事件循环里必须把写入推迟到同步上下文，而不是让它失败。

    Returns:
        True 表示当前线程正跑着事件循环。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


class TaskEventSink:
    """平台侧接收方。没有 task_id 时丢弃，避免本地调试写库。"""

    def __init__(self) -> None:
        self._rows: list[dict] = []
        self._bytes = 0
        self._pending: dict | None = None
        self._seq = 0
        self._task_id = 0
        self._agent_id = 0
        self._ready = False
        self._retry = False

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
        """把已结束的行写入数据库。

        成功率优先于「清空缓冲」：写失败的行 MUST 留在缓冲里等下次重试，
        MUST NOT 直接丢弃。处在事件循环线程时推迟到同步上下文再写，
        避免 Django 的 SynchronousOnlyOperation 把整批事件打掉。
        """
        if not self._rows or not self._task_id:
            self._rows.clear()
            self._bytes = 0
            return
        if in_async_context():
            # 事件循环里不能直接访问 ORM：保留缓冲，交给同步上下文的 flush/close
            backend_log.warning(
                "事件写入在事件循环线程里被推迟 task_id=%s rows=%s",
                self._task_id,
                len(self._rows),
            )
            return
        pending = self._rows
        if self._retry:
            # 上次可能写成功但回包失败：重试前剔除已入库的行，避免重复
            existing = self._existing_seqs([row["seq"] for row in pending])
            pending = [row for row in pending if row["seq"] not in existing]
        if pending:
            try:
                api.insert_task_events(self._task_id, pending)
                written = pending
            except Exception:
                backend_log.exception(
                    "事件批量写入失败，降级逐行写 task_id=%s rows=%s",
                    self._task_id,
                    len(pending),
                )
                written = self._insert_one_by_one(pending)
        else:
            written = []
        handled = {row["seq"] for row in written}
        if pending and len(written) < len(pending):
            self._retry = True
        self._rows = [row for row in self._rows if row["seq"] not in handled]
        self._recount()
        self._trim_overflow()
        for row in written:
            _add_usage(row, self._agent_id, self._task_id)

    def _existing_seqs(self, seqs: list[int]) -> set[int]:
        """查出这些序号里已经入库的那些。

        Args:
            seqs: 待写入的行序号。

        Returns:
            已存在的序号集合；查询失败时返回空集合（宁可重复也不丢）。
        """
        from backend.apps.task_list.models import TaskEvent

        try:
            return set(
                TaskEvent.objects.filter(task_id=self._task_id, seq__in=seqs).values_list(
                    "seq", flat=True
                )
            )
        except Exception:
            backend_log.exception("查询已入库事件序号失败 task_id=%s", self._task_id)
            return set()

    def _recount(self) -> None:
        """按剩余缓冲重算字节数。"""
        self._bytes = sum(
            len(json.dumps(row, ensure_ascii=False, default=str)) for row in self._rows
        )

    def _trim_overflow(self) -> None:
        """缓冲积压超过上限时丢最旧的行并告警，防止长故障吃光内存。"""
        overflow = len(self._rows) - _RETRY_MAX_ROWS
        if overflow <= 0:
            return
        dropped = self._rows[:overflow]
        self._rows = self._rows[overflow:]
        self._recount()
        backend_log.warning(
            "事件重试缓冲超过 %s 行，丢弃最旧的 %s 行 task_id=%s seq=%s..%s",
            _RETRY_MAX_ROWS,
            overflow,
            self._task_id,
            dropped[0]["seq"],
            dropped[-1]["seq"],
        )

    def _insert_one_by_one(self, rows: list[dict]) -> list[dict]:
        """逐行写入，返回写成功的行；失败行只记日志。

        Args:
            rows: 一批事件行。

        Returns:
            真正写进数据库的行。
        """
        written: list[dict] = []
        for row in rows:
            try:
                api.insert_task_events(self._task_id, [row])
            except Exception:
                backend_log.warning(
                    "事件行写入失败，留待下次重试 task_id=%s seq=%s type=%s",
                    self._task_id,
                    row.get("seq"),
                    row.get("event_type"),
                )
                continue
            written.append(row)
        return written

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
        """收下一行；满一批或超字节上限就落库。"""
        self._rows.append(row)
        self._bytes += len(json.dumps(row, ensure_ascii=False, default=str))
        if len(self._rows) >= _BATCH or self._bytes >= _MAX_BATCH_BYTES:
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
    payload["task_id"] = ctx.task_id
    if record.event_type == "ModelCallEndEvent":
        payload["usage_id"] = uuid.uuid4().hex
    incoming = int(payload.get("input_tokens") or 0)
    outgoing = int(payload.get("output_tokens") or 0)
    hit = int(payload.get("cache_input_tokens") or 0)
    called_at = _naive(record.ended_at if record.event_type == "ModelCallEndEvent" else None)
    peak = None
    snapshot = _jsonable(record.pricing_snapshot) if record.pricing_snapshot else None
    if isinstance(snapshot, dict) and "peak" in snapshot:
        peak = bool(snapshot["peak"])
    media_id = _media_id(record, image_b64, ctx, seq) if image_b64 else None
    if image_b64 and media_id is None:
        # 有图但存不下来：留痕，事后才分得清「没截图」和「截图存失败」
        payload["media_error"] = "encode_failed"
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


def _add_usage(row: dict, agent_id: int, task_id: int) -> None:
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
    _record_usage(row, task_id, agent_id)


def _record_usage(row: dict, task_id: int, agent_id: int) -> None:
    """把任务模型调用写入全局用量账本；event_id 保证重试幂等。"""
    payload = row.get("payload") or {}
    usage_id_text = str(payload.get("usage_id") or "")
    try:
        usage_id = uuid.UUID(usage_id_text)
    except ValueError:
        usage_id = uuid.uuid4()
    try:
        from backend.apps.usage_ledger.api import record_usage

        record_usage(
            event_id=f"task:{task_id}:{row['seq']}",
            provider=(
                "deepseek" if "deepseek" in str(row.get("model") or "").lower() else "dashscope"
            ),
            model=str(row.get("model") or ""),
            occurred_at=row["called_at"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cache_input_tokens=row["cache_input_tokens"],
            cache_creation_tokens=row["cache_creation_tokens"],
            category="LLM",
            source="task",
            execution_id=str(task_id),
            usage_id=usage_id,
            metadata={
                "role_name": row.get("role_name", ""),
                "role_kind": row.get("role_kind", ""),
                "agent_id": agent_id,
            },
        )
    except Exception:  # noqa: BLE001
        backend_log.exception("写入全局用量账本失败 task_id=%s seq=%s", task_id, row.get("seq"))


def _media_id(record, image_b64: str, ctx, seq: int) -> int | None:
    """压成 720px WebP 后落盘并写元数据。坏图返回 None 并记一条警告。"""
    packed = media_storage.encode(image_b64)
    if packed is None:
        backend_log.warning(
            "截图编码失败 task_id=%s seq=%s role=%s chars=%s",
            ctx.task_id,
            seq,
            (record.role_name or "")[:64],
            len(image_b64),
        )
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
