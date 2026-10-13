"""配置层：模型能力目录 + 智能体提示词。设备执行专用。"""

from __future__ import annotations

from .prompts.common_prompt import CHINESE_DEMAND
from .prompts.executor_prompt import EXECUTOR_PROMPT
from .prompts.planner_prompt import PLANNER_PROMPT
from .prompts.verifier_prompt import VERIFIER_PROMPT

# ── DeepSeek 模型目录（正式模型名 → 是否支持图片输入）──
#
# 取值依据（2026-10-08 实测）：`GET https://api.deepseek.com/v1/models` 返回的
# `input_modalities` 与官方价目页的「图像理解」一行。旧名 deepseek-v4-flash /
# deepseek-v4-flash-vision-exp 仍可调用但模型已下线、按 Flash 计费，故只作计费别名。
#
# 前端模型清单镜像本目录（`frontend/src/modules/ai-assistant/components/ModelConfigField.vue`），
# 由 tests/graybox/unit/test_ai_deepseek_model_catalog.py 对拍，两侧必须同步修改。
DEEPSEEK_MODELS: dict[str, bool] = {
    "deepseek-flash": True,  # DeepSeek-V4.1-Flash：支持图片输入（多模态）
    "deepseek-v4-pro": False,  # DeepSeek-V4-Pro：纯文本
}


def model_supports_image(provider: str, model_name: str) -> bool | None:
    """该 provider + 模型名是否支持图片输入。

    Args:
        provider: 模型提供商（只认 deepseek）。
        model_name: 模型名（只认 `DEEPSEEK_MODELS` 已登记的名字）。

    Returns:
        True / False 表示已登记模型的图片输入能力；非 deepseek 或未登记的模型名返回 None。
    """
    if str(provider or "").strip().lower() != "deepseek":
        return None
    name = str(model_name or "").strip().lower()
    return DEEPSEEK_MODELS.get(name)


# ── 智能体提示词分配（正文在 prompts/，角色只从本模块取用）──
#
# planner   → PLANNER_PROMPT
# executor  → EXECUTOR_PROMPT    （执行角色唯一系统提示词）
# verifier  → VERIFIER_PROMPT    （验收角色唯一系统提示词）
# 共用片段  → CHINESE_DEMAND     （追加在每轮用户输入末尾）

__all__ = [
    "CHINESE_DEMAND",
    "DEEPSEEK_MODELS",
    "EXECUTOR_PROMPT",
    "PLANNER_PROMPT",
    "VERIFIER_PROMPT",
    "model_supports_image",
]
