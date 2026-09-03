"""灰盒·单元测试示例 — 纯逻辑，零 I/O 零 DB。

演示单元测试写法；真实用例请替换为对应模块的纯函数/枚举测试。
"""

import pytest

from models import test_models


@pytest.mark.unit
def test_task_outcome_terminal_values():
    assert test_models.TaskOutcome.terminal_values() == ["completed", "stopped", "interrupted", "error"]


@pytest.mark.unit
def test_task_outcome_fail_values_exclude_completed():
    assert test_models.TaskOutcome.fail_values() == ["stopped", "interrupted", "error"]


@pytest.mark.unit
def test_run_status_lowercase_values():
    assert {e.value for e in test_models.TestRunStatus} == {
        "pending",
        "running",
        "completed",
        "stopped",
        "failed",
    }
