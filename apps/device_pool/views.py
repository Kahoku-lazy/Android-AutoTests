"""device-pool DRF HTTP 入口 — 10 个端点（薄层：解析 → 调 manager 四类 → 封信封）。

写操作经 registry / state_machine，本文件不直接 ORM 写。
响应经 EnvelopeJSONRenderer 统一为 {status, data} / {status, message}。
"""

import logging
import re

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from engines.device.registry import close_engine, open_engine

from .manager import DeviceError, detector, registry, serializer, state_machine
from .models import Device
from .pool import device as device_pool

logger = logging.getLogger(__name__)


def _device(serial: str) -> Device:
    """取设备记录，不存在抛 404。"""
    try:
        return Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        raise DeviceError(f"设备 {serial} 未注册", status_code=404)


# ═══════════════════════════════════════════════
# 设备列表 / 当前 / 激活
# ═══════════════════════════════════════════════


@api_view(["GET"])
def list_devices(request):
    """GET /api/devices/ — 设备列表 + 当前设备（含状态同步 + 可见性过滤）。"""
    try:
        state_machine.update_device_status()

        user_id = getattr(request, "user_id", "")
        admin_ids = serializer.resolve_admin_ids(settings.ADMIN_USERS)
        devices = [
            d for d in Device.objects.all() if serializer.is_device_visible(d, user_id, admin_ids)
        ]
        status_order = {"ONLINE": 0, "BUSY": 1}
        devices.sort(key=lambda d: status_order.get(d.status, 99))

        current_serial = device_pool.current_serial
        if not current_serial:
            online = [d for d in devices if d.status in ("ONLINE", "BUSY")]
            if online:
                first = online[0]
                device_pool.switch_to(first.serial)
                current_serial = first.serial

        # 当前设备指针是全局的，可能指向本用户不可见的设备 → 响应置 None（不改全局指针）
        visible_serials = {d.serial for d in devices}
        if current_serial not in visible_serials:
            current_serial = None

        # 锁定者/配置者存数字 ID，展示层转用户名（批量查询，避免 N+1）
        owner_ids = (
            {d.locked_by for d in devices if d.locked_by}
            | {d.added_by for d in devices if d.added_by}
            | {d.occupied_by for d in devices if d.occupied_by}
        )
        id_to_name = serializer.usernames_by_ids(owner_ids)
        result_list = [serializer.device_to_dict(d, current_serial, id_to_name) for d in devices]

        return Response(
            {
                "devices": result_list,
                "current": current_serial,
            }
        )
    except Exception:
        logger.exception("list_devices failed")
        return Response({"message": "设备列表加载失败"}, status=500)


@api_view(["GET"])
def device_current(request):
    """GET /api/devices/current — 当前活动设备信息。"""
    current_serial = device_pool.current_serial
    info: dict = {}
    app: dict = {}
    dev = None

    if current_serial:
        try:
            dev = Device.objects.get(serial=current_serial)
        except Device.DoesNotExist:
            dev = None
        if dev is not None:
            engine = open_engine(current_serial, dev.connection_addr or current_serial)
            try:
                info = engine.device_info
                app = engine.app_current()
            except Exception:
                logger.warning("读取设备前台失败 serial=%s", current_serial)
            finally:
                close_engine(engine)

    if dev is not None:
        return Response(
            {
                "serial": current_serial,
                "screen_w": dev.screen_w or info.get("displayWidth", 0),
                "screen_h": dev.screen_h or info.get("displayHeight", 0),
                "package": app.get("package", ""),
                "model": dev.model,
                "brand": dev.brand,
                "connection_type": dev.connection_type
                or ("WIFI" if ":" in current_serial else "USB"),
            }
        )
    return Response(
        {
            "serial": current_serial,
            "screen_w": info.get("displayWidth", 0),
            "screen_h": info.get("displayHeight", 0),
            "package": app.get("package", ""),
        }
    )


@api_view(["POST"])
def activate_device(request, serial):
    """POST /api/devices/{serial}/activate — 切换当前活动设备。"""
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        dev, _ = registry.register_device(serial, getattr(request, "user_id", ""))

    if dev.status == "BUSY":
        raise DeviceError("设备正在使用中，无法激活", status_code=400)

    device_pool.switch_to(serial)
    registry.touch_last_seen(dev)

    return Response({"current": serial})


# ═══════════════════════════════════════════════
# 扫描 / 连接 / 断开
# ═══════════════════════════════════════════════


