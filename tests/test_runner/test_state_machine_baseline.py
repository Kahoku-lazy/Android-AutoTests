"""Step 0 基线 — 状态机与枚举现状行为锚定。

所有标注「现状行为」的断言将在 converge-state-enums（L1b 枚举收敛）change 中
显式更新。本变更禁止修复任何现状语义（含 "COMPLETED" 大写、双枚举并存）。
"""

import json

import pytest

from django.test import RequestFactory

from apps.test_runner import state_machine as sm
from apps.test_runner.models import TaskCard
from apps.test_runner.views import task_views

pytestmark = [pytest.mark.integration, pytest.mark.test_runner, pytest.mark.django_db]


@pytest.fixture
def task_card():
    return TaskCard.objects.create(task_id="ID-900", name="baseline", mode="immediate")


def _enqueue_and_dequeue(task_card, run_id="run-baseline"):
    sm.enqueue(task_card, "dev-1")
    # enqueue 内部重取实例写库，本地实例需刷新——dequeue 校验用的是传入实例
    task_card.refresh_from_db()
    record = sm.dequeue(task_card, run_id, "dev-1", [], 1)
    return record


class TestLifecycleTransitions:
    def test_full_lifecycle_idle_to_done(self, task_card):
        record = _enqueue_and_dequeue(task_card)
        sm.complete(task_card, record, summary={}, case_items=[], overall_pass=1)

        task_card.refresh_from_db()
        record.refresh_from_db()
        assert task_card.status == "done"
        assert task_card.outcome == "completed"
        assert task_card.running is False
        # L1b 收敛后口径：写库为小写枚举值
        assert record.status == "completed"

    def test_cancel_queued_back_to_idle(self, task_card):
        sm.enqueue(task_card, "dev-1")
        task_card.refresh_from_db()
        assert task_card.status == "queued"

        sm.cancel(task_card)
        task_card.refresh_from_db()
        assert task_card.status == "idle"
        assert task_card.outcome == ""

    @pytest.mark.parametrize(
        "outcome,expected_run_status",
        [("error", "failed"), ("stopped", "stopped"), ("interrupted", "stopped")],
    )
    def test_fail_outcomes(self, task_card, outcome, expected_run_status):
        record = _enqueue_and_dequeue(task_card)
        sm.fail(task_card, record, outcome=outcome)

        task_card.refresh_from_db()
        record.refresh_from_db()
        assert task_card.status == "done"
        assert task_card.outcome == outcome
        assert record.status == expected_run_status

    def test_fail_invalid_outcome_rejected(self, task_card):
        record = _enqueue_and_dequeue(task_card)
        with pytest.raises(ValueError):
            sm.fail(task_card, record, outcome="invalid")

    def test_illegal_transition_raises(self, task_card):
        # idle → running 直接跳转非法
        with pytest.raises(sm.InvalidTransition):
            sm.dequeue(task_card, "run-x", "dev-1", [], 1)
        # done 是终态，不可再入队
        record = _enqueue_and_dequeue(task_card)
        sm.complete(task_card, record, summary={}, case_items=[])
        with pytest.raises(sm.InvalidTransition):
            sm.enqueue(task_card, "dev-1")

    def test_idempotent_same_transition(self, task_card):
        record = _enqueue_and_dequeue(task_card)
        sm.complete(task_card, record, summary={}, case_items=[])
        # 重复同一终态转换是安全 no-op
        sm.complete(task_card, record, summary={}, case_items=[])
        task_card.refresh_from_db()
        assert task_card.status == "done"
        assert task_card.outcome == "completed"


class TestDriftRepair:
    def test_repair_queued_terminal_drift(self):
        # 现状行为：queued + 终态 outcome 是历史 bug 遗留的漂移数据
        for i, outcome in enumerate(["completed", "stopped", "interrupted", "error"]):
            TaskCard.objects.create(
                task_id=f"ID-DRIFT-{i}",
                name="drift",
                status="queued",
                running=True,
                outcome=outcome,
            )
        clean = TaskCard.objects.create(
            task_id="ID-CLEAN", name="clean", status="queued", outcome=""
        )

        fixed = sm.repair_queued_terminal_drift()

        assert fixed == 4
        for i in range(4):
            t = TaskCard.objects.get(task_id=f"ID-DRIFT-{i}")
            assert t.status == "done"
            assert t.running is False
            assert t.outcome in ("completed", "stopped", "interrupted", "error")
        clean.refresh_from_db()
        assert clean.status == "queued"


class TestDisplayState:
    """Step 5 权威状态判定：display_state 是「任务处于什么状态」的唯一入口。"""

    def _card(self, task_id, status="idle", outcome="", running=False):
        return TaskCard.objects.create(
            task_id=task_id, name="ds", status=status, outcome=outcome, running=running
        )

    def test_running_flag_wins(self):
        assert sm.display_state(self._card("ID-DS-1", status="running", running=True)) == "running"

    def test_queued_without_outcome(self):
        assert sm.display_state(self._card("ID-DS-2", status="queued")) == "queued"

    def test_queued_with_terminal_outcome_is_done_drift(self):
        # 历史漂移：queued + 终态 outcome → 视为已终态（与 repair 语义一致）
        assert (
            sm.display_state(self._card("ID-DS-3", status="queued", outcome="completed")) == "done"
        )

    @pytest.mark.parametrize("outcome", ["completed", "stopped", "interrupted", "error"])
    def test_terminal_outcome_is_done(self, outcome):
        assert (
            sm.display_state(self._card(f"ID-DS-4-{outcome}", status="done", outcome=outcome))
            == "done"
        )

    def test_idle(self):
        assert sm.display_state(self._card("ID-DS-5")) == "idle"


class TestSerialization:
    def test_task_card_list_serialization_anchor(self, task_card):
        request = RequestFactory().get("/api/runner/tasks")
        request.user_id = "tester"

        resp = task_views.task_card_list(request)
        payload = json.loads(resp.content)

        assert payload["status"] is True
        card = next(t for t in payload["tasks"] if t["id"] == "ID-900")
        assert card["status"] == "idle"
        assert card["outcome"] == ""
        assert card["taskType"] == "ui_automation"
        assert card["deviceSerial"] == ""
        # 现状行为：running 派生自 status（杜绝双源不一致）
        assert card["running"] == (card["status"] == "running")
        # Step 5 权威状态：后端下发 state 字段（前端 Step 6 切换消费）
        assert card["state"] == "idle"


class TestRunStatusSingleDefinition:
    """L1b 收敛后：TestRunStatus 唯一定义于 models.test_models（5 值小写）。"""

    def test_single_definition(self):
        from models import constants as m_constants
        from models import test_models

        assert not hasattr(m_constants, "TestRunStatus")
        assert {e.value for e in test_models.TestRunStatus} == {
            "pending",
            "running",
            "completed",
            "stopped",
            "failed",
        }

    def test_state_machine_writes_lowercase_completed(self, task_card):
        record = _enqueue_and_dequeue(task_card)
        sm.complete(task_card, record, summary={}, case_items=[])
        record.refresh_from_db()
        assert record.status == "completed"

    def test_fail_writes_lowercase_status(self, task_card):
        record = _enqueue_and_dequeue(task_card)
        sm.fail(task_card, record, outcome="error")
        record.refresh_from_db()
        assert record.status == "failed"
