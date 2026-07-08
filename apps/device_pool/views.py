"""device-pool HTTP views — 12 endpoints under /api/devices/*.

v2 per PRD §6.2:
  v1 (5): list, scan, connect, disconnect, current, activate
  v2 (6): lock, release, queue, heartbeat, queue-join, queue-leave
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import uiautomator2 as u2

from .models import Device, DeviceLock, DeviceQueue
from .pool import device as device_pool
from .pool import DevicePool


# ═══════════════════════════════════════════════
# 核心 Helper 函数
# ═══════════════════════════════════════════════


def _adb_device_serials():
    """Return set of serials currently visible to adb."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        serials = set()
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                serials.add(parts[0])
        return serials
    except Exception:
        return set()


def _update_device_status():
    """Sync DB device status with actual ADB state.

    在 list_devices 和 heartbeat 端点中调用。

    Rules:
        - adb devices 列表中的 OFFLINE → ONLINE
        - DB 中 BUSY 但锁已超时 → 自动释放 (reason=timeout)
        - 不在 adb 列表中且非 BUSY → 标记 OFFLINE
    """
    _purge_disconnected_devices()
    now = datetime.now()
    adb_serials = _adb_device_serials()
    updated = 0
    offline = 0

    for dev in Device.objects.all():
        if dev.serial in adb_serials:
            # 设备在线
            if dev.status == "OFFLINE":
                dev.status = "ONLINE"
                dev.last_seen = now
                dev.save(update_fields=["status", "last_seen"])
                updated += 1

            # 检查 BUSY 设备的进程锁是否超时（仅 process 类型）
            if dev.status == "BUSY":
                active_lock = (
                    DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                    .order_by("-locked_at")
                    .first()
                )
                if active_lock and active_lock.is_expired:
                    _release_internal(dev, reason="timeout")
                    updated += 1
                elif active_lock:
                    # 更新 last_seen
                    dev.last_seen = now
                    dev.save(update_fields=["last_seen"])
                elif dev.locked_at:
                    # 没有 active 锁但有 locked_at（数据不一致），修复
                    elapsed = (now - dev.locked_at).total_seconds()
                    if elapsed > 300:
                        _release_internal(dev, reason="timeout")
                        updated += 1
        else:
            # 设备不在 adb 列表中
            if dev.status == "BUSY":
                # BUSY 设备可能暂时断 USB，检查进程锁超时
                active_lock = (
                    DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                    .order_by("-locked_at")
                    .first()
                )
                if active_lock and active_lock.is_expired:
                    _release_internal(dev, reason="timeout")
                    dev.status = "OFFLINE"
                    dev.save(update_fields=["status"])
                    updated += 1
                    offline += 1
                # 否则保持 BUSY（保护进行中的任务）
            else:
                dev.status = "OFFLINE"
                dev.save(update_fields=["status"])
                offline += 1

    return updated, offline


def _delete_device_record(dev, *, reason="disconnect"):
    """Remove a device row and its pool cache entry (no DISCONNECTED tombstone)."""
    serial = dev.serial
    if dev.status == "BUSY":
        _release_internal(dev, reason=reason)
    device_pool.remove_device(serial)
    dev.delete()


def _release_internal(dev, reason="manual", clear_lock=False):
    """内部释放占用：清空 occupied_by + 恢复 ONLINE。

    不删除锁记录（保留审计）。
    """
    now = datetime.now()

    # 标记活跃锁为 released（进程+用户均释放）
    DeviceLock.objects.filter(device=dev, status="active").update(
        status="released",
        released_at=now,
        release_reason=reason,
    )

    # 清空进程占用
    dev.occupied_by = ""
    dev.occupied_at = None
    update_fields = ["occupied_by", "occupied_at"]
    if dev.status == "BUSY":
        dev.status = "ONLINE"
        update_fields.append("status")
    if clear_lock:
        dev.locked_by = ""
        dev.locked_at = None
        update_fields.extend(["locked_by", "locked_at"])
    dev.save(update_fields=update_fields)

    print(f"[INFO] 设备 {dev.serial} 已释放占用 (reason={reason})")

    # 触发队列分配
    assigned = _auto_assign_from_queue(dev)
    if assigned:
        print(f"[INFO] 设备 {dev.serial} 已从队列分配给 {assigned}")


