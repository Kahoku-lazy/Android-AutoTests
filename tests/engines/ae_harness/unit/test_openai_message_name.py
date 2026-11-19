"""openai 消息格式：非 user、非 tool 不带 name。不访问网关。"""

from __future__ import annotations

import pytest

from agentscope.message import AssistantMsg, SystemMsg, ToolResultBlock, UserMsg

from engines.ae_harness.agents.models import OpenAIGatewayFormatter

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_openai_formatter_strips_non_user_name():
    """system 与 assistant 去掉 name 键，正文不变；user 与 tool 保留。"""
    formatted = await OpenAIGatewayFormatter().format(
        [
            SystemMsg(name="CASE_WRITER_PROMPT", content="你是助手"),
            UserMsg(name="user", content="你好"),
            AssistantMsg(name="CASE_WRITER_PROMPT", content="好的"),
            AssistantMsg(
                name="CASE_WRITER_PROMPT",
                content=[ToolResultBlock(id="call_1", name="read_artifact", output="空")],
            ),
        ]
    )
    by_role = {item["role"]: item for item in formatted}

    assert "name" not in by_role["system"]
    assert by_role["system"]["content"]
    assert "name" not in by_role["assistant"]
    assert by_role["user"]["name"] == "user"
    assert by_role["tool"]["name"] == "read_artifact"
