"""灰盒·单元测试 — verifier 提示词的日志证据指引迁移（变更 add-device-log-evidence）。

零数据库依赖：只断言迁移里的纯函数三条口径 ——
1. 字段含平台原文锚点且尚无指引时插入；
2. 已含指引时幂等（不重复插）；
3. 管理员改写过（锚点已不在）时一律不动；回滚可逆。
"""

from __future__ import annotations

import importlib

# 迁移模块名以数字开头，只能用 importlib 按字符串路径导入
migration = importlib.import_module(
    "apps.ai_assistant.migrations.0044_add_verifier_log_evidence_guidance"
)

SEEDED_VERIFIER = (
    "\n\n## 角色\n你是验收模型，负责确认执行模型完成的每一步是否真实达成。\n\n"
    "## 验收时\n"
    "- 用 screenshot_page(serial, keep_local=true) 截图一次查看当前页面真实状态，"
    "不要只凭执行描述判断。\n"
    "- 重点对比 assert（断言/期望结果）与截图的真实状态，判断操作是否成功。\n"
    "- actual：描述截图里的实际结果（实际看到了什么）。\n"
)

ADMIN_REWRITTEN_VERIFIER = (
    "## 角色\n你是验收模型。\n\n## 验收时\n- 自己看图判断，别信执行模型的嘴。\n"
)


def test_inserts_guidance_after_anchor() -> None:
    after = migration.with_log_evidence_guidance(SEEDED_VERIFIER)
    assert migration._MARKER in after
    assert "不得单独作为通过依据" in after
    # 插在锚点之后、后续条目之前
    assert (
        after.index("- 重点对比 assert") < after.index("设备日志证据") < after.index("- actual：")
    )


def test_idempotent() -> None:
    once = migration.with_log_evidence_guidance(SEEDED_VERIFIER)
    twice = migration.with_log_evidence_guidance(once)
    assert once == twice


def test_admin_rewritten_prompt_untouched() -> None:
    assert (
        migration.with_log_evidence_guidance(ADMIN_REWRITTEN_VERIFIER) == ADMIN_REWRITTEN_VERIFIER
    )


def test_rollback_is_reversible() -> None:
    after = migration.with_log_evidence_guidance(SEEDED_VERIFIER)
    assert migration.without_log_evidence_guidance(after) == SEEDED_VERIFIER
