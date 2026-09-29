"""灰盒·单元测试 — 验收模型五字段契约的提示词迁移（变更 verifier-output-fields）。

零数据库依赖：输入取「0038 平台原文经 0044、0047 处理后的当前库中原文」，断言六条口径 ——
1. 六处锚点全部替换（照抄路径 / 日志证据措辞 / 验收段三条 / 输出字段 / 输出格式约束 / 案例）；
2. 输出字段段不再有 action / assert，改为五字段且含 logAssertionTimer；
3. 日志证据段不再出现判 true / false 的措辞；
4. 幂等，且管理员改写过的行一律不动；
5. 回滚可逆（apply → revert 回到当前原文）。
"""

from __future__ import annotations

import importlib

migration = importlib.import_module("apps.ai_assistant.migrations.0048_verifier_output_fields")
seed = importlib.import_module("apps.ai_assistant.migrations.0038_aiagent_device_prompts")
log_evidence_guidance = importlib.import_module(
    "apps.ai_assistant.migrations.0044_add_verifier_log_evidence_guidance"
)
executor_fields = importlib.import_module(
    "apps.ai_assistant.migrations.0047_executor_output_fields"
)

ADMIN_REWRITTEN_VERIFIER = "## 角色\n你是验收模型。\n\n## 输出字段\n- result：结果\n"


def current_prompt() -> str:
    """当前库中原文：0038 快照 → 0047（执行侧输入说明）→ 0044（日志证据指引）。"""
    text = executor_fields.apply_contract(seed._SNAPSHOT_VERIFIER, executor_fields._VERIFIER_PAIRS)
    return log_evidence_guidance.with_log_evidence_guidance(text)


def apply_current() -> str:
    return migration.apply_contract(current_prompt(), migration._VERIFIER_PAIRS)


def test_output_fields_replaced() -> None:
    after = apply_current()
    assert "- action：被验证的操作。" not in after
    assert "- assert：断言。" not in after
    assert "- result：PASS（实际结果符合断言）或 FAIL（不符合/无法确认）。" in after
    assert "- click_timer：点击前的时间戳" in after
    assert "- logAssertionTimer：检测到日志关键词的时间戳" in after
    assert "- screenshot：验证截图的相对路径" in after
    assert "- actual：截图里的实际结果（实际看到了什么）。" in after
    assert "只含 result / click_timer / logAssertionTimer / screenshot / actual 五个键" in after


def test_path_copy_rule_replaced() -> None:
    after = apply_current()
    assert "你的最终 JSON 不要编造或抄写文件路径" not in after
    assert "把该路径**原文照抄**进最终 JSON 的 screenshot" in after


def test_log_evidence_wording_uses_pass_fail() -> None:
    after = apply_current()
    assert "支持判 PASS" in after
    assert "才可判 PASS；否则判 FAIL 并在 actual 中说明" in after
    assert "不得据此判 PASS" in after
    assert "判 true" not in after
    assert "判 false" not in after


def test_verdict_bullets_use_pass_fail() -> None:
    after = apply_current()
    assert "- result：PASS 表示操作成功（实际结果符合断言），FAIL 表示未成功或无法确认。" in after
    assert "偏离则判 FAIL 并在 actual 中说明原因" in after
    assert "true 表示操作成功" not in after


def test_example_json_has_five_keys() -> None:
    after = apply_current()
    assert '"logAssertionTimer": "2026-09-28 17:01:13.100"' in after
    assert '"result": true' not in after


def test_idempotent() -> None:
    once = apply_current()
    assert migration.apply_contract(once, migration._VERIFIER_PAIRS) == once


def test_admin_rewritten_prompt_untouched() -> None:
    assert (
        migration.apply_contract(ADMIN_REWRITTEN_VERIFIER, migration._VERIFIER_PAIRS)
        == ADMIN_REWRITTEN_VERIFIER
    )
    assert migration.apply_contract("", migration._VERIFIER_PAIRS) == ""


def test_rollback_is_reversible() -> None:
    assert migration.revert_contract(apply_current(), migration._VERIFIER_PAIRS) == current_prompt()