def _purge_disconnected_devices():
    """Delete legacy DISCONNECTED rows — not kept as history."""
    stale = list(Device.objects.filter(status="DISCONNECTED"))
    for dev in stale:
        _delete_device_record(dev, reason="purge")
    return len(stale)


def _collect_device_info(dev, serial):
    """通过 uiautomator2 采集设备信息并更新 Device 记录。

    采集: model, brand, screen_w, screen_h, android_version
    """
    try:
        d = u2.connect(serial)
        info = d.info
        dev.model = info.get("productName", "") or ""
        dev.brand = info.get("brand", "") or ""
        dev.screen_w = info.get("displayWidth", 0) or 0
        dev.screen_h = info.get("displayHeight", 0) or 0
        sdk = info.get("sdkInt", 0)
        dev.android_version = str(sdk) if sdk else ""
        dev.last_seen = datetime.now()
        dev.save(
            update_fields=[
                "model",
                "brand",
                "screen_w",
                "screen_h",
                "android_version",
                "last_seen",
            ]
        )
        print(
            f"[INFO] 设备信息已采集: {dev.serial} → {dev.brand} {dev.model} "
            f"{dev.screen_w}x{dev.screen_h} SDK={dev.android_version}"
        )
    except Exception as e:
        print(f"[WARN] 采集设备信息失败 {serial}: {e}")


def _auto_assign_from_queue(dev):
    """释放后从队列中分配第一个等待用户。

    Returns: 被分配的用户 ID，或 None（队列为空）。
    """
    entry = (
        DeviceQueue.objects.filter(device=dev, status="waiting").order_by("requested_at").first()
    )

    if not entry:
        return None

    entry.status = "assigned"
    entry.assigned_at = datetime.now()
    entry.save(update_fields=["status", "assigned_at"])

    # 自动绑定用户
    dev.locked_by = entry.user_id
    dev.locked_at = datetime.now()
    dev.save(update_fields=["locked_by", "locked_at"])

    DeviceLock.objects.create(
        device=dev,
        user_id=entry.user_id,
        lock_type="user",
        timeout_seconds=300,
        status="active",
    )

    return entry.user_id


def _check_timeout_queue():
    """清理超过 600 秒未响应的排队记录。"""
    cutoff = datetime.now() - timedelta(seconds=600)
    expired = DeviceQueue.objects.filter(status="waiting", requested_at__lt=cutoff).update(
        status="timeout"
    )
    if expired:
        print(f"[INFO] {expired} 条排队记录超时自动取消")


def _device_to_dict(dev, current_serial):
    """将 Device ORM 对象转为 PRD §6.2.1 响应格式。"""
    now = datetime.now()
    result = {
        "id": dev.id,
        "serial": dev.serial,
        "name": dev.name,
        "model": dev.model,
        "brand": dev.brand,
        "screen": f"{dev.screen_w}x{dev.screen_h}" if dev.screen_w else "",
        "status": dev.status,
        "connection_type": dev.connection_type or ("WIFI" if ":" in dev.serial else "USB"),
        "locked_by": dev.locked_by,
        "locked_at": dev.locked_at.isoformat() if dev.locked_at else None,
        "occupied_by": dev.occupied_by,
        "occupied_at": dev.occupied_at.isoformat() if dev.occupied_at else None,
        "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
        "is_current": dev.serial == current_serial,
    }

    # BUSY 设备：计算剩余时间（进程占用，非用户绑定）
    if dev.status == "BUSY" and (dev.occupied_by or dev.locked_by):
        active_lock = (
            DeviceLock.objects.filter(device=dev, status="active").order_by("-locked_at").first()
        )
        if active_lock:
            result["remaining"] = active_lock.remaining_seconds
            result["locked_by"] = dev.locked_by
        else:
            result["remaining"] = 0
    else:
        result["remaining"] = 0

    return result


# ═══════════════════════════════════════════════
# v1 endpoints (5)
# ═══════════════════════════════════════════════


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
                # 无线 ADB
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
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    activate = data.get("activate", True)

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

    # 7. 自动锁定（如果提供了 user_id）
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


