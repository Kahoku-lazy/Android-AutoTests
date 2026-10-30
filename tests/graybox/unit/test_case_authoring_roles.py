"""家电测试用例编写/验收角色的装配与成对运行入口。"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.sop import SOPStepRunState

from engines.agents.role_sys_prompts import CaseAuthoringPrompts
from engines.agents.agent_builders import (
    build_case_planner,
    build_case_verifier,
    build_case_verifier_goal,
    build_case_writer,
    build_case_writer_goal,
)
from engines.agents.config.models import load_role_config

pytestmark = [pytest.mark.unit]

PLAN_TOOL_NAMES = {"TaskCreate", "TaskGet", "TaskList", "TaskUpdate"}

_WRITER_KEY = "CASE_WRITER_ROLE_CONFIG"
_VERIFIER_KEY = "CASE_VERIFIER_ROLE_CONFIG"
_PLANNER_KEY = "CASE_PLANNER_ROLE_CONFIG"


def _bundle(key: str):
    return load_role_config(key)


def _case_authoring_workflow():
    """延迟导入，避免缺 config.yaml 时拖垮用例角色装配测试。"""
    from engines.agents.workflow import case_authoring_workflow as m

    return m


def _tool_names(agent) -> set[str]:
    """取 Agent basic 组的工具名。"""
    return {tool.name for tool in agent.toolkit.tool_groups[0].tools}


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    """角色构造只需要一个非空密钥，不会发起模型调用。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_build_case_writer_uses_writer_prompt_and_text_model():
    """编写角色：纯文本、FLASH 模型、编写提示词、计划模式工具。"""
    mc, role, _tools, _ctx, react = _bundle(_WRITER_KEY)
    agent = build_case_writer()
    assert agent.name == role.name == "case_writer_role"
    assert agent._system_prompt == CaseAuthoringPrompts.writer()
    assert agent.react_config.max_iters == react.max_iters == 20
    assert agent.model.model == mc.model_name == "deepseek-flash"
    assert [group.name for group in agent.toolkit.tool_groups] == ["basic"]
    assert _tool_names(agent) == PLAN_TOOL_NAMES


def test_build_case_planner_uses_planner_prompt_and_text_model():
    """规划角色：纯文本、FLASH 模型、规划提示词、空工具包。"""
    mc, role, _tools, _ctx, react = _bundle(_PLANNER_KEY)
    agent = build_case_planner()
    assert agent.name == role.name == "case_planner_role"
    assert agent._system_prompt == CaseAuthoringPrompts.planner()
    assert agent.react_config.max_iters == react.max_iters == 2
    assert agent.model.model == mc.model_name
    assert _tool_names(agent) == set()


def test_build_case_verifier_uses_verifier_prompt_and_text_model():
    """验收角色：纯文本、FLASH 模型、验收提示词、空工具包。"""
    mc, role, _tools, _ctx, react = _bundle(_VERIFIER_KEY)
    agent = build_case_verifier()
    assert agent.name == role.name == "case_verifier_role"
    assert agent._system_prompt == CaseAuthoringPrompts.verifier()
    assert agent.react_config.max_iters == react.max_iters == 4
    assert agent.model.model == mc.model_name == "deepseek-flash"
    assert _tool_names(agent) == set()


def test_build_goal_roles_use_goal_prompts():
    """GoalPipeline 角色沿用同名，但提示词切换为存储工具协议。"""
    writer = build_case_writer_goal()
    verifier = build_case_verifier_goal()
    w_mc, w_role, *_ = _bundle("CASE_WRITER_GOAL_ROLE_CONFIG")
    v_mc, v_role, *_ = _bundle("CASE_VERIFIER_GOAL_ROLE_CONFIG")

    assert writer.name == w_role.name
    assert writer._system_prompt == CaseAuthoringPrompts.writer_goal()
    assert verifier.name == v_role.name
    assert verifier._system_prompt == CaseAuthoringPrompts.verifier_goal()
    assert writer.model.model == w_mc.model_name
    assert verifier.model.model == v_mc.model_name
    assert _tool_names(writer) == PLAN_TOOL_NAMES
    assert _tool_names(verifier) == set()


