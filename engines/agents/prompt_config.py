"""配置层：模型能力目录 + 智能体提示词。设备执行与家电用例编写共用。"""

from __future__ import annotations

from .prompts.case_module_planner_prompt import CASE_MODULE_PLANNER_PROMPT
from .prompts.case_verifier_prompt import CASE_VERIFIER_GOAL_PROMPT, CASE_VERIFIER_PROMPT
from .prompts.case_writer_prompt import CASE_WRITER_GOAL_PROMPT, CASE_WRITER_PROMPT
from .prompts.common_prompt import CHINESE_DEMAND
from .prompts.executor_prompt import EXECUTOR_PROMPT
from .prompts.verifier_prompt import VERIFIER_PROMPT

# ── DeepSeek 模型目录（正式模型名 → 是否支持图片输入）──
#
# 取值依据（2026-10-17 官方价目页）：`deepseek-flash` 现为 DeepSeek-V4.1-Flash-1017，
# `deepseek-v4-pro` 现为 DeepSeek-V4-Pro-0813。图像理解以价目页「图像理解」一行为准。
# 旧名 deepseek-v4-flash / deepseek-v4-flash-vision-exp 仍可调用，但对应模型已下线，
# 请求由 Flash-1017 提供并按 Flash 计费，故只作计费别名。
#
# 前端模型清单镜像本目录（`frontend/src/modules/ai-assistant/components/ModelConfigField.vue`），
# 由 tests/graybox/unit/test_ai_deepseek_model_catalog.py 对拍，两侧必须同步修改。
DEEPSEEK_MODELS: dict[str, bool] = {
    "deepseek-flash": True,  # DeepSeek-V4.1-Flash-1017：支持图片输入（多模态）
    "deepseek-v4-pro": False,  # DeepSeek-V4-Pro-0813：纯文本
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


# 智能体提示词分配（正文在 prompts/，角色只从本模块取用）
#
# executor      → EXECUTOR_PROMPT        （设备执行角色唯一系统提示词）
# verifier      → VERIFIER_PROMPT        （设备验收角色唯一系统提示词）
# case_writer   → CASE_WRITER_PROMPT     （家电用例编写角色唯一系统提示词）
# case_verifier → CASE_VERIFIER_PROMPT   （家电用例验收角色唯一系统提示词）
# case_planner  → CASE_MODULE_PLANNER_PROMPT（家电用例模块规划角色唯一系统提示词）
# 共用片段      → CHINESE_DEMAND         （追加在每轮用户输入末尾）

__all__ = [
    "CASE_MODULE_PLANNER_PROMPT",
    "CASE_VERIFIER_GOAL_PROMPT",
    "CASE_VERIFIER_PROMPT",
    "CASE_WRITER_GOAL_PROMPT",
    "CASE_WRITER_PROMPT",
    "CHINESE_DEMAND",
    "DEEPSEEK_MODELS",
    "EXECUTOR_PROMPT",
    "VERIFIER_PROMPT",
    "model_supports_image",
]
