"""强制交卷时关闭思考，未满轮次的请求保持原样。"""

from __future__ import annotations

import pytest

from agentscope.tool import ToolChoice

from engines.agents.agent_builders import ReActConfig
from engines.agents.middleware.handover import (
    ForcedHandoverMiddleware,
    apply_forced_handover_kwargs,
)

pytestmark = [pytest.mark.unit]


class _Model:
    extra_body = {"thinking": {"type": "enabled"}, "keep": 1}


def test_role_keeps_thirty_free_rounds_and_five_grace():
    assert ReActConfig.__dataclass_fields__["max_iters"].default == 30
    assert ReActConfig.__dataclass_fields__["structured_output_grace_iters"].default == 5


def test_forced_handover_disables_thinking_and_keeps_other_keys():
    choice = ToolChoice(mode="GenerateStructuredOutput")
    got = apply_forced_handover_kwargs(
        _Model(),
        choice,
        {"extra_body": {"note": "x", "thinking": {"budget": 1}}},
    )
    assert got["extra_body"]["thinking"]["type"] == "disabled"
    assert got["extra_body"]["thinking"]["budget"] == 1
    assert got["extra_body"]["keep"] == 1
    assert got["extra_body"]["note"] == "x"


def test_free_round_leaves_thinking_enabled():
    got = apply_forced_handover_kwargs(_Model(), ToolChoice(mode="auto"), {})
    assert "extra_body" not in got


@pytest.mark.asyncio
async def test_middleware_only_disables_thinking_on_forced_call():
    seen = []

    class Model:
        extra_body = {"thinking": {"type": "enabled"}}

    async def next_handler(**kwargs):
        seen.append(kwargs.get("extra_body"))

    model = Model()
    middleware = ForcedHandoverMiddleware()
    await middleware.on_model_call(
        object(),
        {"current_model": model, "tool_choice": ToolChoice(mode="auto")},
        next_handler,
    )
    await middleware.on_model_call(
        object(),
        {"current_model": model, "tool_choice": ToolChoice(mode="GenerateStructuredOutput")},
        next_handler,
    )
    assert seen[0] is None
    assert seen[1]["thinking"]["type"] == "disabled"
    assert not hasattr(model, "_forced_handover_bound")
