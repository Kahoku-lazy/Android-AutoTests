"""ae_harness 创建出口：显式连接参数、密钥环境变量名透传。

只测 `agents/models.py` 的返回值与 `agents/creator.py` 的透传。
不测提示词内容，也不发任何网络请求（构造模型不联网）。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.agents.models import CreatedModel, create_model, load_secret

pytestmark = [pytest.mark.unit]

_GOVEE = {
    "provider": "govee",
    "api_key_env": "GOVEE_API_KEY",
    "model_name": "deepseek-flash",
    "base_url": "https://test-llm.lanjingerp.com/v1",
}


def test_create_model_returns_model_and_key_name():
    """造模型时顺带交出密钥环境变量名。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    created = create_model(**_GOVEE)
    assert isinstance(created, CreatedModel)
    assert type(created.model).__name__ == "OpenAIChatModel"
    assert created.api_key_env == "GOVEE_API_KEY"


def test_two_configs_give_two_key_names():
    """两套连接参数给出两把不同的密钥名。"""
    if not load_secret("DEEPSEEK_API_KEY"):
        pytest.skip("未配置 DEEPSEEK_API_KEY，跳过需要真实模型构造的用例")
    created = create_model("deepseek", "DEEPSEEK_API_KEY", "deepseek-flash")
    assert created.api_key_env == "DEEPSEEK_API_KEY"


def test_create_model_rejects_mismatched_key():
    """厂商与密钥名不匹配时拒绝，不再按短名查表。"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="DEEPSEEK_API_KEY"):
        create_model("deepseek", "GOVEE_API_KEY", "deepseek-flash")


def test_create_model_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch):
    """密钥没配时拒绝，且报错只含环境变量名。"""
    monkeypatch.setattr("engines.ae_harness.agents.models.load_secret", lambda _name: "")
    with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
        create_model("dashscope", "DASHSCOPE_API_KEY", "qwen-plus")


def test_create_agent_returns_bundle_with_key_name():
    """创建出口返回两段：智能体可运行，密钥名与传入一致。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，跳过需要真实模型构造的用例")
    bundle = create_agent("probe", "你是探针。", **_GOVEE)
    assert isinstance(bundle, AgentBundle)
    assert bundle.agent.name == "probe"
    assert bundle.api_key_env == "GOVEE_API_KEY"


def test_bundle_key_name_has_no_secret():
    """返回值里只有环境变量名，没有密钥明文。"""
    if not load_secret("GOVEE_API_KEY"):
        pytest.skip("未配置 GOVEE_API_KEY，无法断言明文不出现在返回值里")
    bundle = create_agent("probe", "你是探针。", **_GOVEE)
    secret = load_secret("GOVEE_API_KEY")
    assert secret not in bundle.api_key_env
    assert bundle.api_key_env.endswith("_API_KEY")
