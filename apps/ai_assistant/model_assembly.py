"""按智能体配置装配三角色模型（规划 / 执行 / 验收）。

来源：原「模型调试」（工具箱单角色调试台）后端模块拆出的**生产同源装配**部分。
调试页退役后，本函数仍被命令行 `model_test`、`planner_eval` 复用，
故独立成模块，避免与调试对话实现一起被删。

要点：
- 三模型装配与生产链路同源（`build_device_models` + `build_tool_specs`），
  Skill 目录按智能体的 `enable_skills` 开关整组下发。
- 只做装配：不落库、不校验设备、不发起对话（写库路径仍只有 `apps/ai_assistant/api.py`）。
"""

from __future__ import annotations

from apps.ai_assistant.api import decrypt_key, get_provider_config
from apps.ai_assistant.engine_adapter import build_tool_specs
from apps.ai_assistant.skills_catalog import list_enabled_skill_dirs
from engines.ai.agents import DeviceExecutionConfig, ModelConfig, build_device_models


def build_device_models_for_agent(agent):
    """按智能体配置装配三个角色模型，返回 (config, planner, executor, verifier)。"""
    route_cfg = (agent.route_configs or {}).get("device_control") or {}

    def _cfg(m: dict) -> ModelConfig:
        return ModelConfig(
            provider=m.get("provider", "deepseek"),
            model_name=m.get("model_name", ""),
            api_key=decrypt_key(m.get("api_key", "")),
            base_url=get_provider_config(m.get("provider", "deepseek"), m.get("base_url", ""))[
                "base_url"
            ],
        )

    config = DeviceExecutionConfig(
        planner=_cfg(route_cfg.get("planner") or {}),
        executor=_cfg(route_cfg.get("executor") or {}),
        verifier=_cfg(route_cfg.get("verifier") or {}),
        max_loops=int(agent.max_loops or 3),
    )
    planner, executor, verifier = build_device_models(
        config,
        tools=build_tool_specs(),
        user_id=str(agent.owner_id or ""),
        skill_dirs=list_enabled_skill_dirs() if agent.enable_skills else [],
    )
    return config, planner, executor, verifier
