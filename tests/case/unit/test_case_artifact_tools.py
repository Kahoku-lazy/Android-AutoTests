"""产物增量工具：只回条数不回正文，验收侧只读。"""

from __future__ import annotations

import asyncio
import json

from engines.agents.tools.tool_case_artifact import (
    build_artifact_store_tools,
    build_verifier_artifact_tools,
    build_writer_artifact_tools,
)
from engines.agents.workflow.case_artifact import ArtifactStore


def _names(tools: list) -> set[str]:
    """取工具名集合。"""
    return {tool.name for tool in tools}


def _call(tool, argument: dict) -> str:
    """同步调用一个 async 工具，取回文本。"""
    chunk = asyncio.run(tool(**argument))
    return "".join(getattr(block, "text", "") for block in chunk.content)


def _state_payload() -> list[dict]:
    """一份合法的状态机。"""
    return [
        {
            "id": "S1",
            "name": "详情页",
            "observable": True,
            "observe_by": "截图：顶栏显示型号",
            "source": "打开 App 后进入设备详情页",
        },
        {
            "id": "S2",
            "name": "场景页",
            "observable": True,
            "observe_by": "截图：功能格「场景」高亮",
            "source": "点击场景模式后进入场景页",
        },
    ]


def _transition_payload() -> list[dict]:
    """一份合法的迁移。"""
    return [
        {
            "id": "T1",
            "from": "S1",
            "to": "S2",
            "event": "点击场景模式",
            "source": "点击场景模式后进入场景页",
        }
    ]


def _scenario_payload() -> list[dict]:
    """一份合法的场景。"""
    return [
        {
            "id": "SC-001",
            "title": "进入场景页",
            "path": ["S1", "S2"],
            "transitions": ["T1"],
            "type": "主流程",
            "source": "点击场景模式后进入场景页",
        }
    ]


def _case_payload() -> list[dict]:
    """一份合法的用例。"""
    return [
        {
            "id": "TC-001",
            "title": "点击场景模式进入场景页",
            "scenario_id": "SC-001",
            "pre_state": "S1",
            "steps": [{"action": "点击场景模式", "expect_state": "S2"}],
            "boundary": [],
            "method": ["场景法"],
            "priority": "P1",
            "source": "点击场景模式后进入场景页",
        }
    ]


def test_writer_has_four_tools() -> None:
    store = ArtifactStore()
    assert _names(build_writer_artifact_tools(store)) == {
        "save_state_machine",
        "append_scenarios",
        "append_cases",
        "read_artifact",
    }


def test_verifier_is_read_only() -> None:
    store = ArtifactStore()
    assert _names(build_verifier_artifact_tools(store)) == {"read_artifact"}
    assert _names(build_artifact_store_tools(store, read_only=True)) == {"read_artifact"}


def test_save_state_machine_returns_counts_only() -> None:
    store = ArtifactStore()
    tool = next(t for t in build_writer_artifact_tools(store) if t.name == "save_state_machine")
    text = _call(tool, {"states": _state_payload(), "transitions": _transition_payload()})
    assert "已保存状态机" in text
    assert "状态 2 条" in text
    assert "详情页" not in text
    assert store.counts()["states"] == 2


def test_append_scenarios_and_cases() -> None:
    store = ArtifactStore()
    tools = {tool.name: tool for tool in build_writer_artifact_tools(store)}
    _call(
        tools["save_state_machine"],
        {"states": _state_payload(), "transitions": _transition_payload()},
    )
    scenario_text = _call(tools["append_scenarios"], {"scenarios": _scenario_payload()})
    case_text = _call(tools["append_cases"], {"cases": _case_payload()})
    assert "已追加 1 条场景" in scenario_text
    assert "已追加 1 条用例" in case_text
    assert "SC-001" not in scenario_text
    assert "TC-001" not in case_text
    assert store.counts() == {"states": 2, "transitions": 1, "scenarios": 1, "cases": 1}


def test_invalid_batch_reports_error_without_writing() -> None:
    store = ArtifactStore()
    tools = {tool.name: tool for tool in build_writer_artifact_tools(store)}
    _call(
        tools["save_state_machine"],
        {"states": _state_payload(), "transitions": _transition_payload()},
    )
    bad = _case_payload()
    bad[0]["scenario_id"] = "SC-999"
    text = _call(tools["append_cases"], {"cases": bad})
    assert text.startswith("写入失败：")
    assert "scenario_id 未声明" in text
    assert store.counts()["cases"] == 0


def test_accepts_json_string_arguments() -> None:
    store = ArtifactStore()
    tools = {tool.name: tool for tool in build_writer_artifact_tools(store)}
    text = _call(
        tools["save_state_machine"],
        {
            "states": json.dumps(_state_payload(), ensure_ascii=False),
            "transitions": json.dumps(_transition_payload(), ensure_ascii=False),
        },
    )
    assert "已保存状态机" in text
    assert store.counts()["transitions"] == 1


def test_verifier_has_facts_tool_only_with_requirement() -> None:
    store = ArtifactStore()
    without_requirement = _names(build_verifier_artifact_tools(store))
    with_requirement = _names(build_verifier_artifact_tools(store, "需求正文"))
    assert without_requirement == {"read_artifact"}
    assert with_requirement == {"read_artifact", "check_artifact_facts"}


def test_writer_has_no_facts_tool() -> None:
    store = ArtifactStore()
    assert "check_artifact_facts" not in _names(build_writer_artifact_tools(store))


def test_facts_tool_reports_clean_artifact() -> None:
    store = ArtifactStore()
    store.put_state_machine(_state_payload(), _transition_payload())
    store.append_scenarios(_scenario_payload())
    store.append_cases(_case_payload())
    requirement = "打开 App 后进入设备详情页。点击场景模式后进入场景页。"
    tool = next(
        item
        for item in build_verifier_artifact_tools(store, requirement)
        if item.name == "check_artifact_facts"
    )
    text = _call(tool, {})
    assert "确定性问题：0 条" in text


def test_read_artifact_counts_only() -> None:
    store = ArtifactStore()
    tools = {tool.name: tool for tool in build_writer_artifact_tools(store)}
    _call(
        tools["save_state_machine"],
        {"states": _state_payload(), "transitions": _transition_payload()},
    )
    assert _call(tools["read_artifact"], {"counts_only": True}).startswith("状态 2 条")
    full = _call(tools["read_artifact"], {"section": "states"})
    assert "S1" in full
