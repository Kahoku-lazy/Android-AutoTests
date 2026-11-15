"""任务域 API 路径：新 /api/tasks/* 存在，旧路径全部 404。"""

import pytest

from django.urls import Resolver404, resolve

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    "path",
    [
        "/api/tasks/",
        "/api/tasks/submit/",
        "/api/tasks/clear/",
        "/api/tasks/1/",
        "/api/tasks/1/report/",
        "/api/tasks/1/rerun/",
        "/api/tasks/1/cancel/",
        "/api/tasks/1/delete/",
        "/api/tasks/upload-file/",
    ],
)
def test_new_task_paths_resolve(path):
    assert resolve(path).view_name.startswith("tasks:")


@pytest.mark.parametrize(
    "path",
    [
        "/api/ai/tasks/submit/",
        "/api/ai/agent-tasks/",
        "/api/ai/agent-tasks/1/",
        "/api/reports/task/1/",
        "/api/ai/upload-file/",
    ],
)
def test_old_task_paths_are_gone(path):
    with pytest.raises(Resolver404):
        resolve(path)
