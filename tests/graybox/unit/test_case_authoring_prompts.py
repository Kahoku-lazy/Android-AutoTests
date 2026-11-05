"""用例编写/验收提示词的纪律断言。

对应变更 case-authoring-state-machine：
- 编写提示词必须给出三段式（状态机 → 场景 → 用例）与四个产物工具；
- 验收提示词只判数据一致与捏造，且必须先调事实预检。
"""

from __future__ import annotations

import pytest

from engines.agents.role_sys_prompts import (
    _PROMPTS_DIR,
    CASE_VERIFIER_PROMPT,
    CASE_WRITER_PROMPT,
    CaseAuthoringPrompts,
)
from engines.agents.role_sys_prompts import __all__ as PROMPT_EXPORTS

pytestmark = [pytest.mark.unit]


def test_role_sys_prompts_exports_two_case_prompts():
    """用例提示词经 role_sys_prompts 统一分配，只剩编写与验收两篇。"""
    assert CASE_WRITER_PROMPT == CaseAuthoringPrompts.writer()
    assert CASE_VERIFIER_PROMPT == CaseAuthoringPrompts.verifier()
    assert "CASE_WRITER_PROMPT" in PROMPT_EXPORTS
    assert "CASE_VERIFIER_PROMPT" in PROMPT_EXPORTS
    for retired in (
        "CASE_MODULE_PLANNER_PROMPT",
        "CASE_WRITER_GOAL_PROMPT",
        "CASE_VERIFIER_GOAL_PROMPT",
    ):
        assert retired not in PROMPT_EXPORTS
    assert len(CASE_WRITER_PROMPT) > 1500
    assert len(CASE_VERIFIER_PROMPT) > 800


def test_retired_prompt_files_are_gone():
    """规划与 Goal 变体的提示词文件已删除。"""
    for name in (
        "CASE_MODULE_PLANNER_PROMPT.md",
        "CASE_WRITER_GOAL_PROMPT.md",
        "CASE_VERIFIER_GOAL_PROMPT.md",
    ):
        assert not (_PROMPTS_DIR / name).exists(), name


def test_writer_prompt_has_three_stages_and_four_tools():
    """编写提示词给出三段式与四个产物工具，且禁止把全文塞进 report。"""
    clauses = [
        "第一段：需求状态机",
        "第二段：业务流场景",
        "第三段：测试用例",
        "save_state_machine",
        "append_scenarios",
        "append_cases",
        "read_artifact",
        "不要把产物正文放进 report",
    ]
    for clause in clauses:
        assert clause in CASE_WRITER_PROMPT, clause


def test_writer_prompt_keeps_fact_discipline():
    """出处必须是原文、不编造数值、不可观察状态不能当断言。"""
    clauses = [
        "source` 必须是需求原文的片段",
        "不编造数值、文案、颜色、时长、上限",
        "不可观察的状态不能当断言",
        "uncertain=true",
        "单批最多 20 条",
    ]
    for clause in clauses:
        assert clause in CASE_WRITER_PROMPT, clause


def test_verifier_prompt_only_judges_two_things():
    """验收提示词只判数据一致与捏造。"""
    clauses = [
        "用例数据是否与需求正文一致",
        "是否存在自推测或捏造",
        "check_artifact_facts",
        "read_artifact",
        "不能因此判 fail",
    ]
    for clause in clauses:
        assert clause in CASE_VERIFIER_PROMPT, clause


def test_verifier_prompt_forbids_old_gates():
    """旧门禁不得复活：覆盖率、字段、方法数、章节都不能作为驳回理由。"""
    clauses = [
        "禁止以「覆盖率不足」「字段不全」「方法数不够」「缺少某节」驳回",
        "禁止只凭执行者的 `report` 或自述判通过",
        "禁止在没有调用 `check_artifact_facts` 的情况下下结论",
    ]
    for clause in clauses:
        assert clause in CASE_VERIFIER_PROMPT, clause


def test_verifier_prompt_requires_actionable_message():
    """驳回意见必须带编号与改法，通过时也要写核对量。"""
    assert "用例/场景/迁移编号 + 缺什么或与原文哪句冲突" in CASE_VERIFIER_PROMPT
    assert "核对过的用例条数" in CASE_VERIFIER_PROMPT
