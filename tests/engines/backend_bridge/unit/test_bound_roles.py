"""名片绑定的 SOP 角色装配：不传短名，验收侧只留只读交集。"""

from __future__ import annotations

import inspect

import pytest

from engines.ae_harness.agents.models import load_secret
from engines.backend_bridge.workflow import RoleBinding, build_bound_roles
from engines.backend_bridge.workflow import bound_roles as bound_roles_module

pytestmark = [pytest.mark.unit]

WRITE_TOOL_HINTS = ("tap", "swipe", "input_text", "install", "uninstall")


def _needs_key() -> None:
    """没有密钥时跳过需要真实模型构造的用例。"""
    if not load_secret("DEEPSEEK_API_KEY"):
        pytest.skip("未配置 DEEPSEEK_API_KEY，跳过需要真实模型构造的用例")


def _binding(name: str, tools: tuple[dict, ...] = ()) -> RoleBinding:
    return RoleBinding(
        run_name=name,
        system_prompt=f"{name} 的提示词",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
        tools=tools,
    )


def test_new_builder_source_has_no_short_name_or_prompt_file():
    """新函数源码不传模型短名，也不引用旧提示词文件名。"""
    source = inspect.getsource(bound_roles_module)

    assert "model_short" not in source
    assert "UI_EXECUTOR_PROMPT" not in source
    assert "UI_VERIFIER_PROMPT" not in source


async def test_verifier_drops_write_tools():
    """验收勾选里的写工具不会挂到验收实例上。"""
    _needs_key()
    tools = ({"domain": "adb", "preset": "readonly", "add": ["adb_tap"], "remove": []},)
    roles = await build_bound_roles(_binding("执行"), _binding("验收", tools))
    schemas = await roles.verifier.agent.toolkit.get_tool_schemas()
    names = [item["function"]["name"] for item in schemas]

    assert names
    offenders = [name for name in names if any(hint in name for hint in WRITE_TOOL_HINTS)]
    assert not offenders


async def test_unknown_tool_name_is_rejected():
    """未知工具名在装配时拒绝。"""
    _needs_key()
    tools = ({"domain": "adb", "preset": "all", "add": ["not_a_tool"], "remove": []},)

    with pytest.raises(ValueError, match="未知工具"):
        await build_bound_roles(_binding("执行", tools), _binding("验收"))
