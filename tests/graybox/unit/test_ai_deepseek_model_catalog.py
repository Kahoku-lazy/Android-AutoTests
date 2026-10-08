"""灰盒·单元测试 — DeepSeek 模型清单的三处一致性与能力标注守护。

守护三件事（本单之前**没有任何测试**守着它们，导致清单可以静默漂移）：

1. 前端模型清单（`ModelConfigField.vue`）≡ 引擎模型目录（`engines/ai/agents/config.py` 的
   `DEEPSEEK_MODELS`），含「是否支持图片」能力位；
2. 目录里的每个模型都能在价目表**正式命中**、不是靠默认档兜底计费；
3. 两份价目表（后端 `apps/ai_assistant/deepseek_billing.py` 与引擎 `engines/ai/billing/billing.py`）
   逐键、逐值、别名与默认档完全一致。

读源码对拍属仓库既有范式（见 tests/AGENTS.md「契约对拍测试」）：只读、不改、零外部依赖。
"""

import re

from pathlib import Path

import pytest

from apps.ai_assistant import deepseek_billing as app_billing
from apps.ai_assistant.provider_registry import VALID_PROVIDERS
from engines.ai.agents.config import DEEPSEEK_MODELS, model_supports_image
from engines.ai.billing import billing as engine_billing

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]

ROOT = Path(__file__).resolve().parents[3]
VUE_PATH = (
    ROOT / "frontend" / "src" / "modules" / "ai-assistant" / "components" / "ModelConfigField.vue"
)

# 规模下限：识别规则退化（例如正则失配）时计数骤降，测试随即失败而不是给出虚假的"一致"
MIN_MODELS = 2


def _deepseek_block() -> str:
    """取出前端清单里 DeepSeek 那一段（到数组结尾为止）。

    锚点刻意不依赖任何具体 provider：清单收敛（例如移除某个 provider）不应让本守卫失配。
    """
    text = VUE_PATH.read_text(encoding="utf-8")
    match = re.search(r'value:\s*"deepseek".*?\n\]', text, re.DOTALL)
    assert match, "未能在 ModelConfigField.vue 中定位 deepseek 模型清单（识别规则可能已失效）"
    return match.group(0)


def test_frontend_provider_list_matches_backend_valid_providers() -> None:
    """前端「模型服务」清单必须恰为后端合法 provider 集合（平台只支持 DeepSeek 与阿里百炼）。"""
    text = VUE_PATH.read_text(encoding="utf-8")
    block = re.search(r"const providers.*?\n\]", text, re.DOTALL)
    assert block, "未能在 ModelConfigField.vue 中定位 providers 清单（识别规则可能已失效）"

    values = re.findall(r'value:\s*"([^"]+)"', block.group(0))
    assert len(values) >= 2, f"前端 provider 清单识别到的项数骤降：{values}"
    assert set(values) == set(VALID_PROVIDERS), (
        f"前端清单 {sorted(set(values))} 与后端合法集合 {sorted(VALID_PROVIDERS)} 不一致"
    )


def test_frontend_list_matches_engine_catalog() -> None:
    """前端清单的模型名集合与引擎目录键集合相等。"""
    block = _deepseek_block()
    names = re.findall(r'name:\s*"([^"]+)"', block)
    assert len(names) >= MIN_MODELS, f"前端 deepseek 清单识别到的模型数骤降：{names}"
    assert set(names) == set(DEEPSEEK_MODELS), (
        f"前端清单 {sorted(set(names))} 与引擎目录 {sorted(DEEPSEEK_MODELS)} 不一致"
    )


def test_frontend_multimodal_flags_match_engine_catalog() -> None:
    """前端标「多模态」的模型，必须正是引擎目录中支持图片的那些。"""
    block = _deepseek_block()
    flagged = set(re.findall(r'name:\s*"([^"]+)"\s*,\s*multimodal:\s*true', block))
    expected = {name for name, ok in DEEPSEEK_MODELS.items() if ok}
    assert flagged == expected, (
        f"前端多模态标注 {sorted(flagged)} 与引擎目录 {sorted(expected)} 不一致"
    )


