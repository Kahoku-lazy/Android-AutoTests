"""用例编写/验收两个角色的装配与流水线入口。"""

from __future__ import annotations

import pytest

from engines.agents.agent_builders import build_case_verifier, build_case_writer
from engines.agents.config.role_loader import load_role_spec
from engines.agents.models import get_chat_model
from engines.agents.role_sys_prompts import CaseAuthoringPrompts

pytestmark = [pytest.mark.unit]

_WRITER_KEY = "CASE_WRITER_ROLE_CONFIG"
_VERIFIER_KEY = "CASE_VERIFIER_ROLE_CONFIG"


def _bundle(key: str):
    return load_role_spec(key)


def _tool_names(agent) -> set[str]:
    """取 Agent basic 组的工具名。"""
    return {tool.name for tool in agent.toolkit.tool_groups[0].tools}


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    """角色构造只需要一个非空密钥，不会发起模型调用。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_build_case_writer_uses_writer_prompt_and_empty_toolkit():
    """编写角色：纯文本、FLASH 模型、编写提示词、工具由流水线运行时注入。"""
    bundle = _bundle(_WRITER_KEY)
    agent = build_case_writer()
    assert agent.name == bundle.role.name == "case_writer_role"
    assert agent._system_prompt == CaseAuthoringPrompts.writer()
    assert agent.react_config.max_iters == bundle.react.max_iters == 60
    assert agent.model.model == get_chat_model(_WRITER_KEY).model == "deepseek-flash"
    assert [group.name for group in agent.toolkit.tool_groups] == ["basic"]
    assert _tool_names(agent) == set()


def test_build_case_verifier_uses_verifier_prompt_and_empty_toolkit():
    """验收角色：纯文本、FLASH 模型、验收提示词、空工具包。"""
    bundle = _bundle(_VERIFIER_KEY)
    agent = build_case_verifier()
    assert agent.name == bundle.role.name == "case_verifier_role"
    assert agent._system_prompt == CaseAuthoringPrompts.verifier()
    assert agent.react_config.max_iters == bundle.react.max_iters == 4
    assert agent.model.model == get_chat_model(_VERIFIER_KEY).model == "deepseek-flash"
    assert _tool_names(agent) == set()


def test_only_two_case_roles_remain():
    """角色配置只剩编写与验收两个，规划与 Goal 变体已删除。"""
    import engines.agents.agent_builders as builders

    for retired in ("build_case_planner", "build_case_writer_goal", "build_case_verifier_goal"):
        assert not hasattr(builders, retired)


def test_workflow_package_exports_single_entry():
    """workflow 包只导出目标流水线入口，不再有模块化/SOP 变体。"""
    import engines.agents.workflow as package

    assert callable(package.run_case_authoring_artifact)
    assert callable(package.build_case_run_input)
    assert not hasattr(package, "run_case_authoring_modules")
    assert not hasattr(package, "CaseAuthoringWorkflow")


async def test_paired_assembly_attaches_artifact_tools():
    """成对装配：编写角色可写产物，验收角色只读，两侧工具不共享。"""
    from engines.agents.case_roles import build_case_authoring_roles
    from engines.agents.workflow.case_artifact import ArtifactStore

    store = ArtifactStore()
    writer, verifier = await build_case_authoring_roles(store, requirement_text="需求正文")

    writer_tools = {tool.name for group in writer.toolkit.tool_groups for tool in group.tools}
    verifier_tools = {
        tool.name for group in verifier.toolkit.tool_groups for tool in group.tools
    }

    assert {"save_state_machine", "append_scenarios", "append_cases"} <= writer_tools
    assert {"read_artifact", "check_artifact_facts"} <= verifier_tools
    assert not ({"save_state_machine", "append_scenarios", "append_cases"} & verifier_tools)


def test_build_run_input_contains_requirement_and_project_meta():
    """开场输入三段齐全，空白项落到默认值。"""
    from engines.agents.workflow.case_goal_workflow import build_case_run_input

    text = build_case_run_input("  待机下单击 POWER 开机  ", project_code="H717D", version="V2")
    assert "## 需求正文\n待机下单击 POWER 开机" in text
    assert "## 项目代号\nH717D" in text
    assert "## 版本号\nV2" in text

    defaults = build_case_run_input("需求")
    assert "## 项目代号\nPROJ" in defaults
    assert "## 版本号\nV1" in defaults


def test_build_run_input_rejects_blank_requirement():
    """空需求不能开跑。"""
    from engines.agents.workflow.case_goal_workflow import build_case_run_input

    with pytest.raises(ValueError, match="需求正文不能为空"):
        build_case_run_input("   \n  ")


def test_case_authoring_result_passed_needs_cases_facts_and_verdict():
    """通过需要三件事同时成立：有用例、事实无确定性问题、最后判决通过。"""
    from engines.agents.workflow.case_artifact import Artifact, ArtifactCase, ArtifactStep
    from engines.agents.workflow.case_artifact_facts import FactIssue, FactReport
    from engines.agents.workflow.case_goal_workflow import CaseAuthoringResult

    case = ArtifactCase(
        "TC-001",
        "点击",
        "SC-001",
        "S1",
        (ArtifactStep("点击场景模式", "S2", ""),),
        (),
        ("场景法",),
        "P1",
        "原文",
    )
    clean = FactReport()

    passed = CaseAuthoringResult(
        phase="completed",
        artifact=Artifact(cases=(case,)),
        facts=clean,
        verdicts=((True, "通过", "case_verifier_role"),),
        document="文档",
    )
    assert passed.passed is True

    blocked = CaseAuthoringResult(
        phase="failed",
        artifact=Artifact(cases=(case,)),
        facts=FactReport(blocking=(FactIssue("X", "用例 TC-001", "出处不实"),)),
        verdicts=((True, "通过", "case_verifier_role"),),
        document="文档",
    )
    assert blocked.passed is False

    no_cases = CaseAuthoringResult(
        phase="failed",
        artifact=Artifact(),
        facts=clean,
        verdicts=((True, "通过", "case_verifier_role"),),
        document="",
    )
    assert no_cases.passed is False
