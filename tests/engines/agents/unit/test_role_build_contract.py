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
from engines.agents.assistant import clear_chat_model_cache


pytestmark = [pytest.mark.unit]

_EXECUTOR_MODEL = "deepseek_flash"


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


def _executor():
    """装配一个执行角色，返回它的聊天模型。"""
    return build_ui_executor().model


def test_all_names_exist_in_agent_builders():
    """导出清单里的名字必须都是模块属性（曾列出已删除的 build_case_planner 等）。"""
    missing = [name for name in _exported(agent_builders) if not hasattr(agent_builders, name)]

    assert missing == [], f"__all__ 里有不存在符号：{missing}"


def test_star_import_succeeds():
    """`import *` 是导出清单的最终消费者，它不能抛 AttributeError。"""
    namespace: dict = {}

    exec("from engines.agents.agent_builders import *", namespace)  # noqa: S102

    assert "AgentRoleFactory" in namespace


def test_same_short_name_reuses_chat_model():
    """同一短名、同一流式开关：两次装配拿到同一个聊天模型。"""
    assert _executor() is _executor()


def test_new_loop_reuses_same_stream_model():
    """聊天模型按短名与流式开关复用，不按事件循环拆分。"""
    async def _run():
        return _executor()

    first = asyncio.run(_run())
    second = asyncio.run(_run())

    assert first is second


def test_cache_does_not_reread_secret(monkeypatch):
    """密钥在装载时注入；缓存命中后不再因为环境变量变化而新建。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "first-key")
    first = _executor()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "second-key")
    second = _executor()

    assert first is second


def test_clear_cache_rebuilds(monkeypatch):
    """清空复用后重新构造，而不是把旧实例还回来。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-for-role-build-contract")
    first = _executor()
    clear_chat_model_cache()
    second = _executor()

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


def test_executor_model_matches_role_short_name():
    """执行角色拿到的是角色节短名对应的正式模型名，不另造一套客户端。"""
    from engines.agents.config.config import load_model_config
    from engines.agents.config.model_view import model_view

    agent = build_ui_executor()

    assert agent.model.model == model_view(load_model_config(), _EXECUTOR_MODEL).model_name


def test_unknown_section_key_raises(monkeypatch):
    """分段节里写 dataclass 不认识的键：报错并点名。"""

    def fake_section(path: str | None = None) -> dict:
        return {
            "PROBE_ROLE_CONFIG": {
                "ModelConfig": {"model": _EXECUTOR_MODEL, "stream": False},
                "RoleConfig": {"name": "probe_role", "system_prompt": "第一行\n第二行"},
                "ReActConfig": {"max_iter": 10},
            }
        }

    monkeypatch.setattr(role_loader, "load_agent_config", fake_section)

    with pytest.raises(ValueError, match="max_iter"):
        role_loader.load_role_spec("PROBE_ROLE_CONFIG")


def test_empty_section_still_uses_defaults(monkeypatch):
    """空节不报错，仍取 dataclass 默认值。"""

    def fake_section(path: str | None = None) -> dict:
        return {
            "PROBE_ROLE_CONFIG": {
                "ModelConfig": {"model": _EXECUTOR_MODEL, "stream": False},
                "RoleConfig": {"name": "probe_role", "system_prompt": "第一行\n第二行"},
                "ContextConfig": None,
            }
        }

    monkeypatch.setattr(role_loader, "load_agent_config", fake_section)

    bundle = role_loader.load_role_spec("PROBE_ROLE_CONFIG")

    assert bundle.react.max_iters == 30


def test_handover_middleware_does_not_wrap_shared_model():
    """两次装配共用同一聊天模型，交卷中间件不另造客户端。"""
    first = _executor()
    second = _executor()

    assert first is second
    assert type(first).__name__ == "DeepSeekChatModel"
