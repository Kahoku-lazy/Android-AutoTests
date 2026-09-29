"""planner 页面流指引迁移逻辑（原 test_device_prompts.py 的非提示词部分）。

提示词已收回引擎常量（engines/ai/agents/config.py），提示词读写用例随之下线；
这里只保留与提示词存放位置无关的迁移插入逻辑：0041 给存量库的 prompt_planner
追加编号项，要求「锚点命中才插入、重复调用幂等、可逆、不动用户改写」。
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = [pytest.mark.unit]


def _guidance_module():
    """迁移模块名以数字开头，只能经 importlib 取。"""
    return importlib.import_module(
        "apps.ai_assistant.migrations.0041_add_planner_page_flow_guidance"
    )


def test_planner_guidance_inserted_after_anchor():
    mod = _guidance_module()
    base = f"## 步骤要求\n{mod._ANCHOR}\n\n## 输出字段\n"

    updated = mod.with_guidance(base)

    assert mod._GUIDANCE in updated
    assert updated.index(mod._ANCHOR) < updated.index(mod._GUIDANCE)
    # 除追加行外其余内容逐字保留
    assert updated.replace(f"\n{mod._GUIDANCE}", "") == base


def test_planner_guidance_is_idempotent_and_leaves_user_edits():
    mod = _guidance_module()
    once = mod.with_guidance(f"{mod._ANCHOR}\n")

    assert mod.with_guidance(once) == once  # 已含指引 → 不重复插入

    user_written = "## 我自己重写的 planner，没有锚点"
    assert mod.with_guidance(user_written) == user_written


def test_planner_guidance_is_reversible():
    mod = _guidance_module()
    base = f"{mod._ANCHOR}\n"

    assert mod.without_guidance(mod.with_guidance(base)) == base


def test_seed_planner_prompt_carries_guidance():
    """新装库的种子必须已含指引（与存量库迁移两条下发路径一致）。"""
    mod = _guidance_module()
    seed = importlib.import_module("apps.ai_assistant.migrations.0038_aiagent_device_prompts")

    assert mod._GUIDANCE in seed._SNAPSHOT_PLANNER
    assert mod._ANCHOR in seed._SNAPSHOT_PLANNER
