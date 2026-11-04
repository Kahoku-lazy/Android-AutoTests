"""角色提示词纪律断言：把复盘出的可避免失败写成不可回退的文本约束。

对应变更 task-execution-resilience 的 role-prompt-guardrails：
- 执行者：提交前逐条核对、未达成不声称完成、先执行驳回指令、坐标以工具返回为准、
  手势后复核、handover 带 action_time。
- 验收者：先调检查工具再判、不得要求 base64/文件路径、驳回意见必须可执行。
"""

from __future__ import annotations

import pytest

from engines.agents.role_sys_prompts import EXECUTOR_PROMPT
from engines.agents.role_sys_prompts import VERIFIER_PROMPT

pytestmark = [pytest.mark.unit]


def test_executor_prompt_declares_submission_checks():
    """执行提示词六项硬约束齐全。"""
    clauses = [
        "逐条核对",
        "在未达成时声称达成",
        "先逐步执行上一条驳回说明",
        "用回传的页面图核对结果",
        "action_time",
    ]
    for clause in clauses:
        assert clause in EXECUTOR_PROMPT, clause


def test_executor_prompt_uses_page_anchors():
    """执行提示词要求优先按步骤给出的页面锚点导航，并禁止连续盲试 xpath。"""
    assert "【本步页面锚点】" in EXECUTOR_PROMPT
    assert "禁止**连续盲试" in EXECUTOR_PROMPT


def test_executor_prompt_stays_on_result_page_before_submitting():
    """交卷前必须停在本步结果所在的页面，验收重新截图才看得到证据。"""
    assert "交卷前必须停在本步结果所在的页面" in EXECUTOR_PROMPT
    assert "禁止**先返回上一页" in EXECUTOR_PROMPT


def test_executor_prompt_locates_by_xpath_before_vision():
    """先按页面文案走 xpath（含归一化、最多 3 个候选），未命中才用视觉估算。"""
    assert 'xpath_action(texts="文案1,文案2")' in EXECUTOR_PROMPT
    assert "最多 3 个候选" in EXECUTOR_PROMPT
    assert "自动忽略空格与全角差异" in EXECUTOR_PROMPT
    assert "才用截图估算归一化坐标" in EXECUTOR_PROMPT
    assert "或目标本身没有文案" in EXECUTOR_PROMPT


def test_executor_prompt_picks_index_from_marked_image():
    """多命中时先看带序号的标记图挑序号，再带 token 与 index 点击。"""
    assert "每个点带序号" in EXECUTOR_PROMPT
    assert "选定真正要点的那个序号" in EXECUTOR_PROMPT
    assert "带 `token` 和 `index` 点击" in EXECUTOR_PROMPT
    assert "禁止**凭坐标大小猜" in EXECUTOR_PROMPT


def test_executor_prompt_forbids_action_without_anchor_confirmation():
    """没核对过的目标禁止操作；工具报缺 token 时先补核对。"""
    assert "没有经过坐标核对确认的目标禁止操作" in EXECUTOR_PROMPT
    assert "缺 `token` 会直接报错且不会点" in EXECUTOR_PROMPT
    assert "先补一次核对" in EXECUTOR_PROMPT
    assert "禁止**绕过" in EXECUTOR_PROMPT
    assert "核对与点击之间禁止再截图" in EXECUTOR_PROMPT


def test_executor_prompt_confirms_drag_trajectory_first():
    """拖动前必须先用核对图画出起点→终点轨迹，并禁止原样重复同一次拖动。"""
    assert "mark_dot(serial, nx1, ny1, x2=…, y2=…)" in EXECUTOR_PROMPT
    assert "起点、终点与箭头" in EXECUTOR_PROMPT
    assert "再带该 `token` 调 `drag_ratio`" in EXECUTOR_PROMPT
    assert "禁止**原样重复同一次拖动" in EXECUTOR_PROMPT