def test_build_run_input_contains_requirement_and_project_meta():
    """开场输入四段齐全，空白项落到默认值。"""
    try:
        build_run_input = _case_authoring_workflow().build_run_input
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    text = build_run_input(
        "  待机下单击 POWER 开机  ",
        project_code="H717D",
        version="V2",
        existing_cases="TC-H717D-BTN-V1-001",
    )
    assert "## 需求正文\n待机下单击 POWER 开机" in text
    assert "## 项目代号\nH717D" in text
    assert "## 版本号\nV2" in text
    assert "## 已有用例索引\nTC-H717D-BTN-V1-001" in text

    defaults = build_run_input("需求")
    assert "## 项目代号\nPROJ" in defaults
    assert "## 版本号\nV1" in defaults
    assert "（无，按全新模式全量生成）" in defaults


def test_build_run_input_rejects_blank_requirement():
    """空需求不能开跑。"""
    try:
        build_run_input = _case_authoring_workflow().build_run_input
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    with pytest.raises(ValueError, match="需求正文不能为空"):
        build_run_input("   \n  ")


def test_case_authoring_result_passed_follows_last_verdict():
    """整轮是否通过只看最后一次判决；没有判决视为未通过。"""
    try:
        CaseAuthoringResult = _case_authoring_workflow().CaseAuthoringResult
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    name = _bundle(_VERIFIER_KEY)[1].name
    passed = CaseAuthoringResult(
        phase="completed",
        document="用例文档",
        verdicts=((False, "先修覆盖", name), (True, "通过", name)),
    )
    assert passed.passed is True

    failed = CaseAuthoringResult(
        phase="failed",
        document="",
        verdicts=((False, "仍有阻断", name),),
    )
    assert failed.passed is False
    assert CaseAuthoringResult(phase="failed", document="", verdicts=()).passed is False


def test_draft_recording_step_keeps_rejected_draft():
    """SOP 驳回会清空 submission，草稿副本仍要保留。"""
    try:
        _DraftRecordingStep = _case_authoring_workflow()._DraftRecordingStep
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    step = _DraftRecordingStep("子任务", "交文档", executor=object(), verifier=object())
    state = SOPStepRunState()
    state.submission = [TextBlock(text="第一版")]
    step._remember(state)
    state.submission = None
    step._remember(state)
    assert step.drafts == ["第一版"]

    state.submission = [TextBlock(text="第二版")]
    step._remember(state)
    assert step.drafts == ["第一版", "第二版"]


def test_draft_step_marks_tag_only_submission_truncated():
    """只有 <submission> 标签、没有正文的交付按截断处理，不再送验收。"""
    try:
        _DraftRecordingStep = _case_authoring_workflow()._DraftRecordingStep
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    step = _DraftRecordingStep("子任务", "交文档", executor=object(), verifier=object())
    step.drafts = ["<submission></submission>"]

    step._check_document()

    assert step.truncated is True


def test_draft_step_keeps_long_incomplete_document_for_verifier():
    """有正文但缺第六/七节时只记不完整，不按截断拆分。"""
    try:
        _DraftRecordingStep = _case_authoring_workflow()._DraftRecordingStep
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 辅助测试: {exc}")
    step = _DraftRecordingStep("子任务", "交文档", executor=object(), verifier=object())
    step.drafts = ["## 一、需求原子表\n" + "用例正文" * 100]

    step._check_document()

    assert step.truncated is False
    assert step.incomplete is True


def test_workflow_package_exports_case_authoring_entry():
    """新增入口能从 workflow 包直接取用。"""
    try:
        import engines.agents.workflow as workflow_package

        m = _case_authoring_workflow()
    except FileNotFoundError as exc:
        pytest.skip(f"缺 config.yaml，跳过 workflow 包导出测试: {exc}")
    assert workflow_package.CaseAuthoringWorkflow is m.CaseAuthoringWorkflow
    assert workflow_package.build_run_input is m.build_run_input
    assert callable(workflow_package.run_case_authoring)
    assert workflow_package.run_case_authoring_modules is m.run_case_authoring_modules
