"""任务模型归属：五张表在 task_list，ai_assistant 不再定义任务模型。"""

import pytest

from django.db import connection

from backend.apps.ai_assistant import models as ai_models
from backend.apps.task_list import models

pytestmark = [pytest.mark.unit]


def test_task_models_live_in_task_list():
    assert models.Task._meta.app_label == "task_list"
    assert models.Task._meta.db_table == "task_tasks"
    assert models.TaskAttachment._meta.db_table == "task_attachments"
    assert models.TaskEvent._meta.db_table == "task_events"
    assert models.TaskMedia._meta.db_table == "task_media"
    assert models.TaskUsageHourly._meta.db_table == "task_usage_hourly"


def test_ai_assistant_no_longer_owns_task_models():
    for name in ("AITask", "AITaskAttachment", "AITaskEvent", "AITaskMedia", "AIUsageHourly"):
        assert not hasattr(ai_models, name)


def test_task_foreign_keys_still_point_at_agent_and_media():
    assert models.Task._meta.get_field("agent").remote_field.model is ai_models.AIAgent
    assert models.TaskEvent._meta.get_field("media").remote_field.model is models.TaskMedia


@pytest.mark.django_db
def test_migrations_created_task_tables_not_ai_task_tables():
    tables = set(connection.introspection.table_names())
    assert {
        "task_tasks",
        "task_attachments",
        "task_events",
        "task_media",
        "task_usage_hourly",
    } <= tables
    assert not {
        name for name in tables if name in {"ai_tasks", "ai_task_events", "ai_usage_hourly"}
    }
