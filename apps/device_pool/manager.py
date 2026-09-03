"""device-pool 设备管理 — 四个职责类（L3 业务层数据面）。

单一职责划分：探测 / 注册落库 / 状态机 / 展示，各自独立、组合协作：
  DeviceDetector      探测：ADB 发现 + 身份解析 + 元信息采集（产出 DeviceInfo，不落库）
  DeviceRegistry      注册落库：dp_devices 增删 + 连接状态（依赖 Detector）
  DeviceStateMachine  状态机：ONLINE/BUSY 判定 + 同步 + 锁定/释放/占用 + 心跳（依赖 Detector + Registry）
  DeviceSerializer    展示：可见性过滤 + 序列化（只读，独立）

与 pool.DevicePool 分工：本模块管「数据面」（dp_devices 记录与状态机），DevicePool 管
「连接/会话/操作面」。写库仍经本模块类方法（由 api.py 白名单转调）。
"""

import logging
import subprocess
import time

from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.exceptions import APIException

from engines.device.base import EngineConnectError
from engines.device.connection import fetch_device_info, probe_u2

from .contracts import RUNNER_OCCUPIED_PREFIXES, ConnectionType, DeviceInfo, DeviceStatus
from .models import Device, DeviceLock
from .pool import device as device_pool

logger = logging.getLogger(__name__)

# observe 观察占用锁的兜底超时（秒）：关页/崩溃无释放时，30 分钟后由心跳回收
OBSERVE_LOCK_TTL = 1800


