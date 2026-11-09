"""角色装配契约：导出清单与实现一致、模型实例复用边界、分段配置严格校验。

对应用 openspec 变更 `agent-role-build-cache-and-guards`。全部用例不联网：
只构造模型对象与角色，不发请求。
"""

from __future__ import annotations

import asyncio

import pytest

from engines.agents import agent_builders
from engines.agents.agent_builders import build_ui_executor, build_ui_verifier
from engines.agents.config import role_loader
from engines.agents.models import clear_chat_model_cache, get_chat_model
from engines.agents.models.chat_model import bind_forced_handover

pytestmark = [pytest.mark.unit]

_EXECUTOR_KEY = "UI_EXECUTOR_ROLE_CONFIG"


@pytest.fixture(autouse=True)
def _isolated_cache(monkeypatch):
    """用替身密钥建模型，并在用例前后清空复用，避免与其它用例互相污染。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-for-role-build-contract")
    clear_chat_model_cache()
    yield
    clear_chat_model_cache()


def _exported(module) -> list[str]:
    """取模块声明的导出清单。"""
    return list(getattr(module, "__all__", []))


def _in_loop(key: str):
    """在同一个事件循环里取两次模型，返回两个实例。"""

    async def _run():
        return get_chat_model(key), get_chat_model(key)

    return asyncio.run(_run())


def _fresh_loop(key: str):
    """在新的事件循环里取一次模型；每次调用都是新循环。"""

    async def _run():
        return get_chat_model(key)

    return asyncio.run(_run())


def test_all_names_exist_in_agent_builders():
    """导出清单里的名字必须都是模块属性（曾列出已删除的 build_case_planner 等）。"""
    missing = [name for name in _exported(agent_builders) if not hasattr(agent_builders, name)]

    assert missing == [], f"__all__ 里有不存在符号：{missing}"


def test_star_import_succeeds():
    """`import *` 是导出清单的最终消费者，它不能抛 AttributeError。"""
    namespace: dict = {}

    exec("from engines.agents.agent_builders import *", namespace)  # noqa: S102

    assert "AgentRoleFactory" in namespace


def test_same_loop_reuses_chat_model():
    """同一循环、同一配置：两次取用是同一个实例。"""
    first, second = _in_loop(_EXECUTOR_KEY)

    assert first is second


def test_new_loop_gets_new_instance():
    """换一个事件循环：不复用先前循环建好的异步客户端。"""
    first = _fresh_loop(_EXECUTOR_KEY)
    second = _fresh_loop(_EXECUTOR_KEY)

    assert first is not second


def test_credential_change_gets_new_instance(monkeypatch):
    """密钥变了就是不同配置，必须新建实例。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "first-key")
    first, _ = _in_loop(_EXECUTOR_KEY)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "second-key")
    second, _ = _in_loop(_EXECUTOR_KEY)

    assert first is not second


def test_clear_cache_rebuilds(monkeypatch):
    """清空复用后重新构造，而不是把旧实例还回来。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-for-role-build-contract")
    first, _ = _in_loop(_EXECUTOR_KEY)
    clear_chat_model_cache()
    second, _ = _in_loop(_EXECUTOR_KEY)

    assert first is not second


def test_two_executor_builds_share_one_model():
    """装配层的实际收益：同一步数内的多个执行者共用一个客户端。"""
    first = build_ui_executor()
    second = build_ui_executor()

    assert first is not second, "Agent 实例必须各自独立"
    assert first.model is second.model, "模型客户端应复用"


def test_same_config_across_roles_shares_client():
    """执行者与验收者的 ModelConfig 完全相同时共用一个客户端，Agent 仍各自独立。"""
    executor = build_ui_executor()
    verifier = build_ui_verifier()

    assert executor is not verifier, "Agent 实例必须各自独立"
    assert executor.model is verifier.model, "连接参数相同就该复用客户端"


def test_different_model_config_gets_own_instance():
    """连接参数不同（纯文本 + 流式）就另建实例，复用不能跨配置串台。"""
    ui_model = build_ui_executor().model
    text_model = get_chat_model("CASE_WRITER_ROLE_CONFIG")

    assert ui_model is not text_model


def test_unknown_section_key_raises(monkeypatch):
    """分段节里写 dataclass 不认识的键：报错并点名。"""

    def fake_section(key: str) -> dict:
        return {
            "RoleConfig": {"name": "probe_role", "system_prompt": "第一行\n第二行"},
            "ReActConfig": {"max_iter": 10},
        }

    monkeypatch.setattr(role_loader, "load_agent_config", fake_section)

    with pytest.raises(ValueError, match="max_iter"):
        role_loader.load_role_spec("PROBE_ROLE_CONFIG")


def test_empty_section_still_uses_defaults(monkeypatch):
    """空节不报错，仍取 dataclass 默认值。"""

    def fake_section(key: str) -> dict:
        return {
            "RoleConfig": {"name": "probe_role", "system_prompt": "第一行\n第二行"},
            "ContextConfig": None,
        }

    monkeypatch.setattr(role_loader, "load_agent_config", fake_section)

    bundle = role_loader.load_role_spec("PROBE_ROLE_CONFIG")

    assert bundle.react.max_iters == 30


def test_bind_forced_handover_is_idempotent():
    """共享实例被反复交给装配层时，强制交卷改写只挂一次。"""
    model = _fresh_loop(_EXECUTOR_KEY)
    bound_once = bind_forced_handover(model)
    call_api = bound_once._call_api

    bound_twice = bind_forced_handover(model)

    assert bound_twice is bound_once
    assert bound_twice._call_api is call_api
