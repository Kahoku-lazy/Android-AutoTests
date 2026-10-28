"""家电测试用例编写/验收提示词的纪律断言。

对应变更 add-appliance-case-authoring：
- 编写提示词必须保留技能的五阶段 SOP、8 种方法、方法数门槛、13 字段与七节交付结构；
- 验收提示词必须逐条核对、只验收设计、按阻断/严重分级给可执行的驳回意见。
"""

from __future__ import annotations

import pytest

from engines.agents.prompt_config import (
    CASE_MODULE_PLANNER_PROMPT,
    CASE_VERIFIER_GOAL_PROMPT,
    CASE_VERIFIER_PROMPT,
    CASE_WRITER_GOAL_PROMPT,
    CASE_WRITER_PROMPT,
)
from engines.agents.prompt_config import __all__ as PROMPT_EXPORTS
from engines.agents.prompts.case_module_planner_prompt import (
    CASE_MODULE_PLANNER_PROMPT as PLANNER_BODY,
)
from engines.agents.prompts.case_verifier_prompt import (
    CASE_VERIFIER_GOAL_PROMPT as VERIFIER_GOAL_BODY,
)
from engines.agents.prompts.case_verifier_prompt import (
    CASE_VERIFIER_PROMPT as VERIFIER_BODY,
)
from engines.agents.prompts.case_writer_prompt import (
    CASE_WRITER_GOAL_PROMPT as WRITER_GOAL_BODY,
)
from engines.agents.prompts.case_writer_prompt import CASE_WRITER_PROMPT as WRITER_BODY

pytestmark = [pytest.mark.unit]


def test_prompt_config_exports_case_prompts():
    """用例提示词经 prompt_config 统一分配，正文与模块常量一致。"""
    assert CASE_WRITER_PROMPT == WRITER_BODY
    assert CASE_VERIFIER_PROMPT == VERIFIER_BODY
    assert CASE_MODULE_PLANNER_PROMPT == PLANNER_BODY
    assert CASE_WRITER_GOAL_PROMPT == WRITER_GOAL_BODY
    assert CASE_VERIFIER_GOAL_PROMPT == VERIFIER_GOAL_BODY
    assert "CASE_WRITER_PROMPT" in PROMPT_EXPORTS
    assert "CASE_VERIFIER_PROMPT" in PROMPT_EXPORTS
    assert "CASE_MODULE_PLANNER_PROMPT" in PROMPT_EXPORTS
    assert "CASE_WRITER_GOAL_PROMPT" in PROMPT_EXPORTS
    assert "CASE_VERIFIER_GOAL_PROMPT" in PROMPT_EXPORTS
    assert len(CASE_WRITER_PROMPT) > 3000
    assert len(CASE_VERIFIER_PROMPT) > 3000
    assert len(CASE_MODULE_PLANNER_PROMPT) > 800


def test_goal_prompts_use_store_tools_and_result_schema():
    """GoalPipeline 提示词要求先保存/读取文档，report 只写摘要。"""
    assert "save_case_module_document" in CASE_WRITER_GOAL_PROMPT
    assert "read_case_module_document" in CASE_WRITER_GOAL_PROMPT
    assert "MUST NOT 把全文放进 report" in CASE_WRITER_GOAL_PROMPT
    assert "MUST NOT 用计划任务代替 `save_case_module_document`" in CASE_WRITER_GOAL_PROMPT
    assert "read_case_module_document" in CASE_VERIFIER_GOAL_PROMPT
    assert "`result`" in CASE_VERIFIER_GOAL_PROMPT
    assert "不是 `passed`" in CASE_VERIFIER_GOAL_PROMPT


def test_writer_prompt_keeps_skill_sop():
    """编写提示词保留五阶段、方法门槛、七节交付与模块化交付约束。"""
    clauses = [
        "五阶段，顺序不可跳过",
        "需求原子表",
        "方法分配表（需求追溯矩阵）",
        "需求冲突登记表",
        "13 个字段，缺一不可",
        "TC-{项目}-{模块}-V{版本}-{序号}",
        "L1（≤2 因子、无物理依赖）",
        "L2（3-5 因子，或单一物理依赖）",
        "L3（≥6 因子，或多种驱动方式混合）",
        "L4（跨系统/协议/硬件）",
        "P0 占比必须 ≤30%",
        "E2E 用户旅程",
        "覆盖与门禁自检",
        "待确认问题",
        "交付即正文",
        "增量模式",
        "UNTESTABLE",
        "没有文件、设备或日志工具",
        "`UNTESTABLE` 不是状态值",
        "四项缺一不可",
        "模块化交付",
        "本次模块",
        "原子编号区段",
        "E2E-{模块KEY}-01",
        "第六节只统计本模块",
        "规模控制",
        "最多 24 条",
        "未定判据的状态",
        "阈值来源",
        "记录项：观察并记录",
        "已判定覆盖率",
        "已登记覆盖率",
        "计划模式",
        "TaskCreate",
        "TaskGet",
        "TaskList",
        "TaskUpdate",
        "计划不能替代正文",
    ]
    for clause in clauses:
        assert clause in CASE_WRITER_PROMPT, clause


def test_planner_prompt_only_splits_requirement_ranges():
    """规划提示词只切行号区间，要求覆盖、不重叠、不写用例。"""
    clauses = [
        "只负责把一份需求正文切成若干",
        "start_line",
        "end_line",
        "MUST NOT 重叠",
        "MUST NOT 丢段",
        "2~12 个模块",
        "10~18 个需求原子",
        "不要输出用例",
        "3~4 个大写字母",
    ]
    for clause in clauses:
        assert clause in CASE_MODULE_PLANNER_PROMPT, clause


def test_writer_prompt_forbids_vague_expectations():
    """编写提示词点名禁止不可判定的预期措辞，并要求量化。"""
    assert "禁止「正常」「稳定」「良好」「符合预期」「无明显异常」" in CASE_WRITER_PROMPT
    assert "可观察对象 + 量化阈值/容差" in CASE_WRITER_PROMPT
    assert "判不了 PASS/FAIL" in CASE_WRITER_PROMPT


def test_verifier_prompt_judges_by_checklist_not_trust():
    """验收提示词要求逐项核对、不采信作者自述，且不要求文档外证据。"""
    clauses = [
        "逐项核对，不抽样",
        "看不到即不通过",
        "只验收设计",
        "MUST NOT 索要截图、设备日志、执行记录、文件路径",
        "不重写",
        "13 字段完整性",
        "P0 已登记覆盖率 100%，P1 ≥90%，P2 ≥70%",
        "已登记覆盖",
        "已判定覆盖",
        "记录项",
        "passed=true",
        "passed=false",
    ]
    for clause in clauses:
        assert clause in CASE_VERIFIER_PROMPT, clause


def test_verifier_prompt_rejection_is_actionable():
    """驳回意见必须带位置与改法，并禁止放水。"""
    assert "[阻断|严重|建议]" in CASE_VERIFIER_PROMPT
    assert "禁止空 message" in CASE_VERIFIER_PROMPT
    assert "常见放水（禁止）" in CASE_VERIFIER_PROMPT
    assert "提交不是完整文档" in CASE_VERIFIER_PROMPT
    assert "提交只有摘要、目录、文件路径" in CASE_VERIFIER_PROMPT
    assert "几乎逐字相同" in CASE_VERIFIER_PROMPT
    assert "辅助计数有偏差" in CASE_VERIFIER_PROMPT
    assert "最多 40 条" in CASE_VERIFIER_PROMPT
    assert "首轮必须一次列全所有阻断" in CASE_VERIFIER_PROMPT