@api_view(["POST"])
def scan_device(request):
    """POST /api/devices/scan — ADB 扫描注册（全量 / USB / WiFi）。"""
    target = (request.data.get("target") or "").strip()
    user_id = getattr(request, "user_id", "")

    try:
        if target:
            if ":" in target:
                _ip, _, _port = target.partition(":")
                _ip_ok = bool(
                    re.match(
                        r"^((25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[01]?\d?\d)$",
                        _ip,
                    )
                )
                _port_ok = _port.isdigit() and 1024 <= int(_port) <= 65535
                if not (_ip_ok and _port_ok):
                    return Response({"message": "无效的 IP 或端口"}, status=400)

                pair_port = (request.data.get("pair_port") or "").strip()
                pair_code = (request.data.get("pair_code") or "").strip()
                if pair_port or pair_code:
                    if not (pair_port and pair_code):
                        return Response({"message": "请同时填写配对端口和配对码"}, status=400)
                    detector.pair(_ip, pair_port, pair_code)

                detector.connect(target)
                dev, created = registry.register_device(target, user_id)
                state_machine.claim_wireless_device(dev, user_id)
                return Response(
                    {
                        "count": 1,
                        "newly_added": 1 if created else 0,
                        "devices": [serializer.device_to_dict(dev, device_pool.current_serial)],
                    }
                )

            adb_serials = detector.adb_device_serials()
            if target in adb_serials:
                dev, created = registry.register_device(target, user_id)
                return Response(
                    {
                        "count": 1,
                        "newly_added": 1 if created else 0,
                        "devices": [serializer.device_to_dict(dev, device_pool.current_serial)],
                    }
                )
            return Response({"message": f"device {target} not found"}, status=400)

        adb_serials = detector.adb_device_serials()
        newly_added = 0
        devices_out = []
        for addr in adb_serials:
            try:
                dev, created = registry.register_device(addr, user_id)
            except DeviceError:
                continue  # 无线设备未就绪（拿不到序列号），跳过本轮
            if created:
                newly_added += 1
            devices_out.append(serializer.device_to_dict(dev, device_pool.current_serial))

        if devices_out and device_pool.current_serial not in adb_serials:
            device_pool.switch_to(devices_out[0]["serial"])

        return Response(
            {
                "count": len(devices_out),
                "newly_added": newly_added,
                "devices": devices_out,
            }
        )
    except DeviceError:
        raise  # 交给 DRF 异常处理器返回具体 message（如无法解析序列号）
    except Exception:
        logger.exception("scan_device failed")
        return Response({"message": "扫描失败"}, status=500)


@api_view(["POST"])
def connect_device(request, serial):
    """POST /api/devices/{serial} — 连接 + 采集信息 + 自动激活（observe 模式置使用中）。"""
    activate = request.data.get("activate", True)
    mode = request.data.get("mode", "")
    user_id = getattr(request, "user_id", "") or ""

    dev = _device(serial)
    if dev.status == "BUSY":
        raise DeviceError("设备正在使用中，无法连接", status_code=409)

    # 连接地址：无线设备用 connection_addr（IP:port / mDNS），USB 用序列号本身
    addr = dev.connection_addr or serial
    ct = "WIFI" if detector.is_wireless(addr) else "USB"

    # 连接设备（无线 adb connect + u2 探活，逻辑在 detector.connect）
    detector.connect(addr)

    registry.set_connection_state(dev, ct)
    registry.collect_device_info(dev, addr)

    if activate:
        device_pool.switch_to(serial)

    if mode == "observe":
        state_machine.occupy_observe(dev, user_id)

    dev.refresh_from_db()
    return Response(
        {
            "serial": dev.serial,
            "model": dev.model,
            "screen_w": dev.screen_w,
            "screen_h": dev.screen_h,
            "android_version": dev.android_version,
        }
    )


@api_view(["POST"])
def disconnect_device(request, serial):
    """POST /api/devices/{serial}/disconnect — 删除设备（在线可删、使用中置灰、USB 无删除键）。"""
    dev = _device(serial)

    if dev.connection_type != "WIFI":
        raise DeviceError("USB 设备无删除键", status_code=400)
    if dev.status == "BUSY":
        raise DeviceError("设备使用中，无法删除", status_code=409)

    registry.delete_device_record(dev, reason="disconnect")
    logger.warning("设备 %s 已删除", serial)

    return Response({"serial": serial, "deleted": True})


@api_view(["POST"])
def disconnect_observe(request, serial):
    """POST /api/devices/{serial}/disconnect-observe — 轻量断开（不删记录，释放观察占用为 ONLINE）。"""
    device_pool.remove_device(serial)
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return Response({"serial": serial, "message": "设备观察连接已断开"})
    state_machine.release_observe(dev)
    return Response({"serial": serial, "message": "设备观察连接已断开"})


# ═══════════════════════════════════════════════
# 锁定 / 释放 / 心跳
# ═══════════════════════════════════════════════


@api_view(["POST"])
def lock_device(request, serial):
    """POST /api/devices/{serial}/lock — 锁定 / 公开切换（可见性）。"""
    locked = request.data.get("locked", True)
    user_id = getattr(request, "user_id", "") or request.data.get("user_id", "")

    dev = _device(serial)
    return Response(state_machine.set_device_lock(dev, bool(locked), user_id))


@api_view(["POST"])
def release_device(request, serial):
    """POST /api/devices/{serial}/release — 释放设备检查器占用。"""
    dev = _device(serial)
    return Response(state_machine.release_occupy(dev))


@api_view(["GET"])
def heartbeat(request):
    """GET /api/devices/heartbeat — 心跳同步。"""
    return Response(state_machine.heartbeat_sync())
