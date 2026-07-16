"""Device listing and activation endpoints."""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .helpers import _update_device_status, _device_to_dict, _purge_disconnected_devices
from ..models import Device

def list_devices(request):
    """GET /api/devices — 设备列表 + 状态。

    PRD §6.2.1: 返回设备列表、当前设备、排队长度。
    每次调用自动触发心跳检测，同步 adb 真实状态到 DB。
    不逐设备调用 u2.connect（使用 DB 缓存字段），保证 ≤500ms 响应。
    """
    try:
        # 1. 心跳同步
        _update_device_status()
        _check_timeout_queue()

        # 2. 确保 adb 在线设备已在 DB 中注册（轻量：仅 adb devices，不 u2.connect）
        adb_serials = _adb_device_serials()
        for serial in adb_serials:
            Device.objects.get_or_create(
                serial=serial,
                defaults={
                    "status": "ONLINE",
                    "connection_type": "WIFI" if ":" in serial else "USB",
                },
            )

        # 3. 查询所有设备并排序：ONLINE > BUSY > OFFLINE > DISCONNECTED
        devices = list(Device.objects.all())
        status_order = {"ONLINE": 0, "BUSY": 1, "OFFLINE": 2, "DISCONNECTED": 3}
        devices.sort(key=lambda d: status_order.get(d.status, 99))

        # 4. 构建响应
        current_serial = device_pool.current_serial
        if not current_serial:
            online = [d for d in devices if d.status in ("ONLINE", "BUSY")]
            if online:
                first = online[0]
                ct = first.connection_type or ("WIFI" if ":" in first.serial else "USB")
                device_pool.switch_to(first.serial, ct)
                current_serial = first.serial

        result_list = [_device_to_dict(d, current_serial) for d in devices]

        # 5. 排队队列长度（waiting count）
        queue_count = DeviceQueue.objects.filter(status="waiting").count()

        return JsonResponse(
            {
                "ok": True,
                "devices": result_list,
                "current": current_serial,
                "queue_length": queue_count,
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


def device_current(request):
    """GET /api/devices/current — 当前活动设备信息。

    PRD §6.2.7: 返回当前设备 serial, screen, package 等。
    """
    info = device_pool.info()
    current_serial = device_pool.current_serial

    # 尝试从 DB 获取更丰富的信息
    try:
        dev = Device.objects.get(serial=current_serial)
        return JsonResponse(
            {
                "ok": True,
                "serial": current_serial,
                "screen_w": dev.screen_w or info.get("displayWidth", 0),
                "screen_h": dev.screen_h or info.get("displayHeight", 0),
                "package": info.get("currentPackageName", ""),
                "model": dev.model,
                "brand": dev.brand,
                "connection_type": device_pool.get_connection_type(current_serial),
            }
        )
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": True,
                "serial": current_serial,
                "screen_w": info.get("displayWidth", 1440),
                "screen_h": info.get("displayHeight", 3040),
                "package": info.get("currentPackageName", ""),
            }
        )


@csrf_exempt
def activate_device(request, serial):
    """POST /api/devices/{serial}/activate — 切换当前活动设备。

    PRD §6.2.7: 切换 uiautomator2 当前设备指针。
    """
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        Device.objects.create(
            serial=serial, status="ONLINE", connection_type="WIFI" if ":" in serial else "USB"
        )
        dev = Device.objects.get(serial=serial)

    # 检查状态
    if dev.status in ("OFFLINE", "DISCONNECTED"):
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 当前{dev.status}，无法激活",
            },
            status=400,
        )

    ct = dev.connection_type or ("WIFI" if ":" in serial else "USB")
    device_pool.switch_to(serial, ct)

    # 更新 last_seen
    dev.last_seen = datetime.now()
    dev.save(update_fields=["last_seen"])

    return JsonResponse({"ok": True, "current": serial})


