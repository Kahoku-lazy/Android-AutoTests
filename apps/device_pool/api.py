"""device-pool 跨模块写操作白名单。

共享给其他模块（test_runner / ai_assistant / element_locator / device_inspector）。
遵循防火墙 #2：跨 App 写操作必须走本 api；本模块写逻辑下沉到 service.py。
"""

__all__ = [
    "acquire_device",
    "device",
    "device_action",
    "ensure_device",
    "get_online_devices",
    "list_apps",
    "list_devices",
    "release_device",
    "release_device_locks_for_device",
    "use_device",
]

from datetime import datetime

from django.db import transaction

from .models import Device, DeviceLock
from .pool import device
from .service import release_internal

# 执行引擎占用前缀：设备动作/抓取不与执行引擎抢设备（与 device_inspector.service 同口径）
_EXECUTION_OCCUPY_PREFIXES = ("runner-", "ai_agent", "task-", "run-")


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


def use_device(serial: str) -> None:
    """切到目标设备 + 可用性/执行引擎占用校验（跨 App 统一入口）。

    与 device_inspector.service.ensure_current_device 同一口径：
    未注册抛 ValueError；执行引擎占用抛 ValueError（上层转用户文案）。
    """
    if not serial:
        raise ValueError("未选择设备，请先连接设备")
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        raise ValueError("设备未注册")

    if dev.status == "BUSY" and dev.occupied_by:
        for prefix in _EXECUTION_OCCUPY_PREFIXES:
            if str(dev.occupied_by).startswith(prefix):
                raise ValueError(f"设备正被执行引擎占用（{dev.occupied_by}），请等待执行完毕")

    if device.current_serial != serial:
        device.switch_to(serial, dev.connection_type or "USB", dev.connection_addr)


def device_action(
    serial: str,
    action: str,
    *,
    package: str = "",
    x=None,
    y=None,
    x2=None,
    y2=None,
    direction: str = "up",
    distance: int = 500,
    text: str = "",
    clear_first: bool = True,
    duration: float = 0.5,
) -> dict:
    """对指定设备执行一个 UI 动作，返回当前前台 package/activity（供跳转判定）。

    action: start_app / stop_app / click / long_click / swipe / drag / back / input_text / current
    """
    use_device(serial)

    if x is not None:
        x = int(x)
    if y is not None:
        y = int(y)
    if x2 is not None:
        x2 = int(x2)
    if y2 is not None:
        y2 = int(y2)

    if action == "start_app":
        if not package:
            raise ValueError("start_app 需要 package 参数")
        device.action_start_app(package)
    elif action == "stop_app":
        if not package:
            raise ValueError("stop_app 需要 package 参数")
        device.action_stop_app(package)
    elif action == "back":
        device.action_press_key("back")
    elif action == "click":
        if x is None or y is None:
            raise ValueError("click 需要 x/y 坐标")
        device.action_click(x, y)
    elif action == "long_click":
        if x is None or y is None:
            raise ValueError("long_click 需要 x/y 坐标")
        device.action_longclick(x, y)
    elif action == "swipe":
        device.action_swipe(direction or "up", int(distance or 500))
    elif action == "drag":
        if x is None or y is None or x2 is None or y2 is None:
            raise ValueError("drag 需要 x/y（起点）与 x2/y2（终点）坐标")
        device.action_drag_coord(x, y, x2, y2, duration=float(duration))
    elif action == "input_text":
        device.action_input(text or "", x, y, clear_first=bool(clear_first))
    elif action == "current":
        pass
    else:
        raise ValueError(f"不支持的设备动作: {action}")

    return device.app_current()


def list_apps(serial: str, query: str = "") -> dict:
    """列出设备已安装包名（可按 query 子串过滤），供 AI 获取被测 App 包名后 start_app。"""
    use_device(serial)
    raw = device.action_shell("pm list packages")
    packages = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        pkg = line[len("package:") :].strip()
        if pkg and (not query or query.lower() in pkg.lower()):
            packages.append(pkg)
    return {"packages": packages, "count": len(packages)}
