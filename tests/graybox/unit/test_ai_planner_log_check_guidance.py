"""灰盒·单元测试 — planner 提示词的日志核对标记指引迁移（变更 executor-step-log-check）。

零数据库依赖：只断言迁移里的纯函数三条口径 ——
1. 字段含平台原文锚点且尚无指引时插入（插在 assert 条目之后）；
2. 已含指引时幂等（不重复插）；
3. 管理员改写过（锚点已不在）时一律不动；回滚可逆。
"""

from __future__ import annotations

import importlib

# 迁移模块名以数字开头，只能用 importlib 按字符串路径导入
migration = importlib.import_module(
    "apps.ai_assistant.migrations.0046_add_planner_log_check_guidance"
)

SEEDED_PLANNER = (
    "\n## 角色\n接到用户需求后，你负责把 UI 自动化任务规划成可执行的步骤序列。\n\n"
    "## 输出字段\n"
    "- goal：一句话总目标。\n"
    "- steps：操作步骤列表，每项含：\n"
    "  - action：一个操作（一个步骤只一个操作；点击类先找元素再点击）。\n"
    "  - assert：该操作的断言，即操作后屏幕上可观察到的期望结果（供验证模型比对）。\n"
    "\n## 输出格式约束\n最终回答必须只输出一个 JSON 字符串。\n"
)

ADMIN_REWRITTEN_PLANNER = (
    "## 角色\n你是规划模型。\n\n## 输出字段\n- goal：目标\n- steps：步骤（自己看着办）\n"
)


def test_inserts_guidance_after_anchor() -> None:
    after = migration.with_log_check_guidance(SEEDED_PLANNER)
    assert migration._MARKER in after
    assert "断言要看设备上报的日志" in after
    # 插在 assert 条目之后、输出格式约束之前
    assert (
        after.index("- assert：该操作的断言")
        < after.index("log_check")
        < after.index("## 输出格式约束")
    )


def test_idempotent() -> None:
    once = migration.with_log_check_guidance(SEEDED_PLANNER)
    twice = migration.with_log_check_guidance(once)
    assert once == twice


def test_admin_rewritten_prompt_untouched() -> None:
    assert migration.with_log_check_guidance(ADMIN_REWRITTEN_PLANNER) == ADMIN_REWRITTEN_PLANNER


def test_rollback_is_reversible() -> None:
    after = migration.with_log_check_guidance(SEEDED_PLANNER)
    assert migration.without_log_check_guidance(after) == SEEDED_PLANNER
