"""评测探针：同一实例、一次通过、驳回后再通过、验收者写操作。"""

from __future__ import annotations

import pytest

from engines.backend_bridge.workflow.eval_probe import play_script, probe_same_instance

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

SELECTION = [{"domain": "adb", "preset": "all", "add": [], "remove": []}]


async def test_probe_second_turn_uses_same_instance(monkeypatch):
    class _Agent:
        name = "probe"

    class _Bundle:
        agent = _Agent()
        api_key_env = "DEEPSEEK_API_KEY"

    monkeypatch.setattr(
        "engines.backend_bridge.workflow.eval_probe.build_card_agent",
        lambda **_kwargs: _await(_Bundle()),
    )

    async def reply(agent, text):
        return f"{id(agent)}:{text}", {"round": text}

    result = await probe_same_instance(
        reply,
        name="probe",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="m",
        system_prompt="你好",
    )

    assert result["same_instance"] is True
    assert result["steps"][1]["text"].endswith("你好")
    assert result["steps"][3]["text"].endswith("上一句我说了什么")


async def test_script_pass_once_then_reject_once_then_verifier_write():
    once = await play_script(
        SELECTION, [{"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}}]
    )
    retried = await play_script(
        SELECTION,
        [
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}},
            {"role": "verifier", "tool": "adb_dump_ui", "input": {}},
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 0.5, "ny": 0.9}},
        ],
    )
    provoked = await play_script(
        SELECTION, [{"role": "verifier", "tool": "adb_tap", "input": {"nx": 0.1, "ny": 0.1}}]
    )

    assert once[0]["text"] == "adb_tap"
    assert [item["role"] for item in retried] == ["executor", "verifier", "executor"]
    assert provoked[0]["text"] == "未挂载"


async def _await(value):
    return value
