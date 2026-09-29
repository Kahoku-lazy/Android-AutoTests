"""灰盒·单元测试 — 验收提示词的六字段与「两条件」迁移（变更 verifier-log-check-tool）。

零数据库依赖：输入取「0048 / 0049 处理后的当前库中原文」，断言五条口径 ——
1. 通用查询指引换成规则检查工具指引（并写明两条件）；
2. 验收判定段补上「日志检测到 + 截图确认才 PASS」；
3. 输出字段：时间戳来源改为检查工具返回、新增 `logAssertionInfo`；
4. 输出格式约束与案例 JSON 都变成六个键；
5. 幂等、已改写行不动、回滚可逆。
"""

from __future__ import annotations

import importlib

migration = importlib.import_module("apps.ai_assistant.migrations.0050_verifier_log_check_contract")
fields_0048 = importlib.import_module("apps.ai_assistant.migrations.0048_verifier_output_fields")
tool_0049 = importlib.import_module(
    "apps.ai_assistant.migrations.0049_add_verifier_log_tool_guidance"
)
seed = importlib.import_module("apps.ai_assistant.migrations.0038_aiagent_device_prompts")
guidance_0044 = importlib.import_module(
    "apps.ai_assistant.migrations.0044_add_verifier_log_evidence_guidance"
)

ADMIN_REWRITTEN_VERIFIER = "## 角色\n你是验收模型。\n\n## 输出字段\n- result：结果\n"


def current_prompt() -> str:
    """当前库中原文：0038 → 0044 → 0047 输入行 → 0048 六处 → 0049 自查指引。"""
    text = executor_input = seed._SNAPSHOT_VERIFIER
    text = guidance_0044.with_log_evidence_guidance(text)
    # 0047 的 verifier 输入行替换（同一份纯函数）
    executor_fields = importlib.import_module(
        "apps.ai_assistant.migrations.0047_executor_output_fields"
    )
    text = executor_fields.apply_contract(text, executor_fields._VERIFIER_PAIRS)
    assert executor_input  # 仅避免未使用变量告警
    text = fields_0048.apply_contract(text, fields_0048._VERIFIER_PAIRS)
    return tool_0049.with_log_tool_guidance(text)


def apply_current() -> str:
    return migration.apply_contract(current_prompt(), migration._PAIRS)


def test_guidance_switches_to_check_tool_with_two_conditions() -> None:
    after = apply_current()
    assert "read_device_log" not in after
    assert "check_device_log" in after
    assert "日志检测到与截图确认两个条件都满足才可判 PASS" in after
    assert "未检测到该关键词时必须判 FAIL" in after


def test_output_fields_add_log_assertion_info() -> None:
    after = apply_current()
    assert "- logAssertionInfo：本轮检查的日志关键词" in after
    assert "取 check_device_log 返回的命中时间戳" in after
    assert "取输入「设备日志证据」里命中关键词那一次" not in after
    assert "六个键" in after


def test_example_json_has_six_keys() -> None:
    after = apply_current()
    assert '"logAssertionInfo": "switch_on"' in after
    assert "五个键" not in after


def test_idempotent_and_rewritten_untouched() -> None:
    once = apply_current()
    assert migration.apply_contract(once, migration._PAIRS) == once
    assert (
        migration.apply_contract(ADMIN_REWRITTEN_VERIFIER, migration._PAIRS)
        == ADMIN_REWRITTEN_VERIFIER
    )
    assert migration.apply_contract("", migration._PAIRS) == ""


def test_rollback_is_reversible() -> None:
    assert migration.revert_contract(apply_current(), migration._PAIRS) == current_prompt()
