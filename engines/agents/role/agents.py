"""执行智能体角色。继承 BaseRole，挂上设备工具和执行技能。

模型与工作流全部写死在本模块（不读数据库、不经接口）：

- 模型：`DeepSeekModelConfig` 里的 provider / model_name / base_url
- 密钥：环境变量 `DEEPSEEK_API_KEY`
- 角色：执行者 60 轮、验收者 30 轮
"""

from __future__ import annotations

import os

from ..config.models import DeepSeekModelConfig
from ..prompt_config import EXECUTOR_PROMPT
from ..prompts.verifier_prompt import verifier_system_prompt
from ..tools_config import build_executor_toolkit, build_verifier_toolkit
from .base import AgentRoleConfig, BaseRole

# 单步尝试的工具轮次预算：30 轮实测会被试错吃满，收尾那次点击反而轮不到。
EXECUTOR_MAX_ITERS = 60
# 验收者只截图 + 判卷，预算维持默认值。
VERIFIER_MAX_ITERS = 30


def _executor_config() -> dict:
    """执行角色的构造参数。工具包每次新建，避免多次运行共用一个实例。"""
    return {
        "provider": DeepSeekModelConfig.provider,
        "model_name": DeepSeekModelConfig.FLASH,
        "base_url": DeepSeekModelConfig.base_url,
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "name": "executor_role",
        "system_prompt": EXECUTOR_PROMPT,
        "toolkit": build_executor_toolkit(),
        "vision": True,
        "max_iters": EXECUTOR_MAX_ITERS,
    }


def _verifier_config() -> dict:
    """验收角色的构造参数。只截图与查日志，预算维持 30 轮。"""
    return {
        "provider": DeepSeekModelConfig.provider,
        "model_name": DeepSeekModelConfig.FLASH,
        "base_url": DeepSeekModelConfig.base_url,
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "name": "verifier_role",
        "system_prompt": verifier_system_prompt(),
        "toolkit": build_verifier_toolkit(),
        "vision": True,
        "max_iters": VERIFIER_MAX_ITERS,
    }


def build_executor() -> BaseRole:
    """按写死的配置创建一个执行角色；每次调用都是独立实例（不共享对话状态）。

    Returns:
        新的执行角色。
    """
    return BaseRole(*AgentRoleConfig(**_executor_config()).load_config())


def build_verifier() -> BaseRole:
    """按写死的配置创建一个验收角色；每次调用都是独立实例。

    Returns:
        新的验收角色。
    """
    return BaseRole(*AgentRoleConfig(**_verifier_config()).load_config())
