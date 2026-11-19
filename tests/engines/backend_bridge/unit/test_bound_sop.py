"""名片绑定 SOP 的运行入口：有 serial 才追加开场，且不读步骤键。"""

from __future__ import annotations

import pytest

from engines.ae_harness.workflow.sop import SopSpec, StepSpec
from engines.backend_bridge.workflow import RoleBinding, run_bound_sop
from engines.backend_bridge.workflow import bound_sop as bound_sop_module

pytestmark = [pytest.mark.unit]


def _binding(name: str, model: str) -> RoleBinding:
    return RoleBinding(
        run_name=name,
        system_prompt=f"{name} 的提示词",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=model,
    )


def _spec() -> SopSpec:
    return SopSpec(
        name="检查桌面", steps=[StepSpec(subject="回到桌面", description="停在桌面")], task="看桌面"
    )


def test_runner_source_does_not_read_spec_keys():
    """新运行函数不调用步骤键表。"""
    source = bound_sop_module.run_bound_sop.__module__
    text = open(bound_sop_module.__file__, encoding="utf-8").read()

    assert source.endswith("bound_sop")
    assert "SPEC_KEYS" not in text


async def test_serial_is_appended_only_when_present(monkeypatch):
    """有 serial 才追加开场模板；没有时任务描述保持原样。"""
    seen: dict[str, str] = {}

    async def fake_run_sop(*args, **kwargs):
        seen["task"] = args[2].task
        seen["models"] = kwargs["role_models"]

        class _Result:
            phase = "done"
            steps = []
            record = None

        return _Result()

    async def fake_build(executor, verifier, **kwargs):
        def bundle(name: str, key: str):
            return type(
                "Bundle", (), {"agent": type("Agent", (), {"name": name})(), "api_key_env": key}
            )()

        return type(
            "Roles",
            (),
            {
                "executor": bundle(executor.run_name, executor.api_key_env),
                "verifier": bundle(verifier.run_name, verifier.api_key_env),
                "observer": type("Observer", (), {"records": []})(),
            },
        )()

    monkeypatch.setattr(bound_sop_module, "run_sop", fake_run_sop)
    monkeypatch.setattr(bound_sop_module, "build_bound_roles", fake_build)
    monkeypatch.setattr(bound_sop_module, "cancel_controls", lambda task_id: [])

    plain = _spec()
    await run_bound_sop(
        plain, _binding("执行", "deepseek-flash"), _binding("验收", "deepseek-v4-pro")
    )
    assert seen["task"] == "看桌面"

    with_serial = _spec()
    await run_bound_sop(
        with_serial,
        _binding("执行", "deepseek-flash"),
        _binding("验收", "deepseek-v4-pro"),
        serial="ABC123",
    )
    assert "ABC123" in seen["task"]
    assert seen["models"] == {"执行": "deepseek-flash", "验收": "deepseek-v4-pro"}
