"""Django ↔ AI 引擎胶水层：从 AITask + AIAgent 组装 TaskRequest。

只负责「读配置 + 解密 + 组装」，不碰框架实现；引擎经 engines.ai.registry 获取。
"""

from __future__ import annotations

from engines.ai.base import ModelSpec, TaskRequest, ToolSpec

from . import api
from .provider_registry import get_provider_config
from .skills_catalog import list_enabled_skill_dirs
from .tools import AUTO_ALLOW_TOOLS, TOOLS

__all__ = ["build_request", "build_tool_specs"]


def _model_spec(cfg: dict) -> ModelSpec:
    """route_configs 里单个角色配置 → ModelSpec（解密 key + 解析默认 base_url）。"""
    provider = (cfg.get("provider") or "deepseek").strip()
    return ModelSpec(
        provider=provider,
        model_name=(cfg.get("model_name") or "").strip(),
        api_key=api.decrypt_key(cfg.get("api_key", "")),
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


def _resolve_device_serial() -> str:
    """取第一台在线设备 serial；无设备返回空。"""
    from apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        return ""
    return devices[0].serial or ""


def build_request(task, agent) -> TaskRequest:
    """AITask + AIAgent → TaskRequest（任务表单 + 三角色模型 + 工具清单）。"""
    from django.conf import settings

    route_cfg = (agent.route_configs or {}).get("device_control") or {}
    models = {
        "planner": _model_spec(route_cfg.get("planner") or {}),
        "executor": _model_spec(route_cfg.get("executor") or {}),
        "verifier": _model_spec(route_cfg.get("verifier") or {}),
    }
    return TaskRequest(
        goal=task.goal,
        models=models,
        tools=build_tool_specs(),
        max_loops=int(agent.max_loops or 3),
        device_serial=task.device_serial or _resolve_device_serial(),
        user_id=str(agent.owner_id or ""),
        task_id=int(getattr(task, "id", 0) or 0),
        media_root=str(getattr(settings, "MEDIA_ROOT", "") or ""),
        skill_dirs=list_enabled_skill_dirs() if agent.enable_skills else [],
    )
