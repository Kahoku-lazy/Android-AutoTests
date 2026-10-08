"""灰盒·单元测试 — 模型调试台 / model_test 共用的三角色装配入口。

守的是**真实装配**这条链路：本用例刻意**不打桩被测函数本身**，只用桩 agent 调真实的
`model_debug.build_device_models_for_agent`，因此装配链上任何一环名字悬空或签名漂移都会失败。

历史缺陷（本用例的由来）：该函数调用了未导入的 `build_device_models`，而旧用例把这个装配函数
整体打桩，真实路径从未被执行 —— 缺陷从 `f823a6a7` 起潜伏，直到手工跑 `model_test` 才暴露。
"""

from types import SimpleNamespace

import pytest

from apps.ai_assistant import model_debug
from engines.ai.agents import DeviceExecutionConfig, ExecutorRole, PlannerRole, VerifierRole

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def _stub_agent():
    """桩 agent：只提供装配函数实际读取的四个属性。"""
    return SimpleNamespace(
        route_configs={
            "device_control": {
                "planner": {
                    "provider": "deepseek",
                    "model_name": "stub-planner",
                    "api_key": "k1",
                },
                "executor": {
                    "provider": "deepseek",
                    "model_name": "stub-executor",
                    "api_key": "k2",
                },
                "verifier": {
                    "provider": "deepseek",
                    "model_name": "stub-verifier",
                    "api_key": "k3",
                },
            }
        },
        max_loops=2,
        owner_id=7,
        enable_skills=False,
    )


@pytest.fixture
def stub_externals(monkeypatch):
    """只对两处**外部依赖**打桩：密钥解密（免加密格式）与技能目录（免磁盘/DB）。

    被测函数本身、工具装配（build_tool_specs）与角色构造都走真实实现。
    """
    monkeypatch.setattr(model_debug, "decrypt_key", lambda raw: f"plain::{raw}")
    monkeypatch.setattr(model_debug, "list_enabled_skill_dirs", lambda: [])


def test_assembly_entry_builds_config_and_three_roles(stub_externals):
    """装配入口必须能真跑通，产出「1 份三角色配置 + 3 个角色对象」。"""
    config, planner, executor, verifier = model_debug.build_device_models_for_agent(_stub_agent())

    assert isinstance(config, DeviceExecutionConfig)
    assert config.max_loops == 2
    assert [
        config.planner.model_name,
        config.executor.model_name,
        config.verifier.model_name,
    ] == ["stub-planner", "stub-executor", "stub-verifier"]
    assert [config.planner.api_key, config.executor.api_key, config.verifier.api_key] == [
        "plain::k1",
        "plain::k2",
        "plain::k3",
    ]

    assert isinstance(planner, PlannerRole)
    assert isinstance(executor, ExecutorRole)
    assert isinstance(verifier, VerifierRole)


def test_assembly_entry_keeps_role_recipes(stub_externals):
    """三个角色对象的配方与生产规格同源（角色名 / 视觉标记）。"""
    _config, planner, executor, verifier = model_debug.build_device_models_for_agent(_stub_agent())

    assert (planner.spec.role, planner.spec.vision) == ("planner", False)
    assert (executor.spec.role, executor.spec.vision) == ("executor", True)
    assert (verifier.spec.role, verifier.spec.vision) == ("verifier", True)
