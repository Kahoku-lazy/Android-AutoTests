"""把结构化事件写成 CSV，再读回成原类型。模拟尚未落地的事件表。"""

from __future__ import annotations

import csv
import json
import sys

from datetime import datetime
from decimal import Decimal
from pathlib import Path

COLUMNS = (
    "task_id",
    "case_title",
    "step_seq",
    "attempt",
    "seq",
    "event_type",
    "phase",
    "block_type",
    "is_delta",
    "role_name",
    "role_kind",
    "model",
    "status",
    "payload",
    "started_at",
    "ended_at",
    "duration_ms",
    "input_tokens",
    "cache_input_tokens",
    "output_tokens",
    "cost_input",
    "cost_cache",
    "cost_output",
    "cost_total",
    "is_peak",
    "media_type",
    "image_b64",
)

_INT_FIELDS = (
    "task_id",
    "step_seq",
    "attempt",
    "seq",
    "duration_ms",
    "input_tokens",
    "cache_input_tokens",
    "output_tokens",
)
_DECIMAL_FIELDS = ("cost_input", "cost_cache", "cost_output", "cost_total")
_TEXT_FIELDS = (
    "case_title",
    "event_type",
    "phase",
    "block_type",
    "role_name",
    "role_kind",
    "model",
    "status",
    "media_type",
    "image_b64",
)


class CsvEventStore:
    """用 CSV 模拟事件表：emit 相当于插入。"""

    def __init__(self, path: Path, case_title: str = "测试 Agents 工作流"):
        self.path = path
        self.task_id = 1
        self.case_title = case_title
        self.step_seq = 1
        self.attempt = 1
        self._seq = 0
        self._rows: list[dict] = []

    def emit(self, record, image_b64: str = "") -> None:
        """把一条结构化记录收成一行。图片原文放在 image_b64 列。"""
        self._seq += 1
        payload = dict(record.payload or {})
        snapshot = record.pricing_snapshot or {}
        self._rows.append(
            {
                "task_id": self.task_id,
                "case_title": self.case_title,
                "step_seq": self.step_seq,
                "attempt": self.attempt,
                "seq": self._seq,
                "event_type": record.event_type,
                "phase": record.phase,
                "block_type": record.block_type,
                "is_delta": bool(record.is_delta),
                "role_name": record.role_name,
                "role_kind": record.role_kind,
                "model": record.model,
                "status": str(payload.get("status") or ""),
                "payload": payload,
                "started_at": record.started_at,
                "ended_at": record.ended_at,
                "duration_ms": int(record.duration_ms or 0),
                "input_tokens": int(payload.get("input_tokens") or 0),
                "cache_input_tokens": int(payload.get("cache_input_tokens") or 0),
                "output_tokens": int(payload.get("output_tokens") or 0),
                "cost_input": record.cost_input,
                "cost_cache": record.cost_cache,
                "cost_output": record.cost_output,
                "cost_total": record.cost_input + record.cost_cache + record.cost_output,
                "is_peak": snapshot.get("peak") if snapshot else None,
                "media_type": record.media_type or "",
                "image_b64": image_b64 or "",
            }
        )

    def flush(self) -> None:
        """把缓冲行写入 CSV。没有记录时仍写出表头。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for row in self._rows:
                writer.writerow({key: _cell(row[key]) for key in COLUMNS})


def _allow_large_fields() -> None:
    """放宽 CSV 单字段上限，容纳截图 base64。"""
    limit = sys.maxsize
    while limit > 131072:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10
    csv.field_size_limit(limit)


def load_event_csv(path: Path) -> list[dict]:
    """从 CSV 读回，并还原成入库前的类型。"""
    _allow_large_fields()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(COLUMNS)
        return [_parse(raw) for raw in reader]


def assert_event_row(row: dict) -> None:
    """每一列的类型与事件表约定一致。"""
    assert set(row) == set(COLUMNS)
    for key in _INT_FIELDS:
        assert type(row[key]) is int
    for key in _DECIMAL_FIELDS:
        assert type(row[key]) is Decimal
        assert f"{row[key]:.8f}" == _cell(row[key])
    for key in _TEXT_FIELDS:
        assert type(row[key]) is str
    assert type(row["is_delta"]) is bool
    assert row["is_peak"] is None or type(row["is_peak"]) is bool
    assert row["started_at"] is None or type(row["started_at"]) is datetime
    assert row["ended_at"] is None or type(row["ended_at"]) is datetime
    assert type(row["payload"]) is dict


def _cell(value) -> str:
    """把一行里的值写成 CSV 文本。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, Decimal):
        return f"{value:.8f}"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _parse(raw: dict) -> dict:
    """按列把 CSV 字符串还原成整数、小数、布尔、时间和字典。"""
    row = dict(raw)
    for key in _INT_FIELDS:
        row[key] = int(row[key])
    for key in _DECIMAL_FIELDS:
        row[key] = Decimal(row[key])
    row["is_delta"] = row["is_delta"] == "1"
    row["is_peak"] = None if row["is_peak"] == "" else row["is_peak"] == "1"
    for key in ("started_at", "ended_at"):
        row[key] = datetime.fromisoformat(row[key]) if row[key] else None
    row["payload"] = json.loads(row["payload"])
    return row
