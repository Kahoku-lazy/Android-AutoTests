"""步骤简报：锚点只进执行者、证据只进验收者；缺字段时与旧行为一致。"""

from __future__ import annotations

import pytest

from engines.agents.workflow.case_file import CaseStep, LogEvidence
from engines.agents.workflow.step_brief import (
    ANCHOR_HEADER,
    EVIDENCE_HEADER,
    KEYWORDS_HEADER,
    MISSING_KEYWORDS,
    MULTI_KEYWORD_HINT,
    executor_brief,
    verifier_brief,
    with_context,
)

pytestmark = [pytest.mark.unit]

_LOG = LogEvidence(sku="H6810", port=7005, keywords=("timer_configs_set_success",))


def test_plain_step_keeps_original_text():
    """没有 anchor / log 时两份简报与旧行为逐字一致。"""
    step = CaseStep(action="打开定时页", expected="定时页可见")

    assert executor_brief(step) == "打开定时页"
    assert verifier_brief(step) == "定时页可见"


def test_executor_brief_carries_anchor_but_not_expected():
    """锚点进执行者简报，且简报里不出现要核对的结果。"""
    step = CaseStep(
        action="设置 5:00 定时",
        expected="列表出现 5:00",
        anchor={"page": "定时页", "entry": "详情页左上「定时」"},
    )

    brief = executor_brief(step)

    assert ANCHOR_HEADER in brief
    assert "定时页" in brief
    assert "详情页左上「定时」" in brief
    assert "列表出现 5:00" not in brief


def test_verifier_brief_carries_evidence_but_not_action():
    """日志证据进验收简报，且简报里不出现动作与锚点。"""
    step = CaseStep(
        action="设置 5:00 定时",
        expected="定时列表出现 5:00",
        anchor={"page": "定时页"},
        log=_LOG,
    )

    brief = verifier_brief(step, "# H6810 关键词\n- 设置预约定时成功 → timer_configs_set_success")

    assert EVIDENCE_HEADER in brief
    assert "sku=H6810" in brief and "port=7005" in brief
    assert "keyword=timer_configs_set_success" in brief
    assert KEYWORDS_HEADER in brief
    assert "设置 5:00 定时" not in brief
    assert "页面：" not in brief


def test_missing_catalog_tells_verifier_to_fall_back():
    """关键词目录缺失时写明缺失，不让验收去盲试。"""
    step = CaseStep(action="设置定时", expected="定时成功", log=_LOG)

    brief = verifier_brief(step, "")

    assert KEYWORDS_HEADER in brief
    assert MISSING_KEYWORDS in brief


def test_multi_keywords_are_listed_with_hint():
    """多个关键词按顺序列出，并附「逐个查、重复即多次」的提示。"""
    step = CaseStep(
        action="开关各触发一次",
        expected="开灯与关灯日志",
        log=LogEvidence(sku="H6810", port=7005, keywords=("switch_on", "switch_off")),
    )

    brief = verifier_brief(step)

    assert "keywords=switch_on, switch_off" in brief
    assert MULTI_KEYWORD_HINT in brief


def test_catalog_is_attached_even_without_log_block():
    """旧用例没写 log 时也要给关键词表，只是没有【本步日志证据】那一行。"""
    step = CaseStep(action="设置定时", expected="定时成功")

    brief = verifier_brief(step, "# H6810 关键词\n- 设置预约定时成功 → timer_configs_set_success")

    assert KEYWORDS_HEADER in brief
    assert "timer_configs_set_success" in brief
    assert EVIDENCE_HEADER not in brief


def test_context_is_prefixed_and_empty_context_is_noop():
    """开场上下文放在最前面；没有上下文时原样返回。"""
    context = "本次要操作的设备 serial 是：R5CT62RH88F。"

    assert with_context("回到桌面", context) == f"{context}\n\n回到桌面"
    assert with_context("回到桌面", "") == "回到桌面"
    assert with_context("回到桌面", "   ") == "回到桌面"
