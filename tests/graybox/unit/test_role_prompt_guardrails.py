"""角色提示词纪律断言：把复盘出的可避免失败写成不可回退的文本约束。

对应变更 task-execution-resilience 的 role-prompt-guardrails：
- 执行者：提交前逐条核对、未达成不声称完成、先执行驳回指令、坐标以工具返回为准、
  手势后复核、handover 带 action_time。
- 验收者：先调检查工具再判、不得要求 base64/文件路径、驳回意见必须可执行。
"""

from __future__ import annotations

import pytest

from engines.agents.prompts.executor_prompt import EXECUTOR_PROMPT
from engines.agents.prompts.verifier_prompt import VERIFIER_PROMPT

pytestmark = [pytest.mark.unit]


def test_executor_prompt_declares_submission_checks():
    """执行提示词六项硬约束齐全。"""
    clauses = [
        "逐条核对",
        "在未达成时声称已完成",
        "先逐步执行上一条驳回说明",
        "必须原样使用该坐标",
        "手势完成后必须重新截图核对",
        "action_time",
    ]
    for clause in clauses:
        assert clause in EXECUTOR_PROMPT, clause


def test_executor_prompt_requires_coordinate_marking_before_click():
    """估算坐标与 xpath 返回坐标都必须先用 mark_dot 打红点核对，确认后才允许点击。"""
    assert "mark_dot(serial, x, y)" in EXECUTOR_PROMPT
    assert "无论来自自己看图估算还是 xpath_action 返回" in EXECUTOR_PROMPT
    assert "红点没有落在目标元素上" in EXECUTOR_PROMPT
    assert "禁止**在确认红点位置前执行点击" in EXECUTOR_PROMPT
    assert "normalized=False" in EXECUTOR_PROMPT
    assert "不需要再标记" not in EXECUTOR_PROMPT
    assert "截图、坐标核对和返回键不用打开" in EXECUTOR_PROMPT


def test_executor_prompt_declares_log_check_belongs_to_verifier():
    """日志检查只属于验收模型，执行模型不得检查或声称检查过日志。"""
    assert "设备日志不归你检查" in EXECUTOR_PROMPT
    assert "只有验收模型有该权限" in EXECUTOR_PROMPT
    assert "禁止**尝试检查、推测或声称检查过日志" in EXECUTOR_PROMPT
    assert "在 handover 里写日志结论" in EXECUTOR_PROMPT


def test_executor_prompt_no_longer_allows_half_done_submission():
    """旧的“没做完写出来即可交接”表述必须消失。"""
    assert "还没做完或没验证的部分，明确写出来，不要含糊过去" not in EXECUTOR_PROMPT


def test_verifier_prompt_requires_actual_log_check():
    """没有调用检查工具时不得写“没有日志”。"""
    assert "先实际调用 check_device_log 再下结论" in VERIFIER_PROMPT
    assert "没有调用工具就 MUST NOT 写" in VERIFIER_PROMPT


def test_verifier_prompt_rejects_unavailable_evidence():
    """验收不得索要执行者拿不到的 base64 / 文件路径。"""
    assert "MUST NOT 要求执行者提供 base64" in VERIFIER_PROMPT
    assert "落盘文件路径" in VERIFIER_PROMPT


def test_verifier_prompt_rejection_is_executable():
    """驳回意见必须落在执行者工具集内。"""
    assert "驳回意见必须能在执行者工具集内执行" in VERIFIER_PROMPT
    assert "不要让它调用日志工具" in VERIFIER_PROMPT


def test_executor_prompt_separates_connection_spinner_from_page_loading():
    """长按后的设备连接加载圈不按页面加载超时判失败。"""
    assert "属于设备连接/同步过程" in EXECUTOR_PROMPT
    assert "**不是**页面加载" in EXECUTOR_PROMPT
    assert "禁止**据此判本步失败" in EXECUTOR_PROMPT
    assert "这类整体加载持续超过 10s 才可终止" in EXECUTOR_PROMPT


def test_executor_prompt_forbids_incomplete_handover_wording():
    """handover 出现“尚未/未完成/请下一步”即视为没做完。"""
    assert "handover 里**禁止**出现“尚未”“未完成”“未点击”“请下一步”" in EXECUTOR_PROMPT