def test_executor_prompt_does_not_screenshot_twice_per_action():
    """点击类工具已回图时不得再截第二张；只有手势不回图才用截图复核。"""
    assert "直接看那张图" in EXECUTOR_PROMPT
    assert "用回传的页面图核对结果" in EXECUTOR_PROMPT
    assert "禁止**为同一个动作再调截图工具截第二张" in EXECUTOR_PROMPT


def test_executor_prompt_declares_log_check_belongs_to_verifier():
    """日志检查只属于验收模型，执行模型不得检查或声称检查过日志。"""
    assert "设备日志不归你检查" in EXECUTOR_PROMPT
    assert "只有验收模型有该权限" in EXECUTOR_PROMPT
    assert "禁止**尝试检查、推测或声称检查过日志" in EXECUTOR_PROMPT
    assert "在 handover 里写日志结论" in EXECUTOR_PROMPT


def test_executor_prompt_handover_is_two_blocks():
    """handover 只写两块：操作步骤（含 action_time 原文）与最终结果。"""
    assert "只需写两块" in EXECUTOR_PROMPT
    assert "本步做了什么" in EXECUTOR_PROMPT
    assert "最终结果：以「达成」或「未达成」开头" in EXECUTOR_PROMPT
    assert "点击类工具返回原文" in EXECUTOR_PROMPT
    assert "不要写过程分析、逐条证据、日志结论、阻塞说明或下一步建议" in EXECUTOR_PROMPT


def test_executor_prompt_allows_honest_undone_result():
    """如实写「未达成」是合法交卷口径，不再要求逐条证据与阻塞建议。"""
    assert "结果写「未达成」" in EXECUTOR_PROMPT
    assert "「未达成」时在同一句里写清卡在哪里" in EXECUTOR_PROMPT
    assert "逐条写明哪一条没达成" not in EXECUTOR_PROMPT


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


def test_verifier_prompt_takes_keyword_from_step_evidence():
    """关键词优先取步骤给出的证据，其次查关键词表，禁止连续盲试。"""
    assert "【本步日志证据】" in VERIFIER_PROMPT
    assert "【本步关键词表】" in VERIFIER_PROMPT
    assert "MUST NOT 连续盲试多个关键词" in VERIFIER_PROMPT
    assert "系统提示词末尾" not in VERIFIER_PROMPT


def test_verifier_prompt_splits_evidence_by_assertion_type():
    """日志型以日志为准且不必截图；页面型以截图为主且不查日志。"""
    assert "以日志为唯一判据" in VERIFIER_PROMPT
    assert "不必截图" in VERIFIER_PROMPT
    assert "以截图为主要判据" in VERIFIER_PROMPT
    assert "不要调用 check_device_log" in VERIFIER_PROMPT
    assert "混合型" in VERIFIER_PROMPT


def test_verifier_prompt_checks_every_keyword():
    """给出多个关键词时逐个查，全部命中才算通过。"""
    assert "逐个调用 check_device_log" in VERIFIER_PROMPT
    assert "同一个关键词出现两次表示要命中两次" in VERIFIER_PROMPT
    assert "全部命中才算通过" in VERIFIER_PROMPT


def test_executor_prompt_separates_connection_spinner_from_page_loading():
    """长按后的设备连接加载圈不按页面加载超时判失败。"""
    assert "属于设备连接/同步过程" in EXECUTOR_PROMPT
    assert "**不是**页面加载" in EXECUTOR_PROMPT
    assert "禁止**据此判本步失败" in EXECUTOR_PROMPT
    assert "这类整体加载持续超过 10s 才可终止" in EXECUTOR_PROMPT


def test_executor_prompt_forbids_incomplete_handover_wording():
    """handover 出现“尚未/未完成/请下一步”即视为没做完。"""
    assert "handover 里**禁止**出现“尚未”“未完成”“未点击”“请下一步”" in EXECUTOR_PROMPT
