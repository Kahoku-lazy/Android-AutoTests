"""任务事件落库：事件、缩略图、小时用量和任务费用。"""

from __future__ import annotations

import asyncio
import base64

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

import pytest

from PIL import Image

from apps.ai_assistant import api
from apps.ai_assistant.event_store import TaskEventSink
from apps.ai_assistant.models import AIAgent, AITask, AITaskEvent, AITaskMedia, AIUsageHourly
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


def _task() -> AITask:
    agent = AIAgent.objects.create(name="落库助手")
    return AITask.objects.create(agent=agent, title="写入事件", case_title="卡片页")


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

    rows = list(AITaskEvent.objects.filter(task=task).order_by("seq"))
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
    media = AITaskMedia.objects.get(id=rows[2].media_id)
    assert media.media_type == "image/jpeg"
    assert media.thumb_b64
    assert media.width <= 720
    hourly = AIUsageHourly.objects.get(agent_id=task.agent_id, model="deepseek-flash")
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
    assert AITaskMedia.objects.filter(task=task).count() == 1
    ids = list(AITaskEvent.objects.filter(task=task).values_list("media_id", flat=True))
    assert ids[0] == ids[1]


def test_skips_when_task_id_is_zero():
    sink = TaskEventSink()
    sink.emit(_model_end())
    sink.close()
    assert AITaskEvent.objects.count() == 0
    assert AIUsageHourly.objects.count() == 0


def test_media_cap_and_cascade_delete():
    task = _task()
    for index in range(40):
        saved = api.store_task_media(
            task.id,
            f"{index:064x}",
            {"media_type": "image/jpeg", "byte_size": 1, "thumb_b64": "aa"},
        )
        assert saved is not None
    assert api.store_task_media(task.id, "f" * 64, {"media_type": "image/jpeg"}) is None
    AITaskEvent.objects.create(
        task=task,
        seq=1,
        event_type="ReplyEndEvent",
        phase="end",
        block_type="text",
    )
    task.delete()
    assert AITaskEvent.objects.filter(task_id=task.id).count() == 0
    assert AITaskMedia.objects.filter(task_id=task.id).count() == 0


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

    row = AITaskEvent.objects.get(task=task)
    assert row.event_type == "ReplyEndEvent"
    assert row.step_seq == 2
    assert row.attempt == 1
    assert row.case_title == "卡片页"