def test_every_catalog_model_hits_formal_price_entry() -> None:
    """目录内模型必须命中正式价目条目——不得靠默认档兜底（兜底会静默按 Flash 价计费）。"""
    for name in DEEPSEEK_MODELS:
        assert name in app_billing.DEEPSEEK_PRICING, f"{name} 在价目表中没有正式条目"
        assert name in engine_billing.DEEPSEEK_PRICING, f"{name} 在引擎价目表中没有正式条目"
        assert app_billing._resolve_price(name) is app_billing.DEEPSEEK_PRICING[name], (
            f"{name} 的价目解析落到了默认档而非自身条目"
        )


def test_legacy_names_alias_to_a_formal_model() -> None:
    """旧名/通用名一律作别名，且别名目标必须是正式模型（否则解析会落到默认档）。"""
    for alias, target in app_billing._DEEPSEEK_MODEL_ALIASES.items():
        assert target in app_billing.DEEPSEEK_PRICING, f"别名 {alias} → {target} 不是正式模型条目"
    assert app_billing._DEFAULT_DEEPSEEK_MODEL in app_billing.DEEPSEEK_PRICING
    # 已下线的旧名仍在别名表中（厂商仍接受、按 Flash 计费）
    for legacy in ("deepseek-v4-flash", "deepseek-v4-flash-vision-exp"):
        assert legacy in app_billing._DEEPSEEK_MODEL_ALIASES


def test_two_price_tables_are_identical() -> None:
    """两份价目表（后端与引擎）逐键、逐值、别名、默认档一致。"""
    assert app_billing.DEEPSEEK_PRICING == engine_billing.DEEPSEEK_PRICING
    assert app_billing._DEEPSEEK_MODEL_ALIASES == engine_billing._DEEPSEEK_MODEL_ALIASES
    assert app_billing._DEFAULT_DEEPSEEK_MODEL == engine_billing._DEFAULT_DEEPSEEK_MODEL
    assert app_billing._PEAK_MULTIPLIER == engine_billing._PEAK_MULTIPLIER


def test_model_supports_image_only_knows_catalog() -> None:
    """能力判断只认目录：目录内按登记返回，其他 provider 与未知模型名返回 None（不误报）。"""
    assert model_supports_image("deepseek", "deepseek-flash") is True
    assert model_supports_image("deepseek", "deepseek-v4-pro") is False
    assert model_supports_image("deepseek", "deepseek-v4-flash") is None  # 旧名不在目录内
    assert model_supports_image("dashscope", "qwen-max") is None
    assert model_supports_image("deepseek", "") is None


def _assemble(role_cls, model_name: str):
    from engines.ai.agents import ModelConfig

    return role_cls(ModelConfig(provider="deepseek", model_name=model_name, api_key="k"), [])


def test_vision_role_bound_to_text_only_model_logs_warning(caplog):
    """视觉角色（执行/验收）绑定已知纯文本模型 → 装配期告警，且装配不中断。"""
    import logging

    from engines.ai.agents import ExecutorRole

    with caplog.at_level(logging.WARNING, logger="ai_assistant.model"):
        role = _assemble(ExecutorRole, "deepseek-v4-pro")

    assert role is not None  # 只提醒、不拦截
    messages = [r.getMessage() for r in caplog.records]
    assert any("装配提醒" in m and "executor" in m and "deepseek-v4-pro" in m for m in messages), (
        f"未记录含角色名与模型名的装配告警，实际日志：{messages}"
    )


def test_no_warning_for_matching_or_unknown_models(caplog):
    """多模态模型、以及非视觉角色 / 未知模型名，都不应产生该告警。"""
    import logging

    from engines.ai.agents import ExecutorRole, PlannerRole

    with caplog.at_level(logging.WARNING, logger="ai_assistant.model"):
        _assemble(ExecutorRole, "deepseek-flash")  # 多模态 → 不告警
        _assemble(PlannerRole, "deepseek-v4-pro")  # 规划角色不需要图片 → 不告警
        _assemble(ExecutorRole, "自建视觉模型")  # 未知能力 → 不告警（避免误报）

    messages = [r.getMessage() for r in caplog.records]
    assert not any("装配提醒" in m for m in messages), f"出现了不该有的告警：{messages}"