# ═══════════════════════════════════════════════
# v2 endpoints (6)
# ═══════════════════════════════════════════════


@csrf_exempt
def lock_device(request, serial):
    """POST /api/devices/{serial}/lock — 用户绑定或进程占用。

    type="user" (default): 用户绑定 — 设置 locked_by，不改 status
    type="occupy": 进程占用 — 设置 occupied_by，改 status=BUSY
    """
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})

    lock_type = data.get("type", "user")
    user_id = data.get("user_id", "").strip()
    if not user_id:
        return JsonResponse({"ok": False, "error": "user_id 不能为空"}, status=400)
    timeout = int(data.get("timeout", 300))

    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        return JsonResponse({"ok": False, "error": f"设备 {serial} 未注册"}, status=404)

    if dev.status == "OFFLINE" or dev.status == "DISCONNECTED":
        return JsonResponse({"ok": False, "error": f"设备已{dev.status}，无法操作"}, status=400)

    now = datetime.now()

    # ── 进程占用 ──
    if lock_type == "occupy":
        if dev.occupied_by and dev.occupied_by != user_id:
            return JsonResponse(
                {"ok": False, "error": f"设备已被 {dev.occupied_by} 占用"}, status=409
            )
        dev.occupied_by = user_id
        dev.occupied_at = now
        dev.status = "BUSY"
        dev.save(update_fields=["occupied_by", "occupied_at", "status"])
        DeviceLock.objects.create(
            device=dev,
            user_id=user_id,
            lock_type="process",
            timeout_seconds=timeout,
            status="active",
        )
        return JsonResponse(
            {
                "ok": True,
                "serial": serial,
                "occupied_by": user_id,
                "occupied_at": now.isoformat(),
                "timeout": timeout,
            }
        )

    # ── 用户绑定 ──
    if dev.locked_by and dev.locked_by != user_id:
        return JsonResponse({"ok": False, "error": f"设备已被 {dev.locked_by} 绑定"}, status=409)
    dev.locked_by = user_id
    dev.locked_at = now
    dev.save(update_fields=["locked_by", "locked_at"])
    DeviceLock.objects.create(
        device=dev,
        user_id=user_id,
        lock_type="user",
        timeout_seconds=timeout,
        status="active",
    )
    return JsonResponse(
        {
            "ok": True,
            "serial": serial,
            "user_id": user_id,
            "locked_at": now.isoformat(),
            "timeout": timeout,
            "is_occupied": dev.is_occupied,
        }
    )


