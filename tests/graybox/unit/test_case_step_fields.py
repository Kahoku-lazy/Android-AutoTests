"""用例步骤的结构化字段：anchor / log 的解析与拒绝。"""

from __future__ import annotations

import pytest

from engines.agents.workflow.case_file import LogEvidence, validate_platform_yaml

pytestmark = [pytest.mark.unit]


def _case(step_block: str) -> str:
    """把一段步骤 YAML 包成一份单用例 YAML。"""
    return f"""
- title: 定时功能测试
  steps:
{step_block}
""".strip()


def test_plain_step_has_no_structured_fields():
    """只有 action / assert 的旧用例保持兼容，两个新字段为 None。"""
    cases, reason = validate_platform_yaml(_case("    - action: 打开定时页\n      assert: 定时页可见"))

    assert reason == ""
    step = cases[0].steps[0]
    assert step.action == "打开定时页"
    assert step.expected == "定时页可见"
    assert step.anchor is None
    assert step.log is None


def test_anchor_and_log_are_parsed():
    """anchor 与 log 齐全时按字段收好。"""
    text = _case(
        "    - action: 设置 5:00 定时\n"
        "      assert: 列表出现 5:00\n"
        "      anchor:\n"
        "        page: 定时页\n"
        "        entry: 详情页左上「定时」\n"
        "      log:\n"
        "        sku: H6810\n"
        "        port: 7005\n"
        "        keyword: timer_configs_set_success"
    )

    cases, reason = validate_platform_yaml(text)

    assert reason == ""
    step = cases[0].steps[0]
    assert step.anchor == {"page": "定时页", "entry": "详情页左上「定时」"}
    assert step.log == LogEvidence(sku="H6810", port=7005, keyword="timer_configs_set_success")


def test_unknown_anchor_key_is_rejected():
    """anchor 的键只允许 page / entry / target。"""
    text = _case("    - action: 点一下\n      assert: 有反应\n      anchor:\n        where: 首页")

    cases, reason = validate_platform_yaml(text)

    assert cases == []
    assert "anchor 含未知键" in reason


def test_missing_keyword_is_rejected():
    """log 出现时关键词必填。"""
    text = _case(
        "    - action: 点一下\n      assert: 有反应\n"
        "      log:\n        sku: H6810\n        port: 7005"
    )

    cases, reason = validate_platform_yaml(text)

    assert cases == []
    assert "log.keyword 缺失" in reason


def test_bad_port_is_rejected():
    """端口必须是正整数。"""
    text = _case(
        "    - action: 点一下\n      assert: 有反应\n"
        "      log:\n        sku: H6810\n        port: 0\n        keyword: switch_on"
    )

    cases, reason = validate_platform_yaml(text)

    assert cases == []
    assert "log.port 必须是正整数" in reason


def test_overlong_anchor_value_is_rejected():
    """锚点值超过上限时拒绝，避免把长文塞进步骤提示。"""
    long_text = "很长的入口描述" * 30
    text = _case(
        f"    - action: 点一下\n      assert: 有反应\n      anchor:\n        entry: {long_text}"
    )

    cases, reason = validate_platform_yaml(text)

    assert cases == []
    assert "超过 120 字" in reason
