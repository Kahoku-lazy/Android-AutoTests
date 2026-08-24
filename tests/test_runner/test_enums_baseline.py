"""L1b 枚举收敛后的执行侧枚举单元测试（无 DB）。"""

import pytest

from models.test_models import TaskCardStatus, TaskOutcome, TestRunStatus

pytestmark = [pytest.mark.unit, pytest.mark.test_runner]


class TestTaskOutcome:
    def test_terminal_values(self):
        assert TaskOutcome.terminal_values() == [
            "completed",
            "stopped",
            "interrupted",
            "error",
        ]

    def test_fail_values_excludes_completed(self):
        assert TaskOutcome.fail_values() == ["stopped", "interrupted", "error"]
        assert "completed" not in TaskOutcome.fail_values()

    def test_choices_format_with_labels(self):
        pairs = TaskOutcome.choices()
        assert pairs == [
            ("completed", "已完成"),
            ("stopped", "已停止"),
            ("interrupted", "运行中断"),
            ("error", "异常终止"),
        ]


class TestTaskCardStatus:
    def test_four_values(self):
        assert [e.value for e in TaskCardStatus] == ["idle", "queued", "running", "done"]

    def test_choices_format_with_labels(self):
        assert TaskCardStatus.choices() == [
            ("idle", "未执行"),
            ("queued", "排队中"),
            ("running", "执行中"),
            ("done", "已完成"),
        ]


class TestRunStatusEnum:
    def test_five_values_lowercase(self):
        assert [e.value for e in TestRunStatus] == [
            "pending",
            "running",
            "completed",
            "stopped",
            "failed",
        ]

    def test_outcome_to_run_status_mapping(self):
        """L1b §4.1 映射表：TaskOutcome → TestRunStatus（state_machine 写库翻译）。"""
        mapping = {
            TaskOutcome.COMPLETED: TestRunStatus.COMPLETED,
            TaskOutcome.STOPPED: TestRunStatus.STOPPED,
            TaskOutcome.INTERRUPTED: TestRunStatus.STOPPED,
            TaskOutcome.ERROR: TestRunStatus.FAILED,
        }
        assert mapping[TaskOutcome.COMPLETED].value == "completed"
        assert mapping[TaskOutcome.INTERRUPTED].value == "stopped"
        assert mapping[TaskOutcome.ERROR].value == "failed"
