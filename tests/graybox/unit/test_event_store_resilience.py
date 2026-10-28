"""事件落库的韧性：整批失败降级逐行、按字节分片、截图失败留痕。

守的是三件事：
1. 一批里有一行永远写不进去（例如 payload 撑爆 MySQL 包上限），不能连带丢掉其余；
2. 单批字节数增长时提前落库，不把一次 `bulk_create` 撑爆；
3. 截图编码失败时行上有 `media_error`，事后分得清「没截图」和「截图存失败」。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.agents.event_sink import RunContext


class _SilentLog:
    """替掉 backend_log，避免测试往 logs/ 写文件。"""

    def warning(self, *args, **kwargs):
        """吞掉警告。"""

    def exception(self, *args, **kwargs):
        """吞掉异常日志。"""


@pytest.mark.unit
def test_flush_falls_back_to_row_by_row(monkeypatch):
    """整批失败时逐行重试：坏行丢弃，好行照样落库。"""
    from backend.apps.task_list import api, event_store

    written: list[int] = []

    def fake_insert(task_id, rows):
        if len(rows) > 1:
            raise RuntimeError("packet too large")
        if rows[0]["seq"] == 2:
            raise RuntimeError("bad row")
        written.append(rows[0]["seq"])

    monkeypatch.setattr(api, "insert_task_events", fake_insert)
    monkeypatch.setattr(event_store, "backend_log", _SilentLog())

    sink = event_store.TaskEventSink()
    sink._task_id = 7
    sink._rows = [
        {"seq": 1, "event_type": "A"},
        {"seq": 2, "event_type": "B"},
        {"seq": 3, "event_type": "C"},
    ]
    sink.flush()

    assert written == [1, 3]
    assert sink._rows == []
    assert sink._bytes == 0


@pytest.mark.unit
def test_flush_splits_batch_by_bytes(monkeypatch):
    """累计字节数达到上限就先落库，不等凑满 50 行。"""
    from backend.apps.task_list import api, event_store

    batches: list[int] = []
    monkeypatch.setattr(api, "insert_task_events", lambda task_id, rows: batches.append(len(rows)))
    monkeypatch.setattr(event_store, "_MAX_BATCH_BYTES", 100)

    sink = event_store.TaskEventSink()
    sink._task_id = 7
    sink._append_row({"seq": 1, "event_type": "A"})
    assert batches == []
    sink._append_row({"seq": 2, "event_type": "B", "payload": {"text": "x" * 200}})
    assert batches == [2]


@pytest.mark.unit
def test_undecodable_screenshot_is_marked_on_row(monkeypatch):
    """坏图不写 media，但在 payload 里留 media_error。"""
    from backend.apps.task_list import event_store

    monkeypatch.setattr(event_store, "backend_log", _SilentLog())
    image_b64 = "!!!not-a-base64-image!!!"
    record = SimpleNamespace(
        event_type="DataBlockEndEvent",
        phase="推理",
        block_type="data",
        is_delta=False,
        role_name="executor_role",
        role_kind="executor",
        model="deepseek-flash",
        payload={"media_type": "image/png", "bytes": len(image_b64)},
        started_at=None,
        ended_at=None,
        duration_ms=0,
        cost_input=0,
        cost_output=0,
        cost_cache=0,
        pricing_snapshot=None,
    )
    ctx = RunContext(task_id=7, agent_id=3, case_title="用例 A")

    row = event_store._row(record, image_b64, ctx, 1)

    assert row["media_id"] is None
    assert row["payload"]["media_error"] == "encode_failed"
    assert row["case_title"] == "用例 A"
