"""任务事件落库：事件、缩略图、小时用量和任务费用。"""

from __future__ import annotations

import asyncio
import base64

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from django.conf import settings as django_settings
from PIL import Image

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api, media_storage
from backend.apps.task_list.event_store import TaskEventSink
from backend.apps.task_list.models import Task, TaskEvent, TaskMedia, TaskUsageHourly
from engines.agents.event_sink import (
    bind_run_context,
    bind_sink,
    reset_run_context,
    reset_sink,
    set_step_context,
)
from engines.agents.messaging.record import EventRecord
from engines.agents.workflow.ui_auto_workflow import show_event

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_CALLED = datetime(2026, 10, 20, 10, 0, tzinfo=_SHANGHAI)
_MONEY = Decimal("0.00002000")


@pytest.fixture(autouse=True)
def _temp_media_dir(settings, tmp_path):
    """截图落盘改到临时目录，避免测试写进真实 DATA_DIR。"""
    settings.TASK_MEDIA_DIR = tmp_path / "task_media"
    media_storage.reset_media_storage()
    yield
    media_storage.reset_media_storage()


def _task() -> Task:
    agent = AIAgent.objects.create(name="落库助手")
    return Task.objects.create(agent=agent, title="写入事件", case_title="卡片页")


def _png(color: tuple[int, int, int]) -> str:
    image = Image.new("RGB", (8, 8), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _model_end() -> EventRecord:
    return EventRecord(
        event_type="ModelCallEndEvent",
        phase="end",
        block_type="model",
        role_name="executor_role",
        role_kind="executor",
        model="deepseek-flash",
        payload={"input_tokens": 1000, "output_tokens": 10, "cache_input_tokens": 1000},
        ended_at=_CALLED,
        cost_input=Decimal("0"),
        cost_output=Decimal("0.00004000"),
        cost_cache=_MONEY,
        pricing_snapshot={"peak": True, "model": "deepseek-flash"},
    )


def test_writes_events_media_hourly_and_task_cost():
    task = _task()
    sink = TaskEventSink()
    sink_token = bind_sink(sink)
    run_token = bind_run_context(task.id, task.agent_id, task.case_title)
    set_step_context(2, 1)
    try:
        sink.emit(
            EventRecord(
                event_type="ReplyEndEvent",
                phase="end",
                block_type="text",
                role_name="executor_role",
            ),
        )
        sink.emit(_model_end(), "")
        sink.emit(
            EventRecord(
                event_type="ToolResultEndEvent",
                phase="end",
                block_type="tool",
                role_name="executor_role",
                media_type="image/png",
            ),
            _png((10, 20, 30)),
        )
        sink.close()
    finally:
        reset_sink(sink_token)
        reset_run_context(run_token)

    rows = list(TaskEvent.objects.filter(task=task).order_by("seq"))
    assert [row.seq for row in rows] == [1, 2, 3]
    assert rows[0].event_type == "ReplyEndEvent"
    assert rows[0].step_seq == 2
    assert rows[0].attempt == 1
    assert rows[0].case_title == "卡片页"
    assert rows[1].event_type == "ModelCallEndEvent"
    assert rows[1].cache_miss_tokens == 0
    assert rows[1].cost_cache == _MONEY
    assert rows[1].called_hour == 10
    assert rows[1].is_peak is True
    assert rows[2].media_id is not None
    media = TaskMedia.objects.get(id=rows[2].media_id)
    assert media.media_type == "image/webp"
    assert media.storage_key
    assert not media.thumb_b64
    assert media.width <= 720
    assert Path(django_settings.TASK_MEDIA_DIR, media.storage_key).is_file()
    hourly = TaskUsageHourly.objects.get(agent_id=task.agent_id, model="deepseek-flash")
    assert hourly.calls == 1
    assert hourly.cost_cache == _MONEY
    task.refresh_from_db()
    assert task.cost_cache == _MONEY
    assert task.cost_output == Decimal("0.00004000")
    assert task.cost_total == Decimal("0.00006000")


def test_same_image_is_one_media_row():
    task = _task()
    picture = _png((1, 2, 3))
    sink = TaskEventSink()
    token = bind_run_context(task.id, task.agent_id, "")
    try:
        sink.emit(
            EventRecord(event_type="ToolResultEndEvent", phase="end", block_type="tool"), picture
        )
        sink.emit(
            EventRecord(event_type="ToolResultEndEvent", phase="end", block_type="tool"), picture
        )
        sink.flush()
    finally:
        reset_run_context(token)
    assert TaskMedia.objects.filter(task=task).count() == 1
    assert len(list((Path(django_settings.TASK_MEDIA_DIR) / str(task.id)).iterdir())) == 1
    ids = list(TaskEvent.objects.filter(task=task).values_list("media_id", flat=True))
    assert ids[0] == ids[1]


def test_skips_when_task_id_is_zero():
    sink = TaskEventSink()
    sink.emit(_model_end())
    sink.close()
    assert TaskEvent.objects.count() == 0
    assert TaskUsageHourly.objects.count() == 0


def test_media_has_no_count_cap_and_cascade_delete():
    task = _task()
    TaskMedia.objects.bulk_create(
        [
            TaskMedia(
                task=task,
                sha256=f"{index:064x}",
                media_type="image/webp",
                byte_size=1,
                thumb_b64="aa",
            )
            for index in range(300)
        ]
    )
    saved = api.store_task_media(
        task.id,
        {
            "sha256": "f" * 64,
            "data": b"webp-bytes",
            "width": 8,
            "height": 8,
            "media_type": "image/webp",
        },
        {},
    )
    assert saved is not None
    assert TaskMedia.objects.filter(task_id=task.id).count() == 301
    media = TaskMedia.objects.get(id=saved)
    assert Path(django_settings.TASK_MEDIA_DIR, media.storage_key).is_file()
    TaskEvent.objects.create(
        task=task,
        seq=1,
        event_type="ReplyEndEvent",
        phase="end",
        block_type="text",
    )
    api.delete_task(task)
    assert TaskEvent.objects.filter(task_id=task.id).count() == 0
    assert TaskMedia.objects.filter(task_id=task.id).count() == 0
    assert not (Path(django_settings.TASK_MEDIA_DIR) / str(task.id)).exists()


def _delta(index: int) -> EventRecord:
    return EventRecord(
        event_type="ToolCallDeltaEvent",
        phase="推理",
        block_type="tool_call",
        is_delta=True,
        role_name="executor_role",
        role_kind="executor",
        payload={"delta": "x", "idx": index},
        ended_at=datetime(2026, 10, 20, 10, 0, 0, index, tzinfo=_SHANGHAI),
    )


def test_consecutive_deltas_fold_into_one_row():
    task = _task()
    sink = TaskEventSink()
    token = bind_run_context(task.id, task.agent_id, "卡片页")
    try:
        set_step_context(1, 1)
        for index in range(3):
            sink.emit(_delta(index))
        sink.emit(
            EventRecord(
                event_type="ReplyEndEvent",
                phase="结束",
                block_type="reply",
                payload={"finished_reason": "stop"},
            )
        )
        sink.close()
    finally:
        reset_run_context(token)

    rows = list(TaskEvent.objects.filter(task=task).order_by("seq"))
    assert [row.event_type for row in rows] == ["ToolCallDeltaEvent", "ReplyEndEvent"]
    assert [row.seq for row in rows] == [1, 2]
    delta_row = rows[0]
    assert delta_row.delta_count == 3
    assert delta_row.payload == {"delta_count": 3}
    assert delta_row.ended_at == datetime(2026, 10, 20, 10, 0, 0)


def test_delta_run_survives_batch_flush():
    task = _task()
    sink = TaskEventSink()
    token = bind_run_context(task.id, task.agent_id, "卡片页")
    try:
        set_step_context(1, 1)
        for index in range(120):
            sink.emit(_delta(index))
        assert TaskEvent.objects.filter(task=task).count() == 0
        sink.close()
    finally:
        reset_run_context(token)

    rows = list(TaskEvent.objects.filter(task=task).order_by("seq"))
    assert len(rows) == 1
    assert rows[0].delta_count == 120


def test_step_change_splits_delta_run():
    task = _task()
    sink = TaskEventSink()
    token = bind_run_context(task.id, task.agent_id, "卡片页")
    try:
        set_step_context(1, 1)
        sink.emit(_delta(0))
        sink.emit(_delta(1))
        set_step_context(2, 1)
        sink.emit(_delta(2))
        sink.emit(_delta(3))
        sink.close()
    finally:
        reset_run_context(token)

    rows = list(TaskEvent.objects.filter(task=task).order_by("seq"))
    assert [row.delta_count for row in rows] == [2, 2]
    assert [row.seq for row in rows] == [1, 2]


class ReplyEndEvent:
    finished_reason = "completed"


@pytest.mark.django_db(transaction=True)
def test_show_event_from_running_loop_writes():
    task = _task()
    sink = TaskEventSink()
    sink_token = bind_sink(sink)
    run_token = bind_run_context(task.id, task.agent_id, "卡片页")

    async def _run():
        set_step_context(2, 1)
        await show_event(ReplyEndEvent(), {}, {})

    try:
        asyncio.run(_run())
        sink.close()
    finally:
        reset_sink(sink_token)
        reset_run_context(run_token)

    row = TaskEvent.objects.get(task=task)
    assert row.event_type == "ReplyEndEvent"
    assert row.step_seq == 2
    assert row.attempt == 1
    assert row.case_title == "卡片页"
