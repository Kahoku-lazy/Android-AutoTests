"""灰盒·单元测试 — 执行模型三字段契约的提示词迁移（变更 executor-output-fields）。

零数据库依赖：用 0038 的平台原文快照做输入，断言迁移函数的四条口径 ——
1. executor 四处锚点全部替换（输出字段 / 输出格式约束 / 操作后截图命令行 / 案例 JSON）；
2. verifier 输入说明行替换；
3. 幂等，且管理员改写过的行一律不动；
4. 回滚可逆（apply → revert 回到平台原文）。
"""

from __future__ import annotations

import importlib

# 迁移模块名以数字开头，只能用 importlib 按字符串路径导入
migration = importlib.import_module("apps.ai_assistant.migrations.0047_executor_output_fields")
seed = importlib.import_module("apps.ai_assistant.migrations.0038_aiagent_device_prompts")

ADMIN_REWRITTEN_EXECUTOR = "## 角色\n你是执行模型。\n\n## 输出字段\n- result：结果\n"


def _apply_executor() -> str:
    return migration.apply_contract(seed._SNAPSHOT_EXECUTOR, migration._EXECUTOR_PAIRS)


def test_executor_anchors_replaced() -> None:
    after = _apply_executor()
    assert "- action：你执行的操作。" not in after
    assert "- message：操作说明，或遇到的问题。" not in after
    assert "- click_timer：点击前的时间戳" in after
    assert "- screenshot：点击后截图的相对路径" in after
    assert "调 screenshot_page(serial) 截图一次，对比画面确认操作是否成功" not in after
    assert "调 screenshot_page(serial, keep_local=true) 截图一次，对比画面确认操作是否成功" in after
    # 案例 JSON 只保留三键
    assert '"click_timer": "2026-09-28 17:01:12.645"' in after
    assert '"message": "已点击音乐入口' not in after
    # 操作前定位那一步不要求落盘路径（只有操作后确认那一步改）
    assert "- 调 screenshot_page(serial) 截图一次，看图识别目标元素及其位置" in after


def test_verifier_input_line_replaced() -> None:
    after = migration.apply_contract(seed._SNAPSHOT_VERIFIER, migration._VERIFIER_PAIRS)
    assert "- 执行模型的结果：result（PASS/FAIL）、点击前时间戳 click_timer、" in after
    assert "- 执行模型的结果：action、result（PASS/FAIL）、message" not in after
    # 验收模型自己的输出字段契约不受影响
    assert "- action：被验证的操作。" in after


def test_idempotent() -> None:
    once = _apply_executor()
    assert migration.apply_contract(once, migration._EXECUTOR_PAIRS) == once


def test_admin_rewritten_prompt_untouched() -> None:
    assert (
        migration.apply_contract(ADMIN_REWRITTEN_EXECUTOR, migration._EXECUTOR_PAIRS)
        == ADMIN_REWRITTEN_EXECUTOR
    )
    assert migration.apply_contract("", migration._EXECUTOR_PAIRS) == ""


def test_rollback_is_reversible() -> None:
    assert (
        migration.revert_contract(_apply_executor(), migration._EXECUTOR_PAIRS)
        == seed._SNAPSHOT_EXECUTOR
    )
    verifier_after = migration.apply_contract(seed._SNAPSHOT_VERIFIER, migration._VERIFIER_PAIRS)
    assert (
        migration.revert_contract(verifier_after, migration._VERIFIER_PAIRS)
        == seed._SNAPSHOT_VERIFIER
    )
