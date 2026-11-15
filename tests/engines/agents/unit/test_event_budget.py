"""运行预算：次数按用例数配额，时长默认 4 小时。"""

from __future__ import annotations

import pytest

from engines.agents import event_sink
from engines.agents.event_sink import (
    MAX_MODEL_CALLS,
    MAX_MODEL_CALLS_PER_CASE,
    MAX_RUN_SECONDS,
    bind_run_context,
    budget_exceeded,
    count_model_call,
    reset_run_context,
    set_case_quota,
)

pytestmark = pytest.mark.unit


def _run_with_quota(cases: int):
    """绑定运行上下文并设定用例配额，返回还原令牌。"""
    token = bind_run_context(1, 1)
    set_case_quota(cases)
    return token


def test_run_budget_defaults_to_four_hours() -> None:
    """时长默认 4 小时，给全功能回归留出空间。"""
    assert MAX_RUN_SECONDS == 14400


def test_quota_scales_with_case_count() -> None:
    """配额 = 单用例配额 × 用例数：三条用例时 900 次内不算超。"""
    assert MAX_MODEL_CALLS_PER_CASE > 0
    token = _run_with_quota(3)
    try:
        limit = MAX_MODEL_CALLS_PER_CASE * 3
        for _ in range(limit):
            count_model_call()
        assert budget_exceeded() is False
        count_model_call()
        assert budget_exceeded() is True
    finally:
        reset_run_context(token)


def test_single_case_uses_one_quota() -> None:
    """一条用例时只给单份配额。"""
    token = _run_with_quota(1)
    try:
        for _ in range(MAX_MODEL_CALLS_PER_CASE + 1):
            count_model_call()
        assert budget_exceeded() is True
    finally:
        reset_run_context(token)


def test_without_quota_falls_back_to_absolute_limit() -> None:
    """没设配额时回落到 SOP_MAX_MODEL_CALLS 的绝对上限。"""
    token = bind_run_context(1, 1)
    try:
        for _ in range(MAX_MODEL_CALLS + 1):
            count_model_call()
        assert budget_exceeded() is True
        assert event_sink.MAX_MODEL_CALLS == MAX_MODEL_CALLS
    finally:
        reset_run_context(token)
