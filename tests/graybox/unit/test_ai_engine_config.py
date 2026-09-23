"""装配期配置 fail-fast 与 provider 单一真相源（spec: ai-engine-protocol delta）。

覆盖 spec 的 7 个 Scenario：
  装配期配置 fail-fast
    - 三角色配置缺失            → test_missing_role_raises / test_missing_route_raises
    - 模型名或密钥为空          → test_blank_model_name_raises / test_blank_api_key_raises
                                  / test_undecryptable_api_key_raises
    - 无可用设备                → test_no_device_raises（正向：test_task_device_serial_wins
                                  / test_online_device_fallback）
  provider 配置单一真相源
    - 未知 provider 在装配阶段被拒 → test_unknown_provider_rejected_at_assembly
    - 自定义 base_url 必须生效    → test_dashscope_credential_keeps_base_url
                                   / test_dashscope_empty_base_url_uses_default
    - 兜底分支不再吸收未知 provider → test_create_model_rejects_unknown_provider
    - 两侧 provider 集合一致      → test_supported_providers_match_valid_providers
附加（3.3）：test_all_supported_providers_construct / test_deepseek_vision_constructs
"""

from types import SimpleNamespace

import pytest

from apps.ai_assistant import api, engine_adapter
from apps.ai_assistant.provider_registry import VALID_PROVIDERS
from engines.ai.agentscope.config import ModelConfig
from engines.ai.agentscope.model import (
    OPENAI_COMPATIBLE_PROVIDERS,
    SUPPORTED_PROVIDERS,
    create_model,
)
from engines.ai.registry import ConfigurationError

pytestmark = [pytest.mark.unit]

_EXAMPLE_BASE_URL = "https://llm.example.com/v1"


def _role_cfg(
    model_name: str = "deepseek-v4-flash",
    provider: str = "deepseek",
    api_key: str | None = None,
    base_url: str = "",
) -> dict:
    """单个角色的线路配置；api_key 默认现加密成合法密文，传值则原样使用。"""
    return {
        "provider": provider,
        "model_name": model_name,
        "api_key": api.encrypt_key("sk-test") if api_key is None else api_key,
        "base_url": base_url,
    }


def _route_configs(**overrides) -> dict:
    """三角色齐全的 device_control 线路，按角色名覆盖。"""
    roles = {role: _role_cfg() for role in engine_adapter.ROUTE_ROLES}
    roles.update(overrides)
    return {engine_adapter.ROUTE_KEY: roles}


