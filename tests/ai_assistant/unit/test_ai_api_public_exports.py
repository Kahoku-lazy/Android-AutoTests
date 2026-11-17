"""ai_assistant.api / task_list.api 跨模块导出契约。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant import api
from backend.apps.task_list import api as task_api

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def test_config_writes_are_exported():
    assert "create_model_config" in api.__all__
    assert "create_role" in api.__all__
    assert callable(api.create_role)


def test_task_api_owns_task_writes():
    assert "create_task" in task_api.__all__
    assert "recover_orphaned_tasks" in task_api.__all__
    assert "create_task" not in api.__all__
