"""平台 SOP 的取消能力：登记、置位、清理与中间件装配。

覆盖 `openspec/specs/backend-bridge-agent` 的「平台运行可取消」。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.middleware.control import RunCancelled

pytestmark = [pytest.mark.unit]


def test_bind_returns_same_token_per_task():
    from engines.backend_bridge.workflow.cancel import bind_cancel, clear_cancel

    first = bind_cancel(11)
    second = bind_cancel(11)
    try:
        assert first is second
        assert first.cancelled is False
    finally:
        clear_cancel(11)


def test_request_cancel_sets_registered_token():
    from engines.backend_bridge.workflow.cancel import bind_cancel, clear_cancel, request_cancel

    token = bind_cancel(12)
    try:
        assert request_cancel(12, "用户关闭") is True
        assert token.cancelled is True
        assert token.reason == "用户关闭"
    finally:
        clear_cancel(12)


def test_request_cancel_without_registration_returns_false():
    from engines.backend_bridge.workflow.cancel import request_cancel

    assert request_cancel(404) is False


def test_clear_cancel_makes_next_run_clean():
    from engines.backend_bridge.workflow.cancel import (
        bind_cancel,
        cancel_controls,
        clear_cancel,
        request_cancel,
    )

    bind_cancel(13)
    clear_cancel(13)
    assert request_cancel(13) is False
    assert cancel_controls(13) == []

    fresh = bind_cancel(13)
    try:
        assert fresh.cancelled is False
    finally:
        clear_cancel(13)


def test_cancel_controls_wrap_token_in_middleware():
    from engines.backend_bridge.workflow.cancel import bind_cancel, cancel_controls, clear_cancel

    bind_cancel(14)
    try:
        controls = cancel_controls(14)
        assert len(controls) == 1
        assert controls[0].token.cancelled is False
    finally:
        clear_cancel(14)


@pytest.mark.asyncio
async def test_cancelled_token_raises_run_cancelled():
    """取消必须抛 RunCancelled，让调用方能与失败区分。"""

    from engines.backend_bridge.workflow.cancel import bind_cancel, cancel_controls, clear_cancel

    bind_cancel(15, reason="用户取消")
    try:
        middleware = cancel_controls(15)[0]
        middleware.token.cancel("用户取消")

        async def never_called(**kwargs):
            raise AssertionError("取消后不应继续调用模型")

        with pytest.raises(RunCancelled):
            await middleware.on_model_call(None, {}, never_called)
    finally:
        clear_cancel(15)
