"""连通性：engines.agents.agent_builders 按 YAML 创建 Agent 并能拿到一轮回复。

有回复 → Agent 装配 OK；无回复 / 抛错 → 失败。

不依赖 Django。密钥从仓库根 .env 或环境变量读取。

单文件：
    python -m pytest tests/engines/agents/test_agents.py -vv -s --tb=short
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentscope.message import UserMsg

from engines.agents.agent_builders import AgentRoleFactory
from engines.agents.config.role_loader import load_role_spec
from engines.agents.models import get_chat_model

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except ImportError:
    pass

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def _create_from_spec(role_key: str) -> object:
    bundle = load_role_spec(role_key)
    return AgentRoleFactory(
        get_chat_model(role_key),
        bundle.role,
        tools=bundle.tools,
        context=bundle.context,
        react=bundle.react,
        middlewares=[],
    ).create()


async def _assert_agent_replies(label: str, agent) -> None:
    """向 Agent 发一句短问；有非空 content 视为通断成功。"""
    msgs = [UserMsg(name="user", content="Reply with exactly one word: pong")]
    response = await agent.reply(msgs)
    content = getattr(response, "content", None)
    assert response is not None, f"{label}: 无响应对象"
    assert content, f"{label}: 无回复内容（配置或连通失败）: {response!r}"
    print(f"[{label}] reply={content!r}")


@pytest.mark.asyncio
async def test_executor_agent_connectivity() -> None:
    """执行 Agent：UI_EXECUTOR_ROLE_CONFIG 能建 Agent 并返回内容。"""
    agent = _create_from_spec("UI_EXECUTOR_ROLE_CONFIG")
    await _assert_agent_replies("executor_agent", agent)


@pytest.mark.asyncio
async def test_verifier_agent_connectivity() -> None:
    """验收 Agent：UI_VERIFIER_ROLE_CONFIG 能建 Agent 并返回内容。"""
    agent = _create_from_spec("UI_VERIFIER_ROLE_CONFIG")
    await _assert_agent_replies("verifier_agent", agent)
