"""任务装配：设备串兜底解析。

模型与工具包全部写死在 `engines.agents.role.agents`，本模块不再读数据库里的
模型配置、不再构造 `ModelConfig`，也不再做 provider / 密钥校验。
"""

from __future__ import annotations

__all__ = ["resolve_device_serial"]


def resolve_device_serial(task_device_serial: str = "") -> str:
    """取任务指定设备串，否则取第一台在线设备；都没有即抛错（不再返回空串）。

    Args:
        task_device_serial: 任务上指定的设备序列号，可为空。

    Returns:
        可用的设备序列号。

    Raises:
        ValueError: 未指定序列号且当前没有在线设备，或在线设备缺少 serial。
    """
    serial = str(task_device_serial or "").strip()
    if serial:
        return serial

    from backend.apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        raise ValueError("无可用设备：任务未指定设备 serial，且当前没有在线设备")

    first_serial = str(getattr(devices[0], "serial", "") or "").strip()
    if not first_serial:
        raise ValueError("无可用设备：在线设备缺少 serial")
    return first_serial
