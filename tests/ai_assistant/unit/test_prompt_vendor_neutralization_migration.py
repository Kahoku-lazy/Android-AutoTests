"""灰盒·单元测试 — 提示词厂商样例收敛迁移（变更 purge-govee-business-assets）。

零数据库依赖：用 `0038` 的提示词快照做输入，断言 `0065` 的四条口径 ——
1. 应用名、机型、真机序列号都被替换为中性占位；
2. 提示词其余结构不动（标题、字段、步骤编号都在）；
3. 幂等，且不含目标词的行原样返回（管理员改写不动）；
4. 空串安全。

期望值全部从迁移自身的替换表派生，不在用例里重写厂商标识，避免用例本身成为
新的泄露面。
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = [pytest.mark.unit]

migration = importlib.import_module(
    "backend.apps.ai_assistant.migrations.0065_neutralize_prompt_vendor_samples"
)
seed = importlib.import_module("backend.apps.ai_assistant.migrations.0038_aiagent_device_prompts")


def _assert_clean(text: str, label: str) -> None:
    """断言文本里不再残留任何受限标识。"""
    for old, _new in migration._PHRASE_REPLACEMENTS:
        assert old not in text, f"{label} 仍残留 {old!r}"
    assert migration._BARE_TOKEN.search(text) is None, f"{label} 仍残留裸标识"


def test_planner_snapshot_is_neutralized() -> None:
    after = migration.neutralize(seed._SNAPSHOT_PLANNER)
    _assert_clean(after, "planner")
    assert after.startswith("\n## 角色")
    assert "## 步骤要求" in after
    assert "## 案例" in after
    assert "目标应用" in after
    assert "MV-1000" in after
    assert "SERIAL-EXAMPLE" in after


def test_verifier_snapshot_is_neutralized() -> None:
    after = migration.neutralize(seed._SNAPSHOT_VERIFIER)
    _assert_clean(after, "verifier")
    assert "MV-1000 是设备型号" in after


def test_executor_snapshot_is_untouched() -> None:
    """executor 快照不含目标词，必须逐字返回。"""
    assert migration.neutralize(seed._SNAPSHOT_EXECUTOR) == seed._SNAPSHOT_EXECUTOR


def test_idempotent() -> None:
    once = migration.neutralize(seed._SNAPSHOT_PLANNER)
    assert migration.neutralize(once) == once


def test_admin_rewritten_prompt_untouched() -> None:
    rewritten = "## 角色\n你是执行模型。\n\n## 输出字段\n- result：结果\n"
    assert migration.neutralize(rewritten) == rewritten


@pytest.mark.parametrize("blank", ["", None])
def test_blank_input_is_safe(blank: str | None) -> None:
    assert migration.neutralize(blank) == blank
