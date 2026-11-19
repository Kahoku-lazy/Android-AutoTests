"""openai 关思考官方扩展点契约（openai-thinking-tool-choice 新增需求）。

断言扩展点形状与官方 DeepSeek 同款，且新增扩展点不改变「普通 400 只发一次」的既有规则。
不访问网关。
"""

from __future__ import annotations

import pytest

from agentscope.tool import ToolChoice

from engines.ae_harness.agents.models import OpenAIChatModel, create_model

pytestmark = [pytest.mark.unit]

REJECT = "Thinking mode does not support this tool_choice"


@pytest.fixture
def openai(monkeypatch):
    monkeypatch.setattr("engines.ae_harness.agents.models.load_secret", lambda _name: "sk-test")
    created = create_model(
        "openai", "OPENAI_API_KEY", "deepseek-flash", "https://example.invalid/v1", stream=False
    )
    return created.model


def test_disable_thinking_kwargs_shape(openai):
    """扩展点返回 extra_body.thinking.type=disabled，与官方 DeepSeek 逐字同款。"""
    assert openai._get_disable_thinking_kwargs() == {
        "extra_body": {"thinking": {"type": "disabled"}}
    }


def test_openai_base_has_no_thinking_toggle():
    """对照：未覆写的 OpenAI 基类不声明关思考参数（openai 覆写才使 no_think 档生效）。"""
    assert OpenAIChatModel._get_disable_thinking_kwargs(object()) == {}


async def test_plain_400_still_sent_once(openai, monkeypatch):
    """新增扩展点后，与思考模式无关的 400 仍只发一次、原样抛出。"""
    calls = []

    async def fake(_self, model_name, messages, tools=None, tool_choice=None, **kwargs):
        calls.append(kwargs)
        raise RuntimeError("别的 400")

    monkeypatch.setattr(OpenAIChatModel, "_call_api", fake)
    with pytest.raises(RuntimeError, match="别的 400"):
        await openai._call_api("m", [], None, ToolChoice(mode="GenerateStructuredOutput"))
    assert len(calls) == 1