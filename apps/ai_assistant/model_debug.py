"""单模型调试台 — 三角色只读配置 + 单角色调试对话（工具箱「模型调试」来源）。

要点：
- 三角色的**工具子集与视觉标记直接取自角色类**（PlannerRole / ExecutorRole / VerifierRole
  的 RoleSpec），页面展示与实际装配同源，不另抄一份常量。
- 三模型装配与命令行 model_test **共用同一个构造**（build_device_models_for_agent），避免漂移。
- 调试对话**挂该角色真实工具**（需要设备的角色在选定设备后**会真实操作该设备**）、不挂 Skill，
  对话内容**不落库**。
- 本轮产生设备副作用点击时，响应带一份平台装配的「日志检查」：点击前时间点 + 点击后截图路径
  + 该时间点后 5 秒窗口内的日志（与任务步骤证据同源；配对与切片共用 `logcheck` 的纯函数）。
- **验收角色**的调试对话另带一份「设备日志证据 · 调试回溯」：平台从消息里识别取证基准
  （第一个北京时间毫秒时间戳；没有则退回最近一个取证窗），从日志文件回溯该基准后 5 秒窗口的
  日志与命中关键词，按任务链路同一份渲染交给模型（验收模型自己没有日志工具，生产链路也是
  平台喂证据）。响应带 `log_evidence` 与 `log_basis`；取不到时如实给原因，不打开端口。
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
from apps.ai_assistant.log_evidence import ensure_log_evidence
from apps.ai_assistant.log_history import (
    extract_basis_time,
    history_evidence,
    keyword_catalog_text,
)
from apps.ai_assistant.skills_catalog import list_enabled_skill_dirs
from apps.ai_assistant.tools import TOOL_META, TOOLS, available_device_options
from engines.ai.agents.config import DeviceExecutionConfig, ModelConfig
from engines.ai.agents.logcheck import (
    build_executor_log_check,
    checked_log_keywords,
    render_log_evidence,
)
from engines.ai.agents.model import (
    AgentRole,
    ExecutorRole,
    PlannerRole,
    RoleSpec,
    VerifierRole,
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


def normalize_role(role: str) -> str:
    """校验角色名，非法则抛 ValueError（由 View 转 400）。"""
    name = (role or "").strip()
    if name not in ROLE_CLASSES:
        raise ValueError(f"未知角色: {role or '(空)'}，可选 {', '.join(ROLES)}")
    return name


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


def build_role_debug_configs(agent) -> dict:
    """三角色只读调试配置（模型连接 / 工具子集 + 技能归属）。

    不下发系统提示词：提示词随引擎走（engines/ai/agents/config.py），前端不展示。
    """
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
                "tools": _role_tools(role),
            }
            for role in ROLES
        ],
        "skills": _skills(agent),
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
        # 提示词随角色走：与生产同源，不从库读
        prompt=base.prompt,
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
    # 验收角色自己没有日志工具：由平台按取证基准把日志证据喂进输入（与生产同口径）
    log_basis = _debug_log_basis(role, device, content)
    if log_basis is not None:
        prompt += _log_evidence_input(log_basis)
        prompt += _keyword_catalog_input()
    # 证据窗必须在任何设备动作之前开启（与生产链路同口径）；没有端口在监听时如实不带日志
    provider = ensure_log_evidence() if device else None
    window_id = _open_debug_window(provider, device)
    result = asyncio.run(role_obj.ask(prompt))
    log_check = _debug_log_check(result, provider, device, window_id)
    payload = {
        "role": role,
        "label": ROLE_LABELS[role],
        "model_name": result.model_name or model_cfg.model_name,
        "reply": result.output,
        "thinking": result.thinking,
        "tool_usage": result.tool_usage,
        "usage": result.usage,
        "cost": result.cost,
    }
    if log_check["clicks"]:
        payload["log_check"] = log_check
    if log_basis is not None:
        payload["log_basis"] = {
            key: log_basis[key] for key in ("basis_time", "from_message", "files", "note")
        }
        if log_basis["evidence"] is not None:
            payload["log_evidence"] = log_basis["evidence"]
        # logAssertionInfo：模型查询（检查）的日志关键词，平台按工具调用自动填
        keywords = checked_log_keywords(result)
        if keywords:
            payload["log_assertion_info"] = "、".join(keywords)
    return payload


def _keyword_catalog_input() -> str:
    """把当前关键词表与「两条件」判定口径拼进验收角色的输入（表取运行时索引，不写死）。"""
    catalog = keyword_catalog_text()
    rule = (
        "判定口径（必须遵守）：调用 check_device_log 检查断言涉及的日志关键词，"
        "**日志检测到 + 截图确认两个条件都满足才可判 PASS**；未检测到该关键词时必须判 FAIL，"
        "并在 actual 里写明日志未检测到。"
    )
    return f"\n\n{catalog}\n{rule}" if catalog else f"\n\n{rule}"


def _debug_log_basis(role: str, device: str, content: str) -> dict | None:
    """验收角色才取日志证据（规划模型无设备；执行模型自己有只读日志工具）。"""
    if not device or ROLE_CLASSES[role] is not VerifierRole:
        return None
    basis = extract_basis_time(content)
    return history_evidence(basis)


def _log_evidence_input(log_basis: dict) -> str:
    """把取证结果拼进验收角色的输入：同一份渲染文本 + 调试回溯的口径说明。"""
    origin = "消息里的时刻" if log_basis["from_message"] else "最近一个取证窗"
    lines = [
        "",
        "",
        "【设备日志证据 · 调试回溯】"
        f"取证基准 {log_basis['basis_time']}（来源：{origin}）。"
        "平台按该基准之后的 5 秒窗口从设备日志文件中取出，判定口径与任务链路一致；"
        "注意这是调试回溯，不是生产步骤的取证窗。",
        render_log_evidence(log_basis["evidence"]),
    ]
    evidence = log_basis["evidence"]
    if not evidence or not evidence.get("window_line_count"):
        lines.append(f"说明：本轮没有取到窗口内日志（{log_basis['note'] or '窗口内无日志'}）。")
    lines.append(
        "输出时：logAssertionTimer 取上面「窗口内命中」里那个关键词出现的日志时间戳"
        "（原文照抄；没有命中或没有日志就留空字符串）。"
    )
    return "\n".join(lines)


def _open_debug_window(provider, device: str) -> str:
    """动作前开窗；无提供者（端口未监听 / 采集未启用）或开窗失败时返回空串。"""
    if provider is None or not device:
        return ""
    try:
        window_id = provider.open_window(device, "model-debug")
    except Exception:
        logger.exception("模型调试开窗失败，本次点击证据不带日志")
        return ""
    return str(window_id or "")


def _debug_log_check(result, provider, device: str, window_id: str) -> dict:
    """本轮点击证据：点击前时间点 + 点击后截图路径（+ 有端口在监听时的 5 秒窗口日志）。

    配对与切片口径与任务步骤链路共用 `build_executor_log_check`；一轮对话就是一轮，
    因此不需要跳过任何遗留返回（`skip_results=0`）。
    """
    clicks = build_executor_log_check(result)["clicks"]
    log_evidence = None
    if clicks and provider is not None and window_id:
        try:
            log_evidence = provider.read_window(
                device,
                window_id=window_id,
                action_times=[str(item["action_time"]) for item in clicks],
            )
        except Exception:
            logger.exception("模型调试读窗失败，本次点击证据不带日志")
    return {"clicks": clicks, "log": log_evidence}