class DeviceError(APIException):
    """设备业务错误 — 由 DRF 异常处理器自动映射为 HTTP 响应。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class DeviceDetector:
    """设备探测 — ADB 发现 + 身份解析 + 元信息采集（产出 DeviceInfo，不落库）。"""

    def detect(self) -> list[DeviceInfo]:
        """检测设备：adb devices 发现 + 序列号解析，返回检测结果契约列表。

        无线设备解析不到真实序列号时跳过（身份不明不纳入），口径与状态同步的注册一致：
        USB 恒可解析，无线需 getprop ro.serialno 就绪。
        """
        detected: list[DeviceInfo] = []
        for addr in self.adb_device_serials():
            serial, conn_addr = self.resolve_serial(addr)
            if not serial:
                continue
            detected.append(
                DeviceInfo(
                    serial=serial,
                    connection_type=(
                        ConnectionType.WIFI if self.is_wireless(addr) else ConnectionType.USB
                    ),
                    connection_addr=conn_addr,
                )
            )
        return detected

    def adb_device_serials(self) -> set:
        """返回当前 adb 可见设备的地址集合（USB 串号 / 无线 IP:port）。"""
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

    def is_wireless(self, addr: str) -> bool:
        """判断是否无线设备（IP:port 或 mDNS transport）。"""
        return ":" in addr or addr.startswith("adb-")

    def fetch_serial_no(self, addr: str) -> str:
        """获取设备真实序列号 ro.serialno（无线设备连接后需短暂等待，带重试）。"""
        for attempt in range(3):
            try:
                result = subprocess.run(
                    ["adb", "-s", addr, "shell", "getprop", "ro.serialno"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                serial = result.stdout.strip()
                if serial:
                    return serial
            except Exception:
                pass
            if attempt < 2:
                time.sleep(1)
        return ""

    def _getprop(self, addr: str, prop: str) -> str:
        """读取设备 property（如 ro.product.model），失败返回空串。"""
        try:
            result = subprocess.run(
                ["adb", "-s", addr, "shell", "getprop", prop],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def resolve_serial(self, addr: str) -> tuple[str, str]:
        """解析设备序列号与连接地址：USB 直接取 addr，无线取 ro.serialno + addr。

        无线设备解析不到真实序列号时返回 ("", addr)，由调用方跳过注册，避免用
        传输地址（IP:port）顶替 serial —— 地址会随重连变化，导致设备身份漂移。
        """
        if self.is_wireless(addr):
            serial = self.fetch_serial_no(addr)
            if not serial and addr.startswith("adb-"):
                # mDNS 名称内嵌序列号：adb-<serial>-<random>._adb...
                parts = addr.split("-")
                serial = parts[1] if len(parts) > 1 else ""
            return serial, addr
        return addr, ""

    def get_info(self, addr: str) -> DeviceInfo:
        """获取设备信息：采集元信息（model/brand/分辨率/Android 版本），返回契约。

        只采集返回、不落库；serial 由 detect() 阶段产出，本方法不重复解析序列号。
        失败抛异常，由调用方处理（DeviceRegistry.collect_device_info 会兜底捕获）。
        """
        raw = fetch_device_info(addr)
        return DeviceInfo(
            model=self._getprop(addr, "ro.product.model") or raw.get("productName", "") or "",
            brand=self._getprop(addr, "ro.product.brand") or "",
            screen_w=raw.get("displayWidth", 0) or 0,
            screen_h=raw.get("displayHeight", 0) or 0,
            android_version=str(raw.get("sdkInt", 0)) if raw.get("sdkInt", 0) else "",
        )

    def connect(self, addr: str) -> None:
        """连接设备：无线 IP:port 先 adb connect，随后 u2 探活验证。

        Raises:
            DeviceError: 连接失败（超时 / ATX Agent 未运行 / 无法连接）。
        """
        try:
            if ":" in addr:
                result = subprocess.run(
                    ["adb", "connect", addr], capture_output=True, text=True, timeout=10
                )
                output = result.stdout + result.stderr
                if "connected" not in output.lower() and "already" not in output.lower():
                    raise DeviceError("连接超时，请检查设备 USB/WiFi 连接", status_code=504)
            probe_u2(addr)
        except subprocess.TimeoutExpired:
            raise DeviceError("连接超时，请检查设备 USB/WiFi 连接", status_code=504)
        except EngineConnectError as e:
            error_msg = str(e)
            if "atx-agent" in error_msg.lower() or "offline" in error_msg.lower():
                raise DeviceError(
                    "设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务", status_code=502
                )
            raise DeviceError("连接超时，请检查设备 USB/WiFi 连接", status_code=504)


class DeviceRegistry:
    """设备注册落库 — dp_devices 增删 + 连接状态（依赖 DeviceDetector）。"""

    def __init__(self, detector: DeviceDetector):
        self._detector = detector

    def register_device(self, addr: str, user_id: str = "") -> tuple[Device, bool]:
        """注册设备（update_or_create），无线设备取 ro.serialno 作为序列号。返回 (dev, created)。

        Raises:
            DeviceError: 无线设备解析不到真实序列号（设备未就绪）。
        """
        serial, conn_addr = self._detector.resolve_serial(addr)
        if not serial:
            raise DeviceError(
                f"无法解析设备 {addr} 的序列号，请确认设备在线后重试", status_code=502
            )
        ct = "WIFI" if self._detector.is_wireless(addr) else "USB"
        now = datetime.now()
        dev, created = Device.objects.update_or_create(
            serial=serial,
            defaults={
                "status": "ONLINE",
                "connection_type": ct,
                "connection_addr": conn_addr,
            },
        )
        # 清理旧数据：serial 曾存无线传输地址（IP:port / mDNS）的旧记录
        if serial != addr:
            Device.objects.filter(serial=addr).delete()
        if created:
            dev.connected_at = now
            dev.added_by = user_id
            dev.save(update_fields=["connected_at", "added_by"])
            self.collect_device_info(dev, addr)
        return dev, created

    def collect_device_info(self, dev: Device, addr: str) -> None:
        """通过 uiautomator2 采集设备元信息并更新记录（L1c：经引擎静态方法）。"""
        try:
            info = self._detector.get_info(addr)
            dev.model = info.model
            dev.brand = info.brand
            dev.screen_w = info.screen_w
            dev.screen_h = info.screen_h
            dev.android_version = info.android_version
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
        except Exception as e:
            logger.warning("采集设备信息失败 %s: %s", addr, e)

    def delete_device_record(self, dev: Device, reason: str = "disconnect") -> None:
        """删除设备行并清理连接缓存（不保留离线/DISCONNECTED 墓碑）。

        标记活跃锁为 released（保留审计）。
        """
        DeviceLock.objects.filter(device=dev, status="active").update(
            status="released",
            released_at=datetime.now(),
            release_reason=reason,
        )
        device_pool.remove_device(dev.serial)
        if dev.connection_addr:
            device_pool.remove_device(dev.connection_addr)
        dev.delete()

    def purge_disconnected_devices(self) -> int:
        """删除遗留的 DISCONNECTED 行（不作为历史保留）。"""
        stale = list(Device.objects.filter(status="DISCONNECTED"))
        for dev in stale:
            self.delete_device_record(dev, reason="purge")
        return len(stale)

    def set_connection_state(self, dev: Device, connection_type: str) -> None:
        """设置连接类型 + 状态 ONLINE 并落库（连接成功后调用）。"""
        dev.connection_type = connection_type
        dev.status = "ONLINE"
        dev.save(update_fields=["connection_type", "status"])

    def touch_last_seen(self, dev: Device) -> None:
        """刷新最后在线时间戳。"""
        dev.last_seen = datetime.now()
        dev.save(update_fields=["last_seen"])


class DeviceStateMachine:
    """设备状态机 — ONLINE/BUSY 判定 + 同步 + 锁定/释放/占用 + 心跳（依赖 Detector + Registry）。"""

    def __init__(self, detector: DeviceDetector, registry: DeviceRegistry):
        self._detector = detector
        self._registry = registry

    def judge_status(self, dev: Device) -> DeviceStatus:
        """判断设备权威状态：BUSY 且持有未过期进程锁 → BUSY；否则 ONLINE。

        只读判定、不写库；锁过期回收动作由 update_device_status 执行。
        """
        if dev.status == "BUSY":
            active_lock = (
                DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                .order_by("-locked_at")
                .first()
            )
            if active_lock and not active_lock.is_expired:
                return DeviceStatus.BUSY
            return DeviceStatus.ONLINE
        return DeviceStatus.ONLINE

    def update_device_status(self) -> tuple[int, int]:
        """同步 DB 设备状态与真实 ADB 状态（list/heartbeat 触发）。

        含「注册 adb 新设备」——设备发现是状态同步的一部分（见 PRD §4.4）。
        设备不在 adb 列表时：BUSY 保护进行中任务；非 BUSY 直接删除（不保留离线记录）。
        """
        self._registry.purge_disconnected_devices()
        now = datetime.now()
        adb_serials = self._detector.adb_device_serials()
        updated = 0
        removed = 0

        # 注册 adb 可见但 DB 未登记的设备
        for addr in adb_serials:
            serial, conn_addr = self._detector.resolve_serial(addr)
            if not serial:
                # 无线设备未就绪（拿不到 ro.serialno）：清理旧地址记录，但不新建
                Device.objects.filter(serial=addr).delete()
                continue
            dev, created = Device.objects.get_or_create(
                serial=serial,
                defaults={
                    "status": "ONLINE",
                    "connection_type": "WIFI" if self._detector.is_wireless(addr) else "USB",
                    "connection_addr": conn_addr,
                },
            )
            # 记录首次连接时间点：新建取 now，历史遗留用首次发现时间（created_at）回填
            if dev.connected_at is None:
                dev.connected_at = now if created else (dev.created_at or now)
                dev.save(update_fields=["connected_at"])
            # 新建或元信息缺失时采集型号/分辨率（u2 连接有开销，仅缺失时执行）
            if created or not dev.model or not dev.screen_w:
                self._registry.collect_device_info(dev, addr)
            # 清理旧数据：serial 曾存无线传输地址的旧记录
            if serial != addr:
                Device.objects.filter(serial=addr).delete()

        for dev in list(Device.objects.all()):
            visible = dev.serial in adb_serials or (
                dev.connection_addr and dev.connection_addr in adb_serials
            )
            if visible:
                # USB 设备恒公开，清理历史锁定数据
                if dev.connection_type != "WIFI" and (dev.locked_by or dev.locked_at):
                    dev.locked_by = ""
                    dev.locked_at = None
                    dev.save(update_fields=["locked_by", "locked_at"])
                if dev.status == "BUSY":
                    active_lock = (
                        DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                        .order_by("-locked_at")
                        .first()
                    )
                    if active_lock and active_lock.is_expired:
                        self.release_internal(dev, reason="timeout")
                        updated += 1
                    elif active_lock:
                        dev.last_seen = now
                        dev.save(update_fields=["last_seen"])
            else:
                # 不在 adb：BUSY 保护进行中任务；非 BUSY 删除记录
                if dev.status == "BUSY":
                    active_lock = (
                        DeviceLock.objects.filter(device=dev, lock_type="process", status="active")
                        .order_by("-locked_at")
                        .first()
                    )
                    if active_lock and active_lock.is_expired:
                        self._registry.delete_device_record(dev, reason="offline")
                        removed += 1
                else:
                    self._registry.delete_device_record(dev, reason="offline")
                    removed += 1

        return updated, removed

    def set_device_lock(self, dev: Device, locked: bool, user_id: str) -> dict:
        """锁定 / 公开切换（可见性）。USB 设备无锁定能力。"""
        if dev.connection_type != "WIFI":
            raise DeviceError("USB 设备不支持锁定", status_code=400)

        now = datetime.now()
        if locked:
            if dev.locked_by and dev.locked_by != user_id:
                raise DeviceError(f"设备已被 {dev.locked_by} 锁定", status_code=409)
            dev.locked_by = user_id
            dev.locked_at = now
            dev.save(update_fields=["locked_by", "locked_at"])
            DeviceLock.objects.create(
                device=dev, user_id=user_id, lock_type="user", status="active"
            )
        else:
            dev.locked_by = ""
            dev.locked_at = None
            dev.save(update_fields=["locked_by", "locked_at"])
            DeviceLock.objects.filter(device=dev, lock_type="user", status="active").update(
                status="released", released_at=now, release_reason="manual"
            )
        return {"serial": dev.serial, "locked": locked}

    def claim_wireless_device(self, dev: Device, user_id: str) -> None:
        """局域网主动连接 → 默认锁定给当前用户（PRD §2.5.1 默认可见性）。

        仅 WIFI 且 user_id 非空时生效：未锁定则锁定（复用 set_device_lock 写审计），
        未记录配置者则补记（added_by）。
        """
        if dev.connection_type != "WIFI" or not user_id:
            return
        if not dev.locked_by:
            self.set_device_lock(dev, True, user_id)
        if not dev.added_by:
            dev.added_by = user_id
            dev.save(update_fields=["added_by"])

    def release_internal(
        self, dev: Device, reason: str = "manual", clear_lock: bool = False
    ) -> None:
        """释放占用：清空 occupied_by + 恢复 ONLINE，锁记录标记 released（不删除）。"""
        now = datetime.now()

        DeviceLock.objects.filter(device=dev, status="active").update(
            status="released",
            released_at=now,
            release_reason=reason,
        )

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

        logger.info("设备 %s 已释放占用 (reason=%s)", dev.serial, reason)

    def release_occupy(self, dev: Device) -> dict:
        """释放设备检查器占用；执行引擎占用受保护，不可释放。"""
        occupied_by = dev.occupied_by or ""
        if occupied_by.startswith(RUNNER_OCCUPIED_PREFIXES):
            raise DeviceError("设备正在执行用例，无法解除占用", status_code=409)
        if not occupied_by:
            raise DeviceError("设备未被占用，无需操作", status_code=400)

        self.release_internal(dev, reason="manual")
        return {"serial": dev.serial, "released": True}

    def occupy_observe(self, dev: Device, user_id: str) -> None:
        """观察连接占用：置 BUSY + occupied_by + observe 超时锁（30min 兜底回收）。

        fix-observe-leak：原实现不建锁（无超时回收，关页/崩溃后设备永久 BUSY），
        现建 lock_type="observe" 锁，由 heartbeat_sync 过期回收。
        """
        dev.status = "BUSY"
        dev.occupied_by = user_id or "observe"
        dev.occupied_at = datetime.now()
        dev.save(update_fields=["status", "occupied_by", "occupied_at"])
        DeviceLock.objects.create(
            device=dev,
            user_id=user_id or "observe",
            lock_type="observe",
            timeout_seconds=OBSERVE_LOCK_TTL,
            status="active",
        )

    def release_observe(self, dev: Device) -> None:
        """释放观察占用：仅当占用者为观察连接（非执行引擎）时恢复 ONLINE。"""
        occupied = dev.occupied_by or ""
        if occupied.startswith(RUNNER_OCCUPIED_PREFIXES):
            return
        self.release_internal(dev, reason="disconnect")

    def heartbeat_sync(self) -> dict:
        """心跳同步：状态同步 + 刷新活跃锁心跳 + 回收过期 observe 锁，返回各状态计数。"""
        updated, removed = self.update_device_status()
        DeviceLock.objects.filter(status="active").update(last_heartbeat=timezone.now())

        # fix-observe-leak：过期 observe 锁（关页/崩溃无释放）→ 自动释放占用
        for lock in DeviceLock.objects.filter(lock_type="observe", status="active"):
            if lock.is_expired:
                try:
                    self.release_observe(lock.device)
                except Exception:
                    logger.warning("过期 observe 锁回收失败: device=%s", lock.device_id)

        online = Device.objects.filter(status="ONLINE").count()
        busy = Device.objects.filter(status="BUSY").count()

        return {
            "updated": updated,
            "offline": removed,
            "online": online,
            "busy": busy,
            "offline_count": 0,
            "disconnected": 0,
            "total": online + busy,
        }


class DeviceSerializer:
    """设备展示 — 可见性过滤 + 序列化（只读，独立）。"""

    def resolve_admin_ids(self, admin_users: set[str]) -> set[str]:
        """把管理员白名单归一化为数字用户 ID 集合（纯数字保留，用户名查表转 ID）。"""
        ids = {u for u in admin_users if u.isdigit()}
        names = {u for u in admin_users if not u.isdigit()}
        if names:
            ids.update(
                str(uid)
                for uid in User.objects.filter(username__in=names).values_list("id", flat=True)
            )
        return ids

    def is_device_visible(self, dev: Device, user_id: str, admin_ids: set[str]) -> bool:
        """判断设备对当前用户是否可见（PRD §2.5.1 可见性规则）。

        管理员全局可见；USB 恒公开；WIFI 公开对所有人可见；WIFI 锁定仅锁定者与配置者可见。
        """
        if user_id in admin_ids:
            return True
        if dev.connection_type != "WIFI":
            return True
        if not dev.locked_by:
            return True
        return dev.locked_by == user_id or dev.added_by == user_id

    def usernames_by_ids(self, user_ids: set[str]) -> dict[str, str]:
        """数字用户 ID → 用户名映射（批量查询，供序列化展示用）。"""
        ids = {u for u in user_ids if u and u.isdigit()}
        if not ids:
            return {}
        return {str(u.id): u.username for u in User.objects.filter(id__in=ids)}

    def device_to_dict(
        self, dev: Device, current_serial: str, id_to_name: dict[str, str] | None = None
    ) -> dict:
        """将 Device 转为 PRD §5.2 响应字段。

        Args:
            id_to_name: 数字 ID → 用户名映射；提供时 locked_by/added_by/occupied_by 转为用户名展示。
        """
        name_of = id_to_name or {}
        result = {
            "id": dev.id,
            "serial": dev.serial,
            "name": dev.name,
            "model": dev.model,
            "brand": dev.brand,
            "screen": f"{dev.screen_w}x{dev.screen_h}" if dev.screen_w else "",
            "status": dev.status,
            "connection_type": dev.connection_type or ("WIFI" if ":" in dev.serial else "USB"),
            "connection_addr": dev.connection_addr,
            "locked": bool(dev.locked_by) and dev.connection_type == "WIFI",
            "locked_by": name_of.get(dev.locked_by, dev.locked_by)
            if dev.connection_type == "WIFI"
            else "",
            "locked_at": dev.locked_at.isoformat() if dev.locked_at else None,
            "occupied_by": name_of.get(dev.occupied_by, dev.occupied_by),
            "occupied_at": dev.occupied_at.isoformat() if dev.occupied_at else None,
            "connected_at": dev.connected_at.isoformat() if dev.connected_at else None,
            "added_by": name_of.get(dev.added_by, dev.added_by),
            "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
            "is_current": dev.serial == current_serial,
        }

        if dev.status == "BUSY" and dev.occupied_by:
            active_lock = (
                DeviceLock.objects.filter(device=dev, status="active")
                .order_by("-locked_at")
                .first()
            )
            if active_lock:
                result["remaining"] = active_lock.remaining_seconds
            else:
                result["remaining"] = 0
        else:
            result["remaining"] = 0

        return result


# ── 组合装配（单向依赖，无循环）──
detector = DeviceDetector()
registry = DeviceRegistry(detector)
state_machine = DeviceStateMachine(detector, registry)
serializer = DeviceSerializer()
