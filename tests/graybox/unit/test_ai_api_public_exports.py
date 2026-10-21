"""ai_assistant.api / task_list.api 跨模块导出契约。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant import api
from backend.apps.task_list import api as task_api

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def test_filter_agents_for_user_is_exported():
    assert "filter_agents_for_user" in api.__all__
    assert callable(api.filter_agents_for_user)


def test_task_api_owns_task_writes():
    assert "create_task" in task_api.__all__
    assert "recover_orphaned_tasks" in task_api.__all__
    assert "create_task" not in api.__all__
