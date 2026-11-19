"""模型层重试分层契约：默认 1 次、显式配置透传（agent-model-resilience 分层需求）。

monkeypatch 密钥取值，构造模型不联网；守护「模型层 × 中间件」最坏次数有界。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.agents.models import create_model

pytestmark = [pytest.mark.unit]

_PROVIDERS = [
    ("deepseek", "DEEPSEEK_API_KEY", "deepseek-flash", ""),
    ("dashscope", "DASHSCOPE_API_KEY", "qwen-plus", ""),
    ("openai", "OPENAI_API_KEY", "deepseek-flash", "https://gateway.example/v1"),
]


@pytest.fixture(autouse=True)
def _fake_secret(monkeypatch: pytest.MonkeyPatch):
    """用假密钥构造模型，不依赖本机 .env，也不发网络请求。"""
    monkeypatch.setattr(
        "engines.ae_harness.agents.models.load_secret", lambda _name: "unit-test-key"
    )


@pytest.mark.parametrize(("provider", "key_env", "model_name", "url"), _PROVIDERS)
def test_default_max_retries_is_one(provider, key_env, model_name, url):
    """不显式配置时，三家模型的内置重试次数都是 1（最多尝试 2 次）。"""
    created = create_model(provider, key_env, model_name, url)
    assert created.model.max_retries == 1


@pytest.mark.parametrize(("provider", "key_env", "model_name", "url"), _PROVIDERS)
def test_explicit_zero_disables_model_retry(provider, key_env, model_name, url):
    """显式传 0 时模型层不再重试，瞬态故障全部交给可靠性中间件。"""
    created = create_model(provider, key_env, model_name, url, max_retries=0)
    assert created.model.max_retries == 0


def test_explicit_value_passes_through():
    """显式传其它值时原样透传给模型构造器。"""
    created = create_model(
        "openai", "OPENAI_API_KEY", "deepseek-flash", "https://gateway.example/v1", max_retries=2
    )
    assert created.model.max_retries == 2