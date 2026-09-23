"""单模型调试台 — 三角色只读配置 + 单角色调试对话（工具箱「模型调试」来源）。

要点：
- 三角色的**工具子集与视觉标记直接取自角色类**（PlannerRole / ExecutorRole / VerifierRole
  的 RoleSpec），页面展示与实际装配同源，不另抄一份常量。
- 三模型装配与命令行 model_test **共用同一个构造**（build_device_models_for_agent），避免漂移。
- 调试对话**不挂任何工具、不挂 Skill、不触碰真机**，也不落库。
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os

from apps.ai_assistant.api import (
    decrypt_key,
    get_platform_tool_enabled_map,
    get_provider_config,
)
from apps.ai_assistant.engine_adapter import build_tool_specs
from apps.ai_assistant.skills_catalog import list_enabled_skill_dirs
from apps.ai_assistant.tools import TOOL_META, TOOLS, available_device_options
from engines.ai.agentscope.config import DeviceExecutionConfig, ModelConfig
from engines.ai.agentscope.model import (
    AgentRole,
    ExecutorRole,
    PlannerRole,
    RoleSpec,
    VerifierRole,
    build_device_models,
)

logger = logging.getLogger("ai_assistant.model_debug")

# 角色真相源：角色 → 角色类（工具子集 / 视觉标记都取自它的 RoleSpec）
ROLE_CLASSES: dict[str, type[AgentRole]] = {
    "planner": PlannerRole,
    "executor": ExecutorRole,
    "verifier": VerifierRole,
}

ROLES: tuple[str, ...] = tuple(ROLE_CLASSES)

ROLE_LABELS: dict[str, str] = {
    "planner": "规划模型 Planner",
    "executor": "执行模型 Executor",
    "verifier": "验收模型 Verifier",
}

_KNOWLEDGE_FILE_LIMIT = 50


def normalize_role(role: str) -> str:
    """校验角色名，非法则抛 ValueError（由 View 转 400）。"""
    name = (role or "").strip()
    if name not in ROLE_CLASSES:
        raise ValueError(f"未知角色: {role or '(空)'}，可选 {', '.join(ROLES)}")
    return name


def role_prompt(agent, role: str) -> str:
    """该角色的系统提示词（DB 为唯一真相源）。"""
    return str(getattr(agent, f"prompt_{role}", "") or "")


# ── 三角色模型装配（命令行 model_test 与本服务共用）──


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
        system_prompts={role: role_prompt(agent, role) for role in ROLES},
    )
    return config, planner, executor, verifier


def _require_configured(role: str, model_name: str, api_key: str) -> None:
    """模型连接不完整时给可读错误（沿用 model_test 的中文文案）。"""
    label = ROLE_LABELS[role]
    if not model_name:
        raise ValueError(
            f"「{label}」的 model_name 未配置，请到智能体配置页填写 "
            f"route_configs.device_control.{role} 的模型名"
        )
    if not api_key:
        raise ValueError(f"「{label}」的 api_key 未配置（或无法解密），请到智能体配置页重新填写")


def _check_role_model(cfg: ModelConfig, role: str) -> None:
    """装配后再校验一次（防御性，正常路径由 _require_configured 在前置拦下）。"""
    _require_configured(role, cfg.model_name, cfg.api_key)


def require_role_configured(agent, role: str) -> None:
    """装配**之前**校验：只看原始配置 + 解密结果，避免拿空配置去构造引擎模型。

    引擎在 api_key 为空时会直接抛 OpenAIError（500），所以这一步必须在装配前完成。
    """
    raw = ((agent.route_configs or {}).get("device_control") or {}).get(role) or {}
    _require_configured(
        role,
        str(raw.get("model_name") or ""),
        decrypt_key(raw.get("api_key") or ""),
    )


# ── 只读配置 ──


def _model_summary(agent, role: str) -> dict:
    """模型连接摘要（脱敏：只回是否已配置，不回 api_key / base_url 明文）。"""
    route_cfg = (agent.route_configs or {}).get("device_control") or {}
    raw = route_cfg.get(role) or {}
    return {
        "provider": str(raw.get("provider") or "deepseek"),
        "model_name": str(raw.get("model_name") or ""),
        "has_api_key": bool(raw.get("api_key")),
        "configured": bool(raw.get("model_name")) and bool(raw.get("api_key")),
    }


def _role_tools(role: str) -> list[dict]:
    """该角色的工具子集（名字取自角色类，附只读/分类/是否被平台停用）。"""
    enabled_map = get_platform_tool_enabled_map()
    items: list[dict] = []
    for name in ROLE_CLASSES[role].spec.tool_names:
        entry = TOOLS.get(name)
        meta = TOOL_META.get(name) or ("", "", "")
        items.append(
            {
                "name": name,
                "read_only": bool(entry[1]) if entry else False,
                "category": meta[0],
                "enabled": bool(enabled_map.get(name, True)),
            }
        )
    return items


def _skills(agent) -> dict:
    """启用的 Skill 清单。三模型共用同一份（装配链路整组传同一批目录）。"""
    dirs = list_enabled_skill_dirs() if agent.enable_skills else []
    return {
        "gate_on": bool(agent.enable_skills),
        "shared_by_roles": True,
        "items": [{"name": os.path.basename(d), "path": d} for d in dirs],
    }


def _knowledge(agent) -> dict:
    """知识库来源（配置层）。设备执行链路当前未挂载 RAG，故 wired_to_runtime=False。"""
    from apps.ai_assistant.kb_files import list_rag_files

    sources = agent.knowledge_sources or {}
    enabled_ids = [str(k) for k, v in sources.items() if v]
    files = list_rag_files()
    return {
        "gate_on": bool(agent.enable_knowledge_base),
        "enabled_source_ids": enabled_ids,
        "file_count": len(files),
        "files": [
            {"id": f.get("id", ""), "name": f.get("name", ""), "type": f.get("type", "")}
            for f in files[:_KNOWLEDGE_FILE_LIMIT]
        ],
        "wired_to_runtime": False,
    }


def build_role_debug_configs(agent) -> dict:
    """三角色只读调试配置（提示词 / 模型连接 / 工具子集 + 技能与知识库归属）。"""
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "roles": [
            {
                "role": role,
                "label": ROLE_LABELS[role],
                "vision": bool(ROLE_CLASSES[role].spec.vision),
                # 前端据此决定是否要求选设备（判定口径在 role_needs_device）
                "needs_device": role_needs_device(role),
                "model": _model_summary(agent, role),
                "prompt": role_prompt(agent, role),
                "tools": _role_tools(role),
            }
            for role in ROLES
        ],
        "skills": _skills(agent),
        "knowledge": _knowledge(agent),
    }


# ── 单角色调试对话 ──


def role_needs_device(role: str) -> bool:
    """该角色的工具子集里是否有工具需要设备（声明了 serial 参数）。

    按工具函数签名判定而不是硬编码角色名，也不依赖 DEBUG_PARAM_OPTIONS
    （后者只登记了设备管理类工具，screenshot_page 等会被漏掉）。
    """
    for name in ROLE_CLASSES[role].spec.tool_names:
        entry = TOOLS.get(name)
        if entry and "serial" in inspect.signature(entry[0]).parameters:
            return True
    return False


def require_available_device(role: str, serial: str, user_id: str) -> str:
    """校验 serial 对请求者可见、在线且未被占用；不满足时抛 ValueError（View 转 400）。"""
    value = str(serial or "").strip()
    if not value:
        raise ValueError(
            f"「{ROLE_LABELS[role]}」需要先选定一台设备（候选：对当前用户可见 + 在线 + 未被占用）"
        )
    allowed = {item["value"] for item in available_device_options(user_id)}
    if value not in allowed:
        raise ValueError(
            f"设备 {value} 当前不可用（需对当前用户可见、状态在线且未被占用），请重新选择"
        )
    return value


def build_debug_role(agent, role: str, model_cfg: ModelConfig, user_id: str = "") -> AgentRole:
    """构造只带该角色模型/提示词/工具子集的调试角色（Skill 不挂）。

    工具子集直接取角色规格，与生产装配（build_device_models）同源，不另抄一份；
    因此调试对话会真实调用工具、真实操作设备。
    """
    base = ROLE_CLASSES[role].spec
    spec = RoleSpec(
        role=base.role,
        prompt="",
        tool_names=base.tool_names,
        vision=base.vision,
        context_config=base.context_config,
        react_config=base.react_config,
    )

    class _DebugRole(AgentRole):
        """调试专用角色：配置与工具子集来自目标角色，Skill 不挂。"""

    _DebugRole.spec = spec
    return _DebugRole(
        config=model_cfg,
        tools=build_tool_specs(),
        user_id=str(user_id or agent.owner_id or ""),
        skill_dirs=[],  # 调试对话不挂 Skill（与生产的差异见变更非目标）
        system_prompt=role_prompt(agent, role),
    )


def run_role_chat(agent, role: str, text: str, user_id: str = "", serial: str = "") -> dict:
    """对单个角色发起一次调试对话；任一处不合法抛 ValueError（View 转 400）。

    调试对话挂载该角色的真实工具子集：工具里需要设备的角色必须先选定一台可用设备，
    serial 以与生产同口径的提示词前缀下发（不强制覆盖模型传入的工具入参）。
    """
    role = normalize_role(role)
    content = str(text or "").strip()
    if not content:
        raise ValueError("调试内容不能为空")

    # 先校验原始配置：拿空模型连接去构造引擎会抛 OpenAIError（500），必须在装配前拦住
    require_role_configured(agent, role)

    # 该角色工具子集里若有需要设备的工具，必须先选定一台对该请求者可用的设备
    device = require_available_device(role, serial, user_id) if role_needs_device(role) else ""

    config, _planner, _executor, _verifier = build_device_models_for_agent(agent)
    model_cfg = config.__getattribute__(role)
    _check_role_model(model_cfg, role)

    role_obj = build_debug_role(agent, role, model_cfg, user_id=user_id)
    prompt = f"当前设备 serial：{device}\n{content}" if device else content
    result = asyncio.run(role_obj.ask(prompt))
    return {
        "role": role,
        "label": ROLE_LABELS[role],
        "model_name": result.model_name or model_cfg.model_name,
        "reply": result.output,
        "thinking": result.thinking,
        "tool_usage": result.tool_usage,
        "usage": result.usage,
        "cost": result.cost,
    }
