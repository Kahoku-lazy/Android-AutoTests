"""最近任务卡副行只读冻结身份，不回读用例库。"""

from __future__ import annotations

import pytest

from backend.apps.dashboard.ai_usage import ai_recent_tasks
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_recent_task_uses_frozen_case_label():
    Task.objects.create(
        title="工作流",
        status="completed",
        task_kind=TaskKind.ASSISTANT_SOP,
        case_identity={
            "source": "platform",
            "rows": [
                {"project": "灯", "id": "1", "title": "定时"},
                {"project": "灯", "id": "2", "title": "场景"},
            ],
        },
    )
    rows = ai_recent_tasks("1")
    assert rows[0]["title"] == "工作流"
    assert rows[0]["case_label"] == "定时 · 共 2 条"
