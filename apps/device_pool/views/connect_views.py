"""Device connection endpoints — scan, connect, disconnect."""
import json
import re
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import uiautomator2 as u2
from .helpers import (
    _adb_device_serials, _update_device_status, _delete_device_record,
    _collect_device_info, _auto_assign_from_queue, _device_to_dict,
)
from ..models import Device
from ..pool import device as device_pool
@csrf_exempt
def scan_device(request):
    """POST /api/devices/scan — ADB 扫描并注册设备。
    PRD §6.2.2: 支持指定 target 或全量扫描。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})
    target = data.get("target", "").strip()

    try:
        if target:
            # 指定目标：USB 串号 或 IP:port
            if ":" in target:
                # 无线 ADB — 纵深防御：校验 IP/端口格式，避免非法输入透传给 adb（PRD §3.7）
                _ip, _, _port = target.partition(":")
                _ip_ok = bool(
                    re.match(
                        r"^((25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
                        r"(25[0-5]|2[0-4]\d|[01]?\d?\d)$",
                        _ip,
                    )
                )
                _port_ok = _port.isdigit() and 1 <= int(_port) <= 65535
                if not (_ip_ok and _port_ok):
                    return JsonResponse({"ok": False, "error": "无效的 IP 或端口"}, status=400)
                result = subprocess.run(
                    ["adb", "connect", target],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout + result.stderr
                if "connected" in output.lower() or "already" in output.lower():
                    dev, created = Device.objects.update_or_create(
                        serial=target,
                        defaults={
                            "status": "ONLINE",
                            "connection_type": "WIFI",
                        },
                    )
                    if created:
                        _collect_device_info(dev, target)
                    return JsonResponse(
                        {
                            "ok": True,
                            "count": 1,
                            "newly_added": 1 if created else 0,
                            "devices": [_device_to_dict(dev, device_pool.current_serial)],
                        }
                    )
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"无法连接到 {target}，请检查设备网络和 ADB 服务",
                    },
                    status=400,
                )
            else:
                # USB 串号
                adb_serials = _adb_device_serials()
                if target in adb_serials:
                    dev, created = Device.objects.update_or_create(
                        serial=target,
                        defaults={
                            "status": "ONLINE",
                            "connection_type": "USB",
                        },
                    )
                    if created:
                        _collect_device_info(dev, target)
                    return JsonResponse(
                        {
                            "ok": True,
                            "count": 1,
                            "newly_added": 1 if created else 0,
                            "devices": [_device_to_dict(dev, device_pool.current_serial)],
                        }
                    )
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"device {target} not found",
                    },
                    status=400,
                )
        else:
            # 全量扫描
            adb_serials = _adb_device_serials()
            newly_added = 0
            devices_out = []

            for serial in adb_serials:
                ct = "WIFI" if ":" in serial else "USB"
                dev, created = Device.objects.update_or_create(
                    serial=serial,
                    defaults={"status": "ONLINE", "connection_type": ct},
                )
                if created:
                    newly_added += 1
                    _collect_device_info(dev, serial)
                else:
                    # 更新状态（如果之前是 OFFLINE）
                    if dev.status != "ONLINE" and dev.status != "BUSY":
                        dev.status = "ONLINE"
                        dev.save(update_fields=["status"])
                devices_out.append(_device_to_dict(dev, device_pool.current_serial))

            # 将扫描到的设备设为首选 current（如果还没设置）
            if devices_out and device_pool.current_serial not in adb_serials:
                first = devices_out[0]
                device_pool.switch_to(first["serial"], ct or "USB")

            return JsonResponse(
                {
                    "ok": True,
                    "count": len(devices_out),
                    "newly_added": newly_added,
                    "devices": devices_out,
                }
            )
    except subprocess.TimeoutExpired:
        return JsonResponse(
            {
                "ok": False,
                "error": "连接超时，请检查设备 USB/WiFi 连接",
            },
            status=504,
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})
@csrf_exempt
def connect_device(request, serial):
    """POST /api/devices/{serial} — 连接设备 + 自动激活 + 锁定。

    PRD §6.2.3: 建立 u2 连接，采集设备信息，自动切换+锁定。

    mode="observe": 轻量连接模式，仅切换 DevicePool 指针，不锁定设备。
    供 element-locator / case-manager 等临时使用场景。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    activate = data.get("activate", True)
    observe_mode = data.get("mode", "") == "observe"

    # 1. 查找设备记录
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 未注册",
            },
            status=404,
        )

    # 2. 状态校验
    if dev.status in ("OFFLINE", "DISCONNECTED"):
        return JsonResponse(
            {
                "ok": False,
                "error": "设备已离线，无法连接",
            },
            status=400,
        )

    # 3. 检查是否被他人占用
    if dev.status == "BUSY" and (dev.occupied_by or dev.locked_by):
        current_user = data.get("user_id", "")
        if current_user and dev.locked_by != current_user:
            active_lock = (
                DeviceLock.objects.filter(device=dev, status="active")
                .order_by("-locked_at")
                .first()
            )
            remaining = active_lock.remaining_seconds if active_lock else 0
            if remaining > 0:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"设备已被 {dev.locked_by} 锁定，剩余 {remaining} 秒",
                        "locked_by": dev.locked_by,
                        "remaining": remaining,
                    },
                    status=409,
                )

    # 4. 连接设备
    try:
        if ":" in serial:
            # 无线：先 adb connect
            result = subprocess.run(
                ["adb", "connect", serial],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout + result.stderr
            if "connected" not in output.lower() and "already" not in output.lower():
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"连接超时，请检查设备 USB/WiFi 连接",
                    },
                    status=504,
                )

        # uiautomator2 连接
        try:
            d = u2.connect(serial)
            _ = d.info  # 验证连接
        except Exception as e:
            error_msg = str(e)
            if "atx-agent" in error_msg.lower() or "offline" in error_msg.lower():
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务",
                    },
                    status=502,
                )
            return JsonResponse(
                {
                    "ok": False,
                    "error": f"连接超时，请检查设备 USB/WiFi 连接",
                },
                status=504,
            )

    except subprocess.TimeoutExpired:
        return JsonResponse(
            {
                "ok": False,
                "error": "连接超时，请检查设备 USB/WiFi 连接",
            },
            status=504,
        )

    # 5. 采集设备信息
    ct = "WIFI" if ":" in serial else "USB"
    dev.connection_type = ct
    dev.status = "ONLINE"
    dev.save(update_fields=["connection_type", "status"])
    _collect_device_info(dev, serial)

    # 6. 自动激活
    if activate:
        device_pool.switch_to(serial, ct)

    # 7. 自动锁定（如果提供了 user_id）— observe 模式跳过
    if not observe_mode:
        user_id = data.get("user_id", "").strip()
        if user_id:
            # 先检查是否已有活跃锁
            has_active = DeviceLock.objects.filter(device=dev, status="active").exists()
            if not has_active:
                timeout = data.get("timeout", 300)
                dev.status = "BUSY"
                dev.locked_by = user_id
                dev.locked_at = datetime.now()
                dev.save(update_fields=["status", "locked_by", "locked_at"])
                DeviceLock.objects.create(
                    device=dev,
                    user_id=user_id,
                    lock_type="user",
                    timeout_seconds=timeout,
                    status="active",
                )

    # 8. 重新读取最新值
    dev.refresh_from_db()

    return JsonResponse(
        {
            "ok": True,
            "serial": dev.serial,
            "model": dev.model,
            "screen_w": dev.screen_w,
            "screen_h": dev.screen_h,
            "android_version": dev.android_version,
        }
    )
