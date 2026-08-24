"""device-pool 跨模块写操作白名单。

共享给其他模块（test_runner / ai_assistant / element_locator / device_inspector）。
遵循防火墙 #2：跨 App 写操作必须走本 api；本模块写逻辑下沉到 service.py。
"""

__all__ = [
    "acquire_device",
    "device",
    "ensure_device",
    "get_online_devices",
    "list_devices",
    "release_device",
    "release_device_locks_for_device",
]

from datetime import datetime

from django.db import transaction

from .models import Device, DeviceLock
from .pool import device
from .service import release_internal


def get_online_devices():
    """返回所有在线设备（status=ONLINE）。"""
    return list(Device.objects.filter(status="ONLINE"))


def list_devices(user_id: str = "") -> list[dict]:
    """设备管理口径的全量设备列表（只读快照，供 AI 助手 list_devices 工具调用）。

    与 GET /api/devices/ 同一套可见性规则（is_device_visible）与序列化口径
    （device_to_dict：status/occupied_by/remaining/last_seen 等），包含使用中
    （BUSY）设备。不做 ADB 状态同步——工具保持只读无副作用，状态由 heartbeat /
    设备管理页列表刷新。
    """
    from django.conf import settings

    from .service import (
        device_to_dict,
        is_device_visible,
        resolve_admin_ids,
        usernames_by_ids,
    )

    admin_ids = resolve_admin_ids(settings.ADMIN_USERS)
    devices = [d for d in Device.objects.all() if is_device_visible(d, user_id, admin_ids)]
    status_order = {"ONLINE": 0, "BUSY": 1}
    devices.sort(key=lambda d: status_order.get(d.status, 99))

    owner_ids = (
        {d.locked_by for d in devices if d.locked_by}
        | {d.added_by for d in devices if d.added_by}
        | {d.occupied_by for d in devices if d.occupied_by}
    )
    id_to_name = usernames_by_ids(owner_ids)
    return [device_to_dict(d, device.current_serial, id_to_name) for d in devices]


def ensure_device(serial, name=""):
    """Get or create 设备记录（向后兼容）。"""
    obj, _ = Device.objects.get_or_create(
        serial=serial,
        defaults={
            "name": name,
            "connection_type": "WIFI" if ":" in serial else "USB",
        },
    )
    return obj


@transaction.atomic
def acquire_device(serial, user_id, timeout=300):
    """锁定设备（进程占用，供 test_runner / AgentScope 调用）。

    select_for_update() 保证多进程并发下不重复通过 BUSY 检查。
    """
    device_obj = Device.objects.select_for_update().get(serial=serial)

    if device_obj.status == "BUSY":
        active_lock = (
            DeviceLock.objects.filter(device=device_obj, lock_type="process", status="active")
            .order_by("-locked_at")
            .first()
        )
        if active_lock and not active_lock.is_expired:
            # occupied_by 为 CharField，调用方 user_id 多为 int——统一按字符串比较，
            # 避免同一用户（AI 先 acquire 后执行）被误判为他人占用。
            if str(device_obj.occupied_by) != str(user_id):
                raise ValueError(
                    f"设备已被 {device_obj.occupied_by or 'unknown'} 占用，"
                    f"剩余 {active_lock.remaining_seconds} 秒"
                )

    now = datetime.now()
    device_obj.status = "BUSY"
    device_obj.occupied_by = user_id
    device_obj.occupied_at = now
    device_obj.save(update_fields=["status", "occupied_by", "occupied_at"])

    DeviceLock.objects.create(
        device=device_obj,
        user_id=user_id,
        lock_type="process",
        timeout_seconds=timeout,
        status="active",
    )

    return {
        "serial": serial,
        "user_id": user_id,
        "locked_at": now,
        "timeout": timeout,
    }


def release_device(serial, reason="manual"):
    """释放锁定设备（保留锁审计，触发队列自动分配）。"""
    try:
        dev = Device.objects.get(serial=serial)
        if dev.status == "BUSY":
            release_internal(dev, reason=reason)
            return True
    except Device.DoesNotExist:
        pass
    return False


def release_device_locks_for_device(device_obj, reason="disconnect"):
    """批量释放设备的活跃进程锁（崩溃恢复 / 孤儿清理入口）。"""
    return DeviceLock.objects.filter(
        device=device_obj, lock_type="process", status="active"
    ).update(
        status="released",
        released_at=datetime.now(),
        release_reason=reason,
    )