def release_device(request, serial):
    """POST /api/devices/{serial}/release — 释放设备锁。

    PRD §6.2.5: 手动/超时/断开/强制释放，保留锁审计。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    reason = data.get("reason", "manual")
    user_id = data.get("user_id", "").strip()

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

    # 解除进程占用 + 可选解除用户绑定
    # (不再检查 status==BUSY，因为 lock 不再改 status)
    force_release = data.get("force", False)
    unlock_too = data.get("unlock", False)  # 同时解除用户绑定
    occupied_by = dev.occupied_by or ""

    # 执行引擎占用 → 禁止解除（除非强制）
    is_runner_occupied = (
        occupied_by.startswith("ai_agent")
        or occupied_by.startswith("runner-")
        or occupied_by.startswith("task-")
        or occupied_by.startswith("run-")
    )

    if is_runner_occupied and not force_release:
        return JsonResponse(
            {
                "ok": False,
                "error": "设备正在执行用例，无法解除占用。请等待用例执行完毕或先停止执行任务。",
                "occupied_by": occupied_by,
                "is_runner": True,
            },
            status=409,
        )

    # 仅解除用户绑定（不清 occupied_by）
    if unlock_too and not dev.occupied_by:
        if not dev.locked_by:
            return JsonResponse({"ok": False, "error": "设备未被绑定，无需操作"}, status=400)
        dev.locked_by = ""
        dev.locked_at = None
        dev.save(update_fields=["locked_by", "locked_at"])
        DeviceLock.objects.filter(device=dev, lock_type="user", status="active").update(
            status="released", released_at=datetime.now(), release_reason="manual"
        )
        return JsonResponse({"ok": True, "serial": serial, "unlocked": True})

    # 解除占用（委托给共享 helper，保证 DeviceLock 审计 + 队列自动分配）
    if not dev.occupied_by:
        return JsonResponse({"ok": False, "error": "设备未被占用，无需操作"}, status=400)
    _release_internal(dev, reason="force" if force_release else "manual", clear_lock=unlock_too)

    return JsonResponse(
        {
            "ok": True,
            "serial": serial,
            "released": True,
            "force_released": force_release,
            "unlocked": unlock_too,
        }
    )


def device_queue(request):
    """GET /api/devices/queue — 排队状态。

    PRD §6.2.7: 返回当前所有等待中的排队记录（FIFO）。
    """
    entries = (
        DeviceQueue.objects.filter(status="waiting")
        .select_related("device")
        .order_by("requested_at")
    )

    now = datetime.now()
    result = []
    for i, entry in enumerate(entries):
        waited = int((now - entry.requested_at).total_seconds())
        result.append(
            {
                "position": i + 1,
                "serial": entry.device.serial,
                "user_id": entry.user_id,
                "requested_at": entry.requested_at.isoformat(),
                "waited_seconds": waited,
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "queue": result,
            "count": len(result),
        }
    )


def heartbeat(request):
    """GET /api/devices/heartbeat — 手动触发心跳检测。

    PRD §6.2.7: 同步设备状态，清理过期锁和排队。
    """
    updated, offline = _update_device_status()
    _check_timeout_queue()

    online = Device.objects.filter(status="ONLINE").count()
    busy = Device.objects.filter(status="BUSY").count()
    offline_count = Device.objects.filter(status="OFFLINE").count()
    disconnected = Device.objects.filter(status="DISCONNECTED").count()

    return JsonResponse(
        {
            "ok": True,
            "updated": updated,
            "offline": offline,
            "online": online,
            "busy": busy,
            "offline_count": offline_count,
            "disconnected": disconnected,
            "total": online + busy + offline_count + disconnected,
        }
    )


# ═══════════════════════════════════════════════
# v2 排队管理端点 (新增 2 个)
# ═══════════════════════════════════════════════


@csrf_exempt
def join_device_queue(request, serial):
    """POST /api/devices/{serial}/queue — 加入排队。

    防重复：同一用户对同一设备只能排队一次。
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid JSON"})

    user_id = data.get("user_id", "").strip()
    if not user_id:
        return JsonResponse(
            {
                "ok": False,
                "error": "user_id 不能为空",
            },
            status=400,
        )

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

    # 防重复
    existing = DeviceQueue.objects.filter(device=dev, user_id=user_id, status="waiting").first()
    if existing:
        waited = int((datetime.now() - existing.requested_at).total_seconds())
        position = (
            DeviceQueue.objects.filter(
                device=dev,
                status="waiting",
                requested_at__lt=existing.requested_at,
            ).count()
            + 1
        )
        return JsonResponse(
            {
                "ok": True,
                "message": "已在排队中",
                "position": position,
                "waited_seconds": waited,
            }
        )

    # 创建排队
    entry = DeviceQueue.objects.create(
        device=dev,
        user_id=user_id,
        status="waiting",
    )

    position = (
        DeviceQueue.objects.filter(
            device=dev,
            status="waiting",
            requested_at__lt=entry.requested_at,
        ).count()
        + 1
    )

    return JsonResponse(
        {
            "ok": True,
            "message": f"已加入 {serial} 的排队队列",
            "position": position,
            "waited_seconds": 0,
        }
    )


@csrf_exempt
def leave_device_queue(request, serial):
    """DELETE /api/devices/{serial}/queue — 取消排队。"""
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    user_id = data.get("user_id", "").strip()

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

    # 取消排队
    qs = DeviceQueue.objects.filter(device=dev, status="waiting")
    if user_id:
        qs = qs.filter(user_id=user_id)

    updated = qs.update(status="cancelled")

    return JsonResponse(
        {
            "ok": True,
            "cancelled": updated,
        }
    )
