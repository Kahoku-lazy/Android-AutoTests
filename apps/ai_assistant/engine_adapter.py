"""Django ↔ AI 引擎胶水层：从 AITask + AIAgent 组装 TaskRequest。

只负责「读配置 + 解密 + 组装」，不碰框架实现；引擎经 engines.ai.registry 获取。
装配期 fail-fast：线路 / 角色 / provider / 设备串任一项缺失或非法即抛错，
由调用方（后台任务线程）兜底成任务失败终态，不再产出空模型连接。
"""

from __future__ import annotations

from engines.ai.base import ModelSpec, TaskRequest, ToolSpec

from . import api
from .provider_registry import VALID_PROVIDERS, get_provider_config
from .skills_catalog import list_enabled_skill_dirs
from .tools import AUTO_ALLOW_TOOLS, TOOLS

__all__ = ["build_request", "build_tool_specs", "resolve_device_serial"]

# 装配期校验的线路键与角色名（与 AIAgent.route_configs 的结构一致）
ROUTE_KEY = "device_control"
ROUTE_ROLES = ("planner", "executor", "verifier")


def _model_spec(role: str, cfg: object) -> ModelSpec:
    """单个角色的线路配置 → ModelSpec（解密 key + 解析默认 base_url）。

    装配期 fail-fast：角色缺失 / provider 非法 / 模型名或密钥为空即抛错。
    """
    if not isinstance(cfg, dict) or not cfg:
        raise ValueError(f"智能体配置缺少 {ROUTE_KEY}.{role}，无法组装模型连接")

    provider = str(cfg.get("provider") or "deepseek").strip()
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"智能体配置 {ROUTE_KEY}.{role}.provider={provider!r} 不在合法集合 "
            f"{sorted(VALID_PROVIDERS)}"
        )

    model_name = str(cfg.get("model_name") or "").strip()
    if not model_name:
        raise ValueError(f"智能体配置 {ROUTE_KEY}.{role}.model_name 为空")

    api_key = str(api.decrypt_key(cfg.get("api_key", "")) or "").strip()
    if not api_key:
        raise ValueError(f"智能体配置 {ROUTE_KEY}.{role}.api_key 为空")

    return ModelSpec(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=get_provider_config(provider, cfg.get("base_url", ""))["base_url"],
    )


def build_tool_specs() -> list[ToolSpec]:
    """把平台工具注册表（TOOLS）转成 ToolSpec 列表。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=read_only,
            auto_allow=name in AUTO_ALLOW_TOOLS,
        )
        for name, (func, read_only) in TOOLS.items()
    ]


def resolve_device_serial(task_device_serial: str = "") -> str:
    """取任务指定设备串，否则取第一台在线设备；都没有即抛错（不再返回空串）。"""
    serial = str(task_device_serial or "").strip()
    if serial:
        return serial

    from apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        raise ValueError("无可用设备：任务未指定设备 serial，且当前没有在线设备")

    first_serial = str(getattr(devices[0], "serial", "") or "").strip()
    if not first_serial:
        raise ValueError("无可用设备：在线设备缺少 serial")
    return first_serial


# 兼容旧名
_resolve_device_serial = resolve_device_serial


def _system_prompts(agent) -> dict[str, str]:
    """从智能体表字段读取三角色系统提示词；任一份为空则装配失败。"""
    field_by_role = {
        "planner": "prompt_planner",
        "executor": "prompt_executor",
        "verifier": "prompt_verifier",
    }
    out: dict[str, str] = {}
    for role, field in field_by_role.items():
        text = str(getattr(agent, field, "") or "")
        if not text.strip():
            raise ValueError(f"智能体配置 {role} 系统提示词为空，无法组装任务")
        out[role] = text
    return out


def build_request(task, agent) -> TaskRequest:
    """AITask + AIAgent → TaskRequest（任务表单 + 三角色模型 + 工具清单）。

    装配期 fail-fast：线路 / 角色 / provider / 设备串 / 系统提示词任一项缺失或非法即抛错。
    规划用户输入为四键中文 JSON，仍经 TaskRequest.goal 传入引擎。
    """
    from django.conf import settings

    route_cfg = (agent.route_configs or {}).get(ROUTE_KEY) or {}
    models = {role: _model_spec(role, route_cfg.get(role)) for role in ROUTE_ROLES}
    # 提交时已固化 serial；此处再解析一次兜底旧任务 / 测试桩
    serial = resolve_device_serial(getattr(task, "device_serial", "") or "")
    return TaskRequest(
        goal=api.build_planner_user_input(task),
        models=models,
        tools=build_tool_specs(),
        max_loops=int(agent.max_loops or 3),
        device_serial=serial,
        user_id=str(agent.owner_id or ""),
        task_id=int(getattr(task, "id", 0) or 0),
        media_root=str(getattr(settings, "MEDIA_ROOT", "") or ""),
        skill_dirs=list_enabled_skill_dirs() if agent.enable_skills else [],
        system_prompts=_system_prompts(agent),
    )
