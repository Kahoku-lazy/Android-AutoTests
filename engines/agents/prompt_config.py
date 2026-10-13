"""配置层：模型连接配置 + 模型能力目录 + 智能体提示词。设备执行专用。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .prompts.common_prompt import CHINESE_DEMAND
from .prompts.executor_prompt import EXECUTOR_PROMPT
from .prompts.planner_prompt import PLANNER_PROMPT
from .prompts.verifier_prompt import VERIFIER_PROMPT


@dataclass
class ModelConfig:
    """单个模型的连接配置（纯数据，供 `create_model` 建立连接）。"""

    provider: str = "deepseek"  # 提供商：deepseek / dashscope
    model_name: str = ""  # 模型名（如 deepseek-flash / qwen3.6-plus）
    api_key: str = ""  # 已解密的 API Key（Django 层解密后传入）
    base_url: str = ""  # 已解析默认值的 base_url（空则用 provider 默认端点）


@dataclass
class DeviceExecutionConfig:
    """设备执行三角色配置（规划 / 执行 / 验收）+ 每步最大重试次数。"""

    planner: ModelConfig = field(default_factory=ModelConfig)  # 规划模型连接
    executor: ModelConfig = field(default_factory=ModelConfig)  # 执行模型连接（多模态）
    verifier: ModelConfig = field(default_factory=ModelConfig)  # 验收模型连接（多模态）
    max_loops: int = 3  # 每步「执行↔验收」最大重试次数
    log_wait_seconds: float = 0.0  # 读日志证据前等待秒数


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
    "DeviceExecutionConfig",
    "EXECUTOR_PROMPT",
    "ModelConfig",
    "PLANNER_PROMPT",
    "VERIFIER_PROMPT",
    "model_supports_image",
]
