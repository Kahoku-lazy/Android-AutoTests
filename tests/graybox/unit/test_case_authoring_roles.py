"""家电测试用例编写/验收角色的装配与成对运行入口。"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.sop import SOPStepRunState

import engines.agents.workflow as workflow_package

from engines.agents.prompt_config import (
    CASE_MODULE_PLANNER_PROMPT,
    CASE_VERIFIER_GOAL_PROMPT,
    CASE_VERIFIER_PROMPT,
    CASE_WRITER_GOAL_PROMPT,
    CASE_WRITER_PROMPT,
)
from engines.agents.role.case_roles import (
    CASE_PLANNER_MAX_ITERS,
    CASE_PLANNER_MODEL,
    CASE_PLANNER_NAME,
    CASE_VERIFIER_MAX_ITERS,
    CASE_VERIFIER_MODEL,
    CASE_VERIFIER_NAME,
    CASE_WRITER_MAX_ITERS,
    CASE_WRITER_MODEL,
    CASE_WRITER_NAME,
    build_case_planner,
    build_case_verifier,
    build_case_verifier_goal,
    build_case_writer,
    build_case_writer_goal,
)
from engines.agents.workflow.case_authoring_workflow import (
    CaseAuthoringResult,
    CaseAuthoringWorkflow,
    _DraftRecordingStep,
    build_run_input,
    run_case_authoring_modules,
)

pytestmark = [pytest.mark.unit]

PLAN_TOOL_NAMES = {"TaskCreate", "TaskGet", "TaskList", "TaskUpdate"}


def _tool_names(role) -> set[str]:
    """取角色 basic 组的工具名。"""
    return {tool.name for tool in role.role.toolkit.tool_groups[0].tools}


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    """角色构造只需要一个非空密钥，不会发起模型调用。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_build_case_writer_uses_writer_prompt_and_text_model():
    """编写角色：纯文本、FLASH 模型、编写提示词、计划模式工具。"""
    role = build_case_writer()
    assert role.role.name == CASE_WRITER_NAME
    assert role.role.system_prompt == CASE_WRITER_PROMPT
    assert role.role.vision is False
    assert role.role.max_iters == CASE_WRITER_MAX_ITERS
    assert role.model.model == CASE_WRITER_MODEL
    assert CASE_WRITER_MODEL == "deepseek-flash"
    assert [group.name for group in role.role.toolkit.tool_groups] == ["basic"]
    assert _tool_names(role) == PLAN_TOOL_NAMES


def test_build_case_planner_uses_planner_prompt_and_text_model():
    """规划角色：纯文本、FLASH 模型、规划提示词、空工具包。"""
    role = build_case_planner()
    assert role.role.name == CASE_PLANNER_NAME
    assert role.role.system_prompt == CASE_MODULE_PLANNER_PROMPT
    assert role.role.vision is False
    assert role.role.max_iters == CASE_PLANNER_MAX_ITERS
    assert role.model.model == CASE_PLANNER_MODEL
    assert _tool_names(role) == set()


def test_build_case_verifier_uses_verifier_prompt_and_text_model():
    """验收角色：纯文本、FLASH 模型、验收提示词、空工具包。"""
    role = build_case_verifier()
    assert role.role.name == CASE_VERIFIER_NAME
    assert role.role.system_prompt == CASE_VERIFIER_PROMPT
    assert role.role.vision is False
    assert role.role.max_iters == CASE_VERIFIER_MAX_ITERS
    assert role.model.model == CASE_VERIFIER_MODEL
    assert CASE_VERIFIER_MODEL == "deepseek-flash"
    assert _tool_names(role) == set()


def test_build_goal_roles_use_goal_prompts():
    """GoalPipeline 角色沿用同名，但提示词切换为存储工具协议。"""
    writer = build_case_writer_goal()
    verifier = build_case_verifier_goal()

    assert writer.role.name == CASE_WRITER_NAME
    assert writer.role.system_prompt == CASE_WRITER_GOAL_PROMPT
    assert verifier.role.name == CASE_VERIFIER_NAME
    assert verifier.role.system_prompt == CASE_VERIFIER_GOAL_PROMPT
    assert writer.model.model == CASE_WRITER_MODEL
    assert verifier.model.model == CASE_VERIFIER_MODEL
    assert _tool_names(writer) == PLAN_TOOL_NAMES
    assert _tool_names(verifier) == set()


def test_build_run_input_contains_requirement_and_project_meta():
    """开场输入四段齐全，空白项落到默认值。"""
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
    with pytest.raises(ValueError, match="需求正文不能为空"):
        build_run_input("   \n  ")


def test_case_authoring_result_passed_follows_last_verdict():
    """整轮是否通过只看最后一次判决；没有判决视为未通过。"""
    passed = CaseAuthoringResult(
        phase="completed",
        document="用例文档",
        verdicts=((False, "先修覆盖", CASE_VERIFIER_NAME), (True, "通过", CASE_VERIFIER_NAME)),
    )
    assert passed.passed is True

    failed = CaseAuthoringResult(
        phase="failed",
        document="",
        verdicts=((False, "仍有阻断", CASE_VERIFIER_NAME),),
    )
    assert failed.passed is False
    assert CaseAuthoringResult(phase="failed", document="", verdicts=()).passed is False


def test_draft_recording_step_keeps_rejected_draft():
    """SOP 驳回会清空 submission，草稿副本仍要保留。"""
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
    step = _DraftRecordingStep("子任务", "交文档", executor=object(), verifier=object())
    step.drafts = ["<submission></submission>"]

    step._check_document()

    assert step.truncated is True


def test_draft_step_keeps_long_incomplete_document_for_verifier():
    """有正文但缺第六/七节时只记不完整，不按截断拆分。"""
    step = _DraftRecordingStep("子任务", "交文档", executor=object(), verifier=object())
    step.drafts = ["## 一、需求原子表\n" + "用例正文" * 100]

    step._check_document()

    assert step.truncated is False
    assert step.incomplete is True


def test_workflow_package_exports_case_authoring_entry():
    """新增入口能从 workflow 包直接取用。"""
    assert workflow_package.CaseAuthoringWorkflow is CaseAuthoringWorkflow
    assert workflow_package.build_run_input is build_run_input
    assert callable(workflow_package.run_case_authoring)
    assert workflow_package.run_case_authoring_modules is run_case_authoring_modules
