"""连通性：engines.agents.config.models 按 YAML 配置真正打通模型并拿到回复。

有回复 → 配置 OK；无回复 / 抛错 → 失败。

不依赖 Django（本文件不 import django）。密钥从仓库根 .env 或环境变量读取。

单文件：
    python -m pytest tests/engines/agents/test_models.py -vv -s --tb=short
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentscope.message import UserMsg

from engines.agents.config.models import executor_model, verifier_model

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except ImportError:
    pass

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


async def _assert_model_replies(factory_name: str, factory) -> None:
    """调用模型；有非空 content 视为配置连通成功。"""
    chat = factory().create()
    msgs = [UserMsg(name="user", content="Reply with exactly one word: pong")]
    response = await chat(msgs)
    content = getattr(response, "content", None)
    assert response is not None, f"{factory_name}: 无响应对象"
    assert content, f"{factory_name}: 无回复内容（配置或连通失败）: {response!r}"
    print(f"[{factory_name}] reply={content!r}")


@pytest.mark.asyncio
async def test_executor_model_connectivity() -> None:
    """executor 模型：能按 UI_EXECUTOR_ROLE_CONFIG 打通并返回内容。"""
    await _assert_model_replies("executor_model", executor_model)


@pytest.mark.asyncio
async def test_verifier_model_connectivity() -> None:
    """verifier 模型：能按 UI_VERIFIER_ROLE_CONFIG 打通并返回内容。"""
    await _assert_model_replies("verifier_model", verifier_model)