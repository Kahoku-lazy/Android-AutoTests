"""灰盒·单元测试 — 验收提示词的「可自查日志」指引迁移（变更 log-read-from-files）。

零数据库依赖：断言迁移里的纯函数四条口径 ——
1. 字段含平台原文锚点且尚无指引时写入（写在锚点之后）；
2. 已含指引时幂等（不重复写）；
3. 管理员改写过（锚点已不在）时一律不动；
4. 回滚可逆。
"""

from __future__ import annotations

import importlib

migration = importlib.import_module(
    "apps.ai_assistant.migrations.0049_add_verifier_log_tool_guidance"
)

CURRENT_VERIFIER = (
    "\n\n## 角色\n你是验收模型。\n\n## 验收时\n"
    "- 重点对比 assert（断言/期望结果）与截图的真实状态，判断操作是否成功。\n"
    "- 等级「强证据」：窗口内首次出现且动作前基线未出现同名日志，可与截图共同支持判 PASS。\n"
    "- 输入里没有日志证据块时，只依据截图判断，不要臆造日志内容。\n"
    "- actual：描述截图里的实际结果（实际看到了什么）。\n"
)

ADMIN_REWRITTEN_VERIFIER = "## 角色\n你是验收模型。\n\n## 验收时\n- 自己看图判断。\n"


def test_writes_guidance_after_anchor() -> None:
    after = migration.with_log_tool_guidance(CURRENT_VERIFIER)
    assert migration._MARKER in after
    assert "read_device_log" in after
    assert "已落盘的日志文件" in after
    assert after.index("不要臆造日志内容") < after.index("read_device_log")


def test_idempotent() -> None:
    once = migration.with_log_tool_guidance(CURRENT_VERIFIER)
    assert migration.with_log_tool_guidance(once) == once


def test_admin_rewritten_prompt_untouched() -> None:
    assert migration.with_log_tool_guidance(ADMIN_REWRITTEN_VERIFIER) == ADMIN_REWRITTEN_VERIFIER
    assert migration.with_log_tool_guidance("") == ""


def test_rollback_is_reversible() -> None:
    after = migration.with_log_tool_guidance(CURRENT_VERIFIER)
    assert migration.without_log_tool_guidance(after) == CURRENT_VERIFIER
