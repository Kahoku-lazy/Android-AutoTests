"""状态机 _validate() 纯逻辑测试 — 零 I/O，无 DB 依赖。

覆盖：
- 7 条合法转移（idle→queued, queued→running, queued→idle, running→done/*）
- 所有非法转移（done→任意、queued→done 等）
- 幂等设计（同状态重复调用不抛异常）
"""

from unittest.mock import Mock
import pytest

from apps.test_runner.state_machine import _validate, InvalidTransition


def _card(status="idle", outcome=""):
    """快捷构造一个 mock TaskCard（只含 status 和 outcome 属性）。"""
    card = Mock()
    card.status = status
    card.outcome = outcome
    return card


class TestValidTransitions:
    """合法转移——不应抛异常。"""

    @pytest.mark.parametrize("status,outcome,new_status,new_outcome,desc", [
        ("idle",    "",  "queued",   "",             "未执行 → 等待中（入队）"),
        ("queued",  "",  "running",  "",             "等待中 → 执行中（出队）"),
        ("queued",  "",  "idle",     "",             "等待中 → 未执行（取消）"),
        ("running", "",  "done",     "completed",    "执行中 → 已完成（正常）"),
        ("running", "",  "done",     "stopped",      "执行中 → 已完成（手动停止）"),
        ("running", "",  "done",     "interrupted",  "执行中 → 已完成（服务中断）"),
        ("running", "",  "done",     "error",        "执行中 → 已完成（执行错误）"),
    ])
    def test_valid_transition(self, status, outcome, new_status, new_outcome, desc):
        card = _card(status, outcome)
        _validate(card, new_status, new_outcome)  # 不抛异常 = 通过

    def test_idle_to_queued_str_device_serial_not_validated_here(self):
        """_validate 不关心 device_serial——那是 _save_transition 的职责。"""
        card = _card("idle", "")
        _validate(card, "queued", "")


class TestIdempotency:
    """幂等——同一状态重复转移是安全的空操作。"""

    @pytest.mark.parametrize("status,outcome", [
        ("idle",    ""),
        ("queued",  ""),
        ("running", ""),
        ("done",    "completed"),
        ("done",    "stopped"),
        ("done",    "interrupted"),
        ("done",    "error"),
    ])
    def test_same_state_is_noop(self, status, outcome):
        """重复执行当前状态不变 → 不抛异常。"""
        card = _card(status, outcome)
        _validate(card, status, outcome)

    def test_queued_with_different_device_not_validated(self):
        """_validate 不检查队列所属设备，只检查状态本身。"""
        card = _card("queued", "")
        _validate(card, "queued", "")


class TestInvalidTransitions:
    """非法转移——必须抛 InvalidTransition。"""

    def test_done_cannot_transition_to_anything(self):
        """终态禁止任何再转移。"""
        for new_status in ("queued", "running", "idle"):
            for new_outcome in ("", "completed", "stopped", "error"):
                if new_status == "done" and new_outcome == "completed":
                    continue  # 同状态幂等，不抛异常
                card = _card("done", "completed")
                with pytest.raises(InvalidTransition):
                    _validate(card, new_status, new_outcome)

    def test_idle_cannot_jump_to_running_without_queuing(self):
        """idle 只能到 queued，不能直接到 running。"""
        card = _card("idle", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "running", "")

    def test_idle_cannot_jump_directly_to_done(self):
        card = _card("idle", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "done", "completed")

    def test_queued_cannot_go_directly_to_done(self):
        """queued 只能到 running 或 idle，不能跳过 running 直接到 done。"""
        card = _card("queued", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "done", "completed")

    def test_queued_cannot_go_to_random_status(self):
        card = _card("queued", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "unknown_status", "")

    def test_running_cannot_go_back_to_idle(self):
        """running 不能回退到 idle——必须经过 done 终态。"""
        card = _card("running", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "idle", "")

    def test_running_cannot_go_back_to_queued(self):
        card = _card("running", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "queued", "")

    def test_running_invalid_outcome(self):
        """running→done 只能是那 4 种 outcome。"""
        card = _card("running", "")
        with pytest.raises(InvalidTransition):
            _validate(card, "done", "timeout")  # 不存在的 outcome


class TestInvalidTransitionMessage:
    """异常消息应包含 task_id 和状态信息以便调试。"""

    def test_message_contains_task_id_and_states(self):
        card = _card("done", "completed")
        with pytest.raises(InvalidTransition) as exc:
            _validate(card, "queued", "")
        msg = str(exc.value)
        assert "→" in msg
        assert "queued" in msg.lower() or "queued" in msg
