"""govee 思考模式拒绝强制选工具时，按请求类型重发。不访问网关。"""

from __future__ import annotations

import pytest

from agentscope.model import DashScopeChatModel, DeepSeekChatModel
from agentscope.tool import ToolChoice

from engines.ae_harness.agents.models import (
    GoveeThinkingChatModel,
    OpenAIChatModel,
    create_model,
)

pytestmark = [pytest.mark.unit]

REJECT = "Thinking mode does not support this tool_choice"
TOOLS = [
    {"type": "function", "function": {"name": "adb_tap"}},
    {"type": "function", "function": {"name": "GenerateStructuredOutput"}},
]


@pytest.fixture
def govee(monkeypatch):
    monkeypatch.setattr("engines.ae_harness.agents.models.load_secret", lambda _name: "sk-test")
    created = create_model("govee", "GOVEE_API_KEY", "deepseek-flash", "https://example.invalid/v1", stream=False)
    return created.model


def _patch(monkeypatch, responses: list):
    calls = []

    async def fake(_self, model_name, messages, tools=None, tool_choice=None, **kwargs):
        calls.append({"tools": tools, "tool_choice": tool_choice, "extra": kwargs.get("extra_body")})
        item = responses[len(calls) - 1]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(OpenAIChatModel, "_call_api", fake)
    return calls


@pytest.mark.asyncio
async def test_other_400_is_not_retried(govee, monkeypatch):
    calls = _patch(monkeypatch, [RuntimeError("别的 400")])
    with pytest.raises(RuntimeError, match="别的 400"):
        await govee._call_api("m", [], TOOLS, ToolChoice(mode="GenerateStructuredOutput"))
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_unforced_call_is_not_retried(govee, monkeypatch):
    calls = _patch(monkeypatch, [RuntimeError(REJECT)])
    with pytest.raises(RuntimeError):
        await govee._call_api("m", [], TOOLS, None)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_device_tool_retry_keeps_name_and_disables_thinking(govee, monkeypatch):
    calls = _patch(monkeypatch, [RuntimeError(REJECT), "ok"])
    result = await govee._call_api("m", [], TOOLS, ToolChoice(mode="adb_tap"))
    assert result == "ok"
    assert calls[1]["tool_choice"].mode == "adb_tap"
    assert calls[1]["tools"] == TOOLS
    assert calls[1]["extra"]["thinking"]["type"] == "disabled"


@pytest.mark.asyncio
async def test_none_retry_stays_none(govee, monkeypatch):
    calls = _patch(monkeypatch, [RuntimeError(REJECT), "ok"])
    await govee._call_api("m", [], TOOLS, ToolChoice(mode="none"))
    assert calls[1]["tool_choice"].mode == "none"
    assert calls[1]["extra"]["thinking"]["type"] == "disabled"


@pytest.mark.asyncio
async def test_structured_second_reject_drops_device_tools(govee, monkeypatch):
    calls = _patch(monkeypatch, [RuntimeError(REJECT), RuntimeError(REJECT), "ok"])
    await govee._call_api("m", [], TOOLS, ToolChoice(mode="GenerateStructuredOutput"))
    assert calls[1]["tool_choice"].mode == "GenerateStructuredOutput"
    assert calls[2]["tool_choice"].mode == "auto"
    names = [item["function"]["name"] for item in calls[2]["tools"]]
    assert names == ["GenerateStructuredOutput"]


def test_other_providers_are_not_wrapped(monkeypatch):
    monkeypatch.setattr("engines.ae_harness.agents.models.load_secret", lambda _name: "sk-test")
    deepseek = create_model("deepseek", "DEEPSEEK_API_KEY", "deepseek-flash")
    dashscope = create_model("dashscope", "DASHSCOPE_API_KEY", "qwen-plus")
    assert isinstance(deepseek.model, DeepSeekChatModel)
    assert not isinstance(deepseek.model, GoveeThinkingChatModel)
    assert isinstance(dashscope.model, DashScopeChatModel)
