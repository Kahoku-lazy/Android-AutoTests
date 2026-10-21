"""执行智能体角色。继承 BaseRole，挂上设备工具和执行技能。"""

from __future__ import annotations

import os

from ..prompt_config import EXECUTOR_PROMPT
from ..prompts.verifier_prompt import verifier_system_prompt
from ..tools_config import (
    build_executor_toolkit,
    build_verifier_toolkit,
)
from .base import AgentRoleConfig, BaseRole

# UI自动化执行角色
executor_config = {
    "provider": "deepseek",
    "model_name": "deepseek-flash",
    "base_url": "https://api.deepseek.com/v1",
    "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
    "name": "executor_role",
    "system_prompt": EXECUTOR_PROMPT,
    "toolkit": build_executor_toolkit(),
    "vision": True,
    "max_iters": 60,
}

executor = BaseRole(*AgentRoleConfig(**executor_config).load_config())

# UI自动化结果验收角色
verifier_config = {
    "provider": "deepseek",
    "model_name": "deepseek-flash",
    "base_url": "https://api.deepseek.com/v1",
    "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
    "name": "verifier_role",
    "system_prompt": verifier_system_prompt(),
    "toolkit": build_verifier_toolkit(),
    "vision": True,
}

verifier = BaseRole(*AgentRoleConfig(**verifier_config).load_config())