@csrf_exempt
def disconnect_device(request, serial):
    """POST /api/devices/{serial}/disconnect — 断开设备。

    PRD §6.2.6 + F-05: 支持强制断开、权限校验、审计日志。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    force = data.get("force", False)
    reason = data.get("reason", "")

    # 1. 查找设备
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": f"设备 {serial} 未注册",
            },
            status=404,
        )

    # 2. 权限校验（检查进程占用或用户绑定）
    if dev.status == "BUSY" and (dev.occupied_by or dev.locked_by):
        current_user = data.get("user_id", "")
        is_admin = data.get("is_admin", False)

        if current_user and dev.locked_by != current_user:
            if not force or not is_admin:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "设备正被他人使用，断开需要管理员权限和 force 标记",
                    },
                    status=403,
                )
            if not reason:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "强制断开他人设备时必须填写原因",
                    },
                    status=400,
                )

    # 3. 执行断开
    locks_released = 0
    if ":" in serial:
        subprocess.run(
            ["adb", "disconnect", serial],
            capture_output=True,
            text=True,
            timeout=5,
        )

    # 4. 清理缓存
    device_pool.remove_device(serial)

    # 5. 释放锁
    if dev.status == "BUSY":
        rsn = "force" if force else "disconnect"
        _release_internal(dev, reason=rsn)
        locks_released = 1

    # 6. 删除记录（不保留 DISCONNECTED 历史）
    serial = dev.serial
    user = data.get("user_id", "system")
    _delete_device_record(dev, reason="force" if force else "disconnect")
    print(f"[WARNING] 设备 {serial} 已被 {user} 断开并移除 (reason={reason or 'manual'})")

    return JsonResponse(
        {
            "ok": True,
            "serial": serial,
            "disconnected": True,
            "locks_released": locks_released,
        }
    )


@csrf_exempt
def disconnect_observe(request, serial):
    """POST /api/devices/{serial}/disconnect-observe — 轻量断开设备连接。

    element-locator / case-manager observe 模式下的断开操作。
    仅清理 uiautomator2 连接缓存，不删除 DB 记录，不释放锁。
    """
    device_pool.remove_device(serial)
    return JsonResponse({"ok": True, "serial": serial, "message": "设备观察连接已断开"})


# ═══════════════════════════════════════════════
# v2 endpoints (6)
# ═══════════════════════════════════════════════


