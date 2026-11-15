"""assistant 创建层：传表创建、按族分派、只创建不使用。不联网。

另含构造落点守卫：engines/agents 下 Agent( / RealtimeAgent( 只允许出现在 assistant/。
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from agentscope.agent import Agent
from agentscope.tool import Toolkit

from engines.agents.assistant import AgentConfigError, create_chat_agent, create_voice_agent

pytestmark = [pytest.mark.unit]


class _Key:
    """测试用密钥：只提供 reveal，不碰环境变量。"""

    def reveal(self) -> str:
        """返回固定明文。"""
        return "test-key"


def _chat(name: str = "deepseek-flash") -> dict:
    """一条最小聊天模型条目。"""
    return {
        "family": "chat",
        "provider": "deepseek",
        "model_name": name,
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key": _Key(),
        "input_types": ["text/plain"],
    }


def _realtime() -> dict:
    """一条最小实时语音模型条目。"""
    return {
        "family": "realtime",
        "provider": "dashscope",
        "model_name": "qwen3.5-omni-plus-realtime",
        "api_key_env": "DASHSCOPE_API_KEY",
        "api_key": _Key(),
        "voice": "Tina",
    }


def _embedding() -> dict:
    """一条向量模型条目，用来验证拒绝非 chat / realtime。"""
    return {
        "family": "embedding",
        "provider": "dashscope",
        "model_name": "text-embedding-v4",
        "api_key_env": "DASHSCOPE_API_KEY",
        "api_key": _Key(),
        "dimensions": 1024,
    }


def _role(model: str, *, prompt: str = "你是助手。", name: str = "probe") -> dict:
    """一个最小角色节。"""
    return {
        "ModelConfig": {"model": model, "stream": False},
        "RoleConfig": {"name": name, "system_prompt": prompt},
        "ReActConfig": {"max_iters": 8},
    }


def _tts() -> dict:
    """一条语音合成模型条目，用来验证助手出口拒绝 tts。"""
    return {
        "family": "tts",
        "provider": "dashscope",
        "model_name": "qwen3-tts-flash",
        "api_key_env": "DASHSCOPE_API_KEY",
        "api_key": _Key(),
        "voice": "Tina",
    }


def test_chat_role_returns_agent() -> None:
    """聊天短名造出 Agent，名字和提示词来自角色节。"""
    roles = {"UI_EXECUTOR_ROLE_CONFIG": _role("deepseek_flash", name="ui_executor_role")}
    agent = create_chat_agent(roles, {"deepseek_flash": _chat()}, "UI_EXECUTOR_ROLE_CONFIG", middlewares=[])

    assert isinstance(agent, Agent)
    assert agent.name == "ui_executor_role"
    assert agent.model.model == "deepseek-flash"


def test_realtime_role_returns_realtime_agent() -> None:
    """实时语音短名造出 RealtimeAgent，而不是聊天 Agent。"""
    from agentscope.agent import RealtimeAgent

    roles = {"OMNI_ROLE_CONFIG": _role("omni", name="realtime_vocie_agent")}
    agent = create_voice_agent(roles, {"omni": _realtime()}, "OMNI_ROLE_CONFIG")

    assert isinstance(agent, RealtimeAgent)
    assert not isinstance(agent, Agent)
    assert agent.name == "realtime_vocie_agent"


def test_chat_exit_rejects_other_families() -> None:
    """聊天出口拒绝 realtime / embedding / tts，错误带角色键和实际族。"""
    roles = {
        "VOICE": _role("omni"),
        "EMBED": _role("embed"),
        "TTS": _role("speak"),
    }
    models = {"omni": _realtime(), "embed": _embedding(), "speak": _tts()}

    for key, family in (("VOICE", "realtime"), ("EMBED", "embedding"), ("TTS", "tts")):
        with pytest.raises(AgentConfigError, match=key) as caught:
            create_chat_agent(roles, models, key, middlewares=[])
        assert family in str(caught.value)


def test_voice_exit_rejects_other_families() -> None:
    """语音出口拒绝 chat / embedding / tts，错误带角色键和实际族。"""
    roles = {
        "CHAT": _role("deepseek_flash"),
        "EMBED": _role("embed"),
        "TTS": _role("speak"),
    }
    models = {"deepseek_flash": _chat(), "embed": _embedding(), "speak": _tts()}

    for key, family in (("CHAT", "chat"), ("EMBED", "embedding"), ("TTS", "tts")):
        with pytest.raises(AgentConfigError, match=key) as caught:
            create_voice_agent(roles, models, key)
        assert family in str(caught.value)


def test_voice_exit_rejects_chat_only_arguments() -> None:
    """语音出口收到上下文、ReAct、中间件或流式开关时拒绝，不静默丢弃。"""
    roles = {"OMNI_ROLE_CONFIG": _role("omni")}
    models = {"omni": _realtime()}

    with pytest.raises(AgentConfigError, match="middlewares"):
        create_voice_agent(roles, models, "OMNI_ROLE_CONFIG", middlewares=[])
    with pytest.raises(AgentConfigError, match="stream"):
        create_voice_agent(roles, models, "OMNI_ROLE_CONFIG", stream=False)


def test_unknown_role_lists_choices() -> None:
    """未知角色键报错，并列出表里已有的键。"""
    roles = {"UI_EXECUTOR_ROLE_CONFIG": _role("deepseek_flash")}

    with pytest.raises(AgentConfigError, match="UI_EXECUTOR_ROLE_CONFIG"):
        create_chat_agent(roles, {}, "NO_SUCH_ROLE")


def test_missing_name_mentions_role_key() -> None:
    """缺名字时错误定位到角色键。"""
    roles = {"PROBE": {"ModelConfig": {"model": "deepseek_flash"}, "RoleConfig": {"system_prompt": "x"}}}

    with pytest.raises(AgentConfigError, match="PROBE"):
        create_chat_agent(roles, {}, "PROBE")


def test_connection_params_are_rejected() -> None:
    """角色节写 provider / api_key 直接拒绝，不把连接参数带进 Agent。"""
    roles = {
        "PROBE": {
            "ModelConfig": {"model": "deepseek_flash", "api_key": "sk-leak"},
            "RoleConfig": {"name": "probe", "system_prompt": "x"},
        }
    }

    with pytest.raises(AgentConfigError, match="api_key"):
        create_chat_agent(roles, {}, "PROBE")


def test_empty_toolkit_when_caller_omits_it() -> None:
    """不传工具包时聊天角色是空包，不硬编码设备工具。"""
    roles = {"PROBE": _role("deepseek_flash")}
    agent = create_chat_agent(roles, {"deepseek_flash": _chat()}, "PROBE", middlewares=[])

    basic = next(group for group in agent.toolkit.tool_groups if group.name == "basic")
    assert basic.tools == []


def test_caller_toolkit_is_used() -> None:
    """调用方传入的工具包成为该实例的工具包。"""

    def ping() -> str:
        """无操作。"""
        return "pong"

    toolkit = Toolkit(tools=[ping])
    roles = {"PROBE": _role("deepseek_flash")}
    agent = create_chat_agent(roles, {"deepseek_flash": _chat()}, "PROBE", toolkit=toolkit, middlewares=[])

    assert agent.toolkit is toolkit


def test_prompt_and_name_override() -> None:
    """覆盖参数优先于角色节，供会话侧追加提示词。"""
    roles = {"OMNI_ROLE_CONFIG": _role("omni", prompt="原文", name="yaml-name")}
    agent = create_voice_agent(
        roles,
        {"omni": _realtime()},
        "OMNI_ROLE_CONFIG",
        system_prompt="原文\n先检索再回答",
        name="session-name",
    )

    assert agent.name == "session-name"
    assert "先检索再回答" in agent.system_prompt


def test_each_call_returns_a_new_instance() -> None:
    """连续创建两次是不同实例，创建过程不产生回复。"""
    roles = {"PROBE": _role("deepseek_flash")}
    models = {"deepseek_flash": _chat()}
    first = create_chat_agent(roles, models, "PROBE", middlewares=[])
    second = create_chat_agent(roles, models, "PROBE", middlewares=[])

    assert first is not second
    assert first.state is not second.state


def test_agent_construction_stays_in_assistant() -> None:
    """Agent( 与 RealtimeAgent( 不得出现在 assistant 之外。"""
    root = pathlib.Path(__file__).resolve().parents[4] / "engines" / "agents"
    files = sorted(root.rglob("*.py"))
    assert len(files) >= 20, f"扫描量异常（{len(files)}），识别可能失效"
    hits: list[str] = []
    for path in files:
        if "assistant" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else ""
            if name in {"Agent", "RealtimeAgent"}:
                hits.append(f"{path.relative_to(root.parents[1])}:{node.lineno} {name}")
    assert hits == [], "构造必须收进 assistant：\n" + "\n".join(hits)
