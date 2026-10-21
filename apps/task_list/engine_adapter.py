"""平台任务装配：从控制设备线路读取执行 / 验收模型，并解析设备串。

不调用旧规划引擎。模型名、密钥或 provider 不合法时在这里失败，
由调用方（后台任务线程）兜底成任务失败终态。
"""

from __future__ import annotations

from apps.ai_assistant import api
from apps.ai_assistant.provider_registry import VALID_PROVIDERS, get_provider_config
from engines.agents.role.config import ModelConfig

__all__ = ["resolve_device_serial", "sop_role_models"]

# 装配期校验的线路键（与 AIAgent.route_configs 的结构一致）
ROUTE_KEY = "device_control"
SOP_ROLES = ("executor", "verifier")


def _model_config(role: str, cfg: object) -> ModelConfig:
    """单个角色的线路配置 → ModelConfig（解密 key + 解析默认 base_url）。

    角色缺失、provider 非法、模型名或密钥为空时抛错。
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

    return ModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=get_provider_config(provider, cfg.get("base_url", ""))["base_url"],
    )


def sop_role_models(agent):
    """控制设备线路上的执行 / 验收模型。不读取规划角色，也不读取平台工具清单。"""
    route_cfg = (agent.route_configs or {}).get(ROUTE_KEY) or {}
    return tuple(_model_config(role, route_cfg.get(role)) for role in SOP_ROLES)


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