def _agent(**overrides) -> SimpleNamespace:
    fields = {
        "route_configs": _route_configs(),
        "max_loops": 3,
        "owner_id": "1",
        "enable_skills": False,
        "prompt_planner": "## planner prompt",
        "prompt_executor": "## executor prompt",
        "prompt_verifier": "## verifier prompt",
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _task(device_serial: str = "SERIAL-1") -> SimpleNamespace:
    return SimpleNamespace(
        device_serial=device_serial,
        title="打开应用",
        goal="打开应用",
        attachment="",
        id=7,
    )


# ── 装配期配置 fail-fast ──


@pytest.mark.parametrize("missing_role", engine_adapter.ROUTE_ROLES)
def test_missing_role_raises(missing_role):
    """缺任意一个角色 → 装配期报错并指明角色名。"""
    route_configs = _route_configs()
    del route_configs[engine_adapter.ROUTE_KEY][missing_role]

    with pytest.raises(ValueError, match=missing_role):
        engine_adapter.build_request(_task(), _agent(route_configs=route_configs))


def test_missing_route_raises():
    """整条 device_control 线路缺失 → 装配期报错。"""
    with pytest.raises(ValueError, match="planner"):
        engine_adapter.build_request(_task(), _agent(route_configs={}))


def test_blank_model_name_raises():
    route_configs = _route_configs(executor=_role_cfg(model_name="  "))

    with pytest.raises(ValueError, match="executor"):
        engine_adapter.build_request(_task(), _agent(route_configs=route_configs))


def test_blank_api_key_raises():
    route_configs = _route_configs(verifier=_role_cfg(api_key=""))

    with pytest.raises(ValueError, match="verifier"):
        engine_adapter.build_request(_task(), _agent(route_configs=route_configs))


def test_undecryptable_api_key_raises():
    """密文无法解密（decrypt_key 返回空串）→ 同样按空密钥报错。"""
    route_configs = _route_configs(planner=_role_cfg(api_key="not-a-fernet-token"))

    with pytest.raises(ValueError, match="planner"):
        engine_adapter.build_request(_task(), _agent(route_configs=route_configs))


def test_no_device_raises(monkeypatch):
    """任务没给 serial 且无在线设备 → 装配期报错，不传空串。"""
    monkeypatch.setattr("apps.device_pool.api.get_online_devices", lambda: [])

    with pytest.raises(ValueError, match="无可用设备"):
        engine_adapter.build_request(_task(device_serial=""), _agent())


def test_task_device_serial_wins(monkeypatch):
    """任务显式指定 serial 时不再查询在线设备。"""

    def _unexpected_call():
        raise AssertionError("任务已指定 serial，不应查询在线设备")

    monkeypatch.setattr("apps.device_pool.api.get_online_devices", _unexpected_call)

    req = engine_adapter.build_request(_task(device_serial="SERIAL-X"), _agent())

    assert req.device_serial == "SERIAL-X"


def test_online_device_fallback(monkeypatch):
    """任务未指定 serial 时取第一台在线设备。"""
    monkeypatch.setattr(
        "apps.device_pool.api.get_online_devices",
        lambda: [SimpleNamespace(serial="ONLINE-1")],
    )

    req = engine_adapter.build_request(_task(device_serial=""), _agent())

    assert req.device_serial == "ONLINE-1"


def test_blank_system_prompt_raises():
    """某角色系统提示词为空 → 装配期报错并指明角色。"""
    with pytest.raises(ValueError, match="executor"):
        engine_adapter.build_request(_task(), _agent(prompt_executor="   "))


def test_system_prompts_injected():
    """库中提示词进入 TaskRequest.system_prompts。"""
    req = engine_adapter.build_request(_task(), _agent())
    assert req.system_prompts == {
        "planner": "## planner prompt",
        "executor": "## executor prompt",
        "verifier": "## verifier prompt",
    }


# ── provider 配置单一真相源 ──


def test_unknown_provider_rejected_at_assembly():
    """未知 provider → 装配期报错，文案含该 provider 与合法集合。"""
    route_configs = _route_configs(planner=_role_cfg(provider="kimi"))

    with pytest.raises(ValueError) as excinfo:
        engine_adapter.build_request(_task(), _agent(route_configs=route_configs))

    message = str(excinfo.value)
    assert "kimi" in message
    for provider in VALID_PROVIDERS:
        assert provider in message, f"合法集合 {provider} 未出现在错误文案中"


def _capture_chat_model(monkeypatch, name: str) -> dict:
    """把 create_model 用到的 ChatModel 类换成入参捕获器。"""
    captured: dict = {}

    class _FakeChatModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(f"engines.ai.agentscope.model.{name}", _FakeChatModel)
    return captured


def test_dashscope_credential_keeps_base_url(monkeypatch):
    """dashscope 分支必须把解析出的 base_url 传给凭证，不得丢弃。"""
    captured = _capture_chat_model(monkeypatch, "DashScopeChatModel")
    config = ModelConfig(
        provider="dashscope",
        model_name="qwen3.6-plus",
        api_key="sk-test",
        base_url=_EXAMPLE_BASE_URL,
    )

    create_model(config, stream=False)

    assert captured["credential"].base_url == _EXAMPLE_BASE_URL


def test_dashscope_empty_base_url_uses_default(monkeypatch):
    """base_url 为空时交给框架默认端点，不用空串覆盖。"""
    captured = _capture_chat_model(monkeypatch, "DashScopeChatModel")
    config = ModelConfig(provider="dashscope", model_name="qwen3.6-plus", api_key="sk-test")

    create_model(config, stream=False)

    assert "dashscope.aliyuncs.com" in captured["credential"].base_url


def test_create_model_rejects_unknown_provider():
    """兜底分支不再吸收未知 provider。"""
    config = ModelConfig(
        provider="kimi",
        model_name="kimi-k2",
        api_key="sk-test",
        base_url=_EXAMPLE_BASE_URL,
    )

    with pytest.raises(ConfigurationError, match="kimi"):
        create_model(config, stream=False)


def test_supported_providers_match_valid_providers():
    """引擎可处理的 provider 集合必须与 Django 侧合法集合完全相等。"""
    assert set(SUPPORTED_PROVIDERS) == set(VALID_PROVIDERS)


def test_openai_compatible_providers_are_supported():
    """OpenAI 兼容白名单是 SUPPORTED_PROVIDERS 的子集（防止常量自相矛盾）。"""
    assert OPENAI_COMPATIBLE_PROVIDERS <= SUPPORTED_PROVIDERS


@pytest.mark.parametrize("provider", sorted(SUPPORTED_PROVIDERS))
def test_all_supported_providers_construct(provider):
    """六个合法 provider 均可构造模型连接。"""
    config = ModelConfig(
        provider=provider,
        model_name="some-model",
        api_key="sk-test",
        base_url=_EXAMPLE_BASE_URL,
    )

    assert create_model(config, stream=False) is not None


def test_deepseek_vision_constructs():
    """deepseek 多模态分支（OpenAI 兼容 + thinking）可构造。"""
    config = ModelConfig(
        provider="deepseek",
        model_name="deepseek-v4-flash-vision-exp",
        api_key="sk-test",
        base_url=_EXAMPLE_BASE_URL,
    )

    assert create_model(config, stream=False, vision=True) is not None
