"""任务收尾状态常量完整性：防 `TaskStatus` 缺成员导致 AttributeError。

历史事故：旧 task_runner 在建终态映射时引用不存在的 `TaskStatus.CANCELLED`，
收尾阶段直接抛异常，把已经跑完的任务记成 failed。本用例在导入期就校验映射值，
缺成员时导入即失败，不会等到线上收尾才暴露。
"""

from __future__ import annotations

import pytest

from backend.apps.task_list.task_runner import RESULT_STATUS_MAP
from backend.models.constants import TaskStatus

pytestmark = [pytest.mark.unit]


def test_result_status_map_values_are_task_status_members():
    """收尾映射的每个值都必须是 TaskStatus 成员。"""
    assert RESULT_STATUS_MAP
    for engine_status, task_status in RESULT_STATUS_MAP.items():
        assert isinstance(task_status, TaskStatus), engine_status
        assert task_status.value in {member.value for member in TaskStatus}


def test_interrupted_status_exists():
    """启动恢复依赖 interrupted，必须已登记。"""
    assert TaskStatus.INTERRUPTED == "interrupted"
