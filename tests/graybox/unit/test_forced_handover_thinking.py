"""强制交卷时关闭思考，未满轮次的请求保持原样。"""

from __future__ import annotations

import pytest

from agentscope.tool import ToolChoice

from engines.agents.role.config import (
    RoleSpecConfig,
    apply_forced_handover_kwargs,
    bind_forced_handover,
)

pytestmark = [pytest.mark.unit]


class _Model:
    extra_body = {"thinking": {"type": "enabled"}, "keep": 1}


def test_role_keeps_thirty_free_rounds_and_five_grace():
    assert RoleSpecConfig.__dataclass_fields__["max_iters"].default == 30
    assert RoleSpecConfig.__dataclass_fields__["structured_output_grace_iters"].default == 5


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
async def test_bound_model_only_disables_thinking_on_forced_call():
    seen = []

    class Model:
        extra_body = {"thinking": {"type": "enabled"}}

        async def _call_api(self, *args, **kwargs):
            seen.append(kwargs.get("extra_body"))

    model = bind_forced_handover(Model())
    await model._call_api(tool_choice=ToolChoice(mode="auto"))
    await model._call_api(tool_choice=ToolChoice(mode="GenerateStructuredOutput"))
    assert seen[0] is None
    assert seen[1]["thinking"]["type"] == "disabled"
