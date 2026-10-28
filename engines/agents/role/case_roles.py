"""
python -m 调试路径: engines.agents.role.case_roles

本模块的业务功能如下：
1. build_case_planner: 创建家电测试用例模块规划角色（只切需求区间，不写用例）。
2. build_case_writer: 创建家电测试用例编写角色（纯文本，不操作设备）。
3. build_case_verifier: 创建家电测试用例验收角色（只判卷，不改写用例）。
"""

from __future__ import annotations

import os

from ..config.models import DeepSeekModelConfig
from ..prompt_config import (
    CASE_MODULE_PLANNER_PROMPT,
    CASE_VERIFIER_GOAL_PROMPT,
    CASE_VERIFIER_PROMPT,
    CASE_WRITER_GOAL_PROMPT,
    CASE_WRITER_PROMPT,
)
from ..tools_config import build_case_authoring_toolkit, build_case_writer_toolkit
from .base import AgentRoleConfig, BaseRole

CASE_PLANNER_NAME = "case_planner_role"
CASE_WRITER_NAME = "case_writer_role"
CASE_VERIFIER_NAME = "case_verifier_role"

# 编写、验收与规划都用 FLASH：长文档生成慢、成本高，三个角色统一走 Flash；要换只改这三个常量。
CASE_PLANNER_MODEL = DeepSeekModelConfig.FLASH
CASE_WRITER_MODEL = DeepSeekModelConfig.FLASH
CASE_VERIFIER_MODEL = DeepSeekModelConfig.FLASH

# 规划/验收没有工具；编写角色只带计划模式工具，轮次预算要覆盖计划创建与阶段更新。
CASE_PLANNER_MAX_ITERS = 2
CASE_WRITER_MAX_ITERS = 20
CASE_VERIFIER_MAX_ITERS = 4


def _api_key() -> str:
    """读取 DeepSeek 密钥；没有时返回空串，由模型调用阶段报错。"""
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


def _role_config(
    name: str,
    system_prompt: str,
    model_name: str,
    max_iters: int,
    *,
    plan_mode: bool = False,
) -> dict:
    """拼一个用例角色的构造参数；工具包每次新建，避免多次运行共用实例。"""
    return {
        "provider": DeepSeekModelConfig.provider,
        "model_name": model_name,
        "base_url": DeepSeekModelConfig.base_url,
        "api_key": _api_key(),
        "name": name,
        "system_prompt": system_prompt,
        "toolkit": (build_case_writer_toolkit() if plan_mode else build_case_authoring_toolkit()),
        "vision": False,
        "max_iters": max_iters,
    }


def build_case_planner() -> BaseRole:
    """按写死的配置创建一个模块规划角色；每次调用都是独立实例。

    Returns:
        新的模块规划角色。

    Raises:
        ValueError: 模型提供商不在支持集合内。
    """
    config = _role_config(
        CASE_PLANNER_NAME,
        CASE_MODULE_PLANNER_PROMPT,
        CASE_PLANNER_MODEL,
        CASE_PLANNER_MAX_ITERS,
    )
    return BaseRole(*AgentRoleConfig(**config).load_config())


def build_case_writer() -> BaseRole:
    """按写死的配置创建一个用例编写角色；每次调用都是独立实例。

    Returns:
        新的用例编写角色。

    Raises:
        ValueError: 模型提供商不在支持集合内。
    """
    config = _role_config(
        CASE_WRITER_NAME,
        CASE_WRITER_PROMPT,
        CASE_WRITER_MODEL,
        CASE_WRITER_MAX_ITERS,
        plan_mode=True,
    )
    return BaseRole(*AgentRoleConfig(**config).load_config())


def build_case_verifier() -> BaseRole:
    """按写死的配置创建一个用例验收角色；每次调用都是独立实例。

    Returns:
        新的用例验收角色。

    Raises:
        ValueError: 模型提供商不在支持集合内。
    """
    config = _role_config(
        CASE_VERIFIER_NAME,
        CASE_VERIFIER_PROMPT,
        CASE_VERIFIER_MODEL,
        CASE_VERIFIER_MAX_ITERS,
    )
    return BaseRole(*AgentRoleConfig(**config).load_config())


def build_case_writer_goal() -> BaseRole:
    """创建一个走 GoalPipeline 交付协议的编写角色。

    Returns:
        新的用例编写角色，提示词要求先保存文档再交结构化 report。

    Raises:
        ValueError: 模型提供商不在支持集合内。
    """
    config = _role_config(
        CASE_WRITER_NAME,
        CASE_WRITER_GOAL_PROMPT,
        CASE_WRITER_MODEL,
        CASE_WRITER_MAX_ITERS,
        plan_mode=True,
    )
    return BaseRole(*AgentRoleConfig(**config).load_config())


def build_case_verifier_goal() -> BaseRole:
    """创建一个走 GoalPipeline 判定协议的验收角色。

    Returns:
        新的用例验收角色，提示词要求先读存储文档再给 result/message。

    Raises:
        ValueError: 模型提供商不在支持集合内。
    """
    config = _role_config(
        CASE_VERIFIER_NAME,
        CASE_VERIFIER_GOAL_PROMPT,
        CASE_VERIFIER_MODEL,
        CASE_VERIFIER_MAX_ITERS,
    )
    return BaseRole(*AgentRoleConfig(**config).load_config())
