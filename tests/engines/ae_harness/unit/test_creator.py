"""ae_harness 创建出口：两段返回、密钥环境变量名透传。

只测 `agents/models.py` 的返回值与 `agents/creator.py` 的透传。
不测提示词内容，也不发任何网络请求（构造模型不联网）。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.config import load_secret
from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.agents.models import CreatedModel, create_model

pytestmark = [pytest.mark.unit]


def test_create_model_returns_model_and_key_name():
    """造模型时顺带交出密钥环境变量名。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    created = create_model("govee_chat_flash")
    assert isinstance(created, CreatedModel)
    assert type(created.model).__name__ == "OpenAIChatModel"
    assert created.api_key_env == "GOVEE_API_KEY"


def test_two_configs_give_two_key_names():
    """两条配置给出两把不同的密钥名。"""
    if not load_secret("DEEPSEEK_API_KEY"):
        pytest.skip("未配置 DEEPSEEK_API_KEY，跳过需要真实模型构造的用例")
    assert create_model("deepseek_chat_flash").api_key_env == "DEEPSEEK_API_KEY"


def test_create_model_rejects_unknown_short_name():
    """未知短名报错，并把可选短名写进消息。"""
    with pytest.raises(ValueError) as excinfo:
        create_model("no_such_model")
    assert "未知模型" in str(excinfo.value)
    assert "govee_chat_flash" in str(excinfo.value)


def test_create_agent_returns_bundle_with_key_name():
    """创建出口返回两段：智能体可运行，密钥名与配置一致。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    bundle = create_agent("probe", "UI_EXECUTOR_PROMPT", "govee_chat_flash")
    assert isinstance(bundle, AgentBundle)
    assert bundle.agent.name == "probe"
    assert bundle.api_key_env == "GOVEE_API_KEY"


def test_bundle_key_name_has_no_secret():
    """返回值里只有环境变量名，没有密钥明文。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，无法断言明文不出现在返回值里")
    bundle = create_agent("probe", "UI_VERIFIER_PROMPT", "govee_chat_flash")
    secret = load_secret("GOVEE_API_KEY")
    assert secret not in bundle.api_key_env
    assert bundle.api_key_env.endswith("_API_KEY")
