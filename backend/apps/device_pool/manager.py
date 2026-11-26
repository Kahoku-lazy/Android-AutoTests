import subprocess
import threading
import time

from datetime import datetime
from typing import Final

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.exceptions import APIException

from engines.device.action import EngineConnectError
from engines.device.connection import fetch_device_info, probe_u2
from utils.adb import AdbUnavailableError, adb_binary
from utils.logs import backend_log

from .contracts import (
    RUNNER_OCCUPIED_PREFIXES,
    ConnectionType,
    DeviceInfo,
    DeviceStatus,
    LockReleaseReason,
    LockStatus,
)
from .models import Device, DeviceLock
from .pool import device as device_pool

OBSERVE_LOCK_TTL = 1800

STATUS_SYNC_TTL_SECONDS: Final[float] = 10.0
_status_sync_lock = threading.Lock()
_status_sync_at = 0.0
_status_sync_result: tuple[int, int] = (0, 0)


def reset_status_sync_cache() -> None:
    global _status_sync_at, _status_sync_result
    with _status_sync_lock:
        _status_sync_at = 0.0
        _status_sync_result = (0, 0)


class DeviceError(APIException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.log = backend_log
        self.status_code = status_code


class DeviceDetector:
    def detect(self) -> list[DeviceInfo]:
        detected: list[DeviceInfo] = []
        for addr in self.connectable_serials():
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
        try:
            result = subprocess.run(
                [adb_binary(), "devices"], capture_output=True, text=True, timeout=5
            )
            serials = set()
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    serials.add(parts[0])
            return serials
        except AdbUnavailableError:
            raise
        except Exception:
            return set()

    def connectable_serials(self, listed: set | None = None) -> set:
        rows = self.adb_device_serials() if listed is None else listed
        return {addr for addr in rows if not str(addr).endswith("_adb-tls-connect._tcp")}

    def is_wireless(self, addr: str) -> bool:
        return ":" in addr or addr.startswith("adb-")

    @staticmethod
    def parse_mdns_serial(addr: str) -> str:
        if not addr.startswith("adb-"):
            return ""
        body = addr[4:]
        serial = body.split("-", 1)[0]
        return serial.strip() if serial else ""

    def is_adb_listed(self, addr: str) -> bool:
        return addr in self.adb_device_serials()

    def wireless_ready_hint(self, ip: str) -> dict:
        listed = self.adb_device_serials()
        ip_addrs = [a for a in listed if a.startswith(f"{ip}:")]
        mdns = [a for a in listed if a.startswith("adb-") and "_adb-tls-connect" in a]
        mdns_serials = [s for a in mdns if (s := self.parse_mdns_serial(a))]
        return {
            "ip_connected": bool(ip_addrs),
            "connection_addrs": ip_addrs,
            "mdns_addrs": mdns,
            "mdns_serials": mdns_serials,
            "can_skip_pair": bool(ip_addrs or mdns),
        }

    def fetch_serial_no(self, addr: str) -> str:
        for attempt in range(3):
            try:
                result = subprocess.run(
                    [adb_binary(), "-s", addr, "shell", "getprop", "ro.serialno"],
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
        try:
            result = subprocess.run(
                [adb_binary(), "-s", addr, "shell", "getprop", prop],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def resolve_serial(self, addr: str) -> tuple[str, str]:
        if self.is_wireless(addr):
            if str(addr).endswith("_adb-tls-connect._tcp"):
                return "", addr
            return self.fetch_serial_no(addr), addr
        return addr, ""

    def get_info(self, addr: str) -> DeviceInfo:
        raw = fetch_device_info(addr)
        return DeviceInfo(
            model=self._getprop(addr, "ro.product.model") or raw.get("productName", "") or "",
            brand=self._getprop(addr, "ro.product.brand") or "",
            screen_w=raw.get("displayWidth", 0) or 0,
            screen_h=raw.get("displayHeight", 0) or 0,
            android_version=str(raw.get("sdkInt", 0)) if raw.get("sdkInt", 0) else "",
        )

    def connect(self, addr: str) -> None:
        try:
            if ":" in addr and not self.is_adb_listed(addr):
                result = subprocess.run(
                    [adb_binary(), "connect", addr],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = (result.stdout or "") + (result.stderr or "")
                lower = output.lower()
                if "connected" not in lower and "already" not in lower:
                    if any(
                        k in lower
                        for k in ("unauthorized", "failed to authenticate", "not authorized")
                    ):
                        raise DeviceError(
                            "设备未配对或授权失效，请填写配对端口和配对码后重试",
                            status_code=400,
                        )
                    raise DeviceError(
                        "连接失败，请确认无线调试已开启；首次连接需填写配对端口和配对码",
                        status_code=504,
                    )
            probe_u2(addr)
        except AdbUnavailableError as e:
            raise DeviceError(str(e), status_code=503) from e
        except subprocess.TimeoutExpired as exc:
            raise DeviceError("连接超时，请检查设备 USB/WiFi 连接", status_code=504) from exc
        except EngineConnectError as e:
            error_msg = str(e)
            if "atx-agent" in error_msg.lower() or "offline" in error_msg.lower():
                raise DeviceError(
                    "设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务", status_code=502
                ) from e
            raise DeviceError("连接超时，请检查设备 USB/WiFi 连接", status_code=504) from e

    def pair(self, ip: str, pair_port: str, pair_code: str) -> None:
        port = (pair_port or "").strip()
        code = (pair_code or "").strip()
        if not port.isdigit() or not (1024 <= int(port) <= 65535):
            raise DeviceError("无效的配对端口", status_code=400)
        if not code.isdigit() or not (4 <= len(code) <= 16):
            raise DeviceError("请输入无线调试显示的配对码", status_code=400)
        addr = f"{ip}:{port}"
        try:
            result = subprocess.run(
                [adb_binary(), "pair", addr, code],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except AdbUnavailableError as e:
            raise DeviceError(str(e), status_code=503) from e
        except subprocess.TimeoutExpired:
            raise DeviceError("配对超时，请确认手机配对页仍打开", status_code=504) from None
        output = ((result.stdout or "") + (result.stderr or "")).lower()
        if "successfully paired" in output or "already paired" in output:
            return
        raise DeviceError("配对失败，请核对配对端口和配对码", status_code=400)


class DeviceRegistry:
    def __init__(self, detector: DeviceDetector):
        self.log = backend_log
        self._detector = detector

    def register_device(self, addr: str, user_id: str = "") -> tuple[Device, bool]:
        serial, conn_addr = self._detector.resolve_serial(addr)
        if not serial:
            raise DeviceError(
                f"无法解析设备 {addr} 的序列号，请确认设备在线后重试", status_code=502
            )
        ct = ConnectionType.WIFI if self._detector.is_wireless(addr) else ConnectionType.USB
        now = datetime.now()
        dev, created = Device.objects.update_or_create(
            serial=serial,
            defaults={
                "status": DeviceStatus.ONLINE,
                "connection_type": ct,
                "connection_addr": conn_addr,
            },
        )
        if serial != addr:
            Device.objects.filter(serial=addr).delete()
        if created:
            dev.connected_at = now
            dev.added_by = user_id
            dev.save(update_fields=["connected_at", "added_by"])
            self.collect_device_info(dev, addr)
        return dev, created

    def collect_device_info(self, dev: Device, addr: str) -> None:
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
            backend_log.warning("采集设备信息失败 %s: %s", addr, e)

    def delete_device_record(self, dev: Device, reason: str = LockReleaseReason.DISCONNECT) -> None:
        DeviceLock.objects.filter(device=dev, status=LockStatus.ACTIVE).update(
            status=LockStatus.RELEASED,
            released_at=datetime.now(),
            release_reason=reason,
        )
        device_pool.remove_device(dev.serial)
        if dev.connection_addr:
            device_pool.remove_device(dev.connection_addr)
        dev.delete()

    def purge_disconnected_devices(self) -> int:
        stale = list(Device.objects.filter(status="DISCONNECTED"))
        for dev in stale:
            self.delete_device_record(dev, reason="purge")
        return len(stale)

    def set_connection_state(self, dev: Device, connection_type: str) -> None:
        dev.connection_type = connection_type
        dev.status = DeviceStatus.ONLINE
        dev.save(update_fields=["connection_type", "status"])

    def touch_last_seen(self, dev: Device) -> None:
        dev.last_seen = datetime.now()
        dev.save(update_fields=["last_seen"])


class DeviceStateMachine:
    def __init__(self, detector: DeviceDetector, registry: DeviceRegistry):
        self.log = backend_log
        self._detector = detector
        self._registry = registry

    def judge_status(self, dev: Device) -> DeviceStatus:
        if dev.status == DeviceStatus.BUSY:
            active_lock = (
                DeviceLock.objects.filter(device=dev, lock_type="process", status=LockStatus.ACTIVE)
                .order_by("-locked_at")
                .first()
            )
            if active_lock and not active_lock.is_expired:
                return DeviceStatus.BUSY
            return DeviceStatus.ONLINE
        return DeviceStatus.ONLINE

    def update_device_status(self) -> tuple[int, int]:
        global _status_sync_at, _status_sync_result
        now = time.monotonic()
        if now - _status_sync_at < STATUS_SYNC_TTL_SECONDS:
            return _status_sync_result
        with _status_sync_lock:
            now = time.monotonic()
            if now - _status_sync_at < STATUS_SYNC_TTL_SECONDS:
                return _status_sync_result
            result = self._sync_device_status()
            _status_sync_at = now
            _status_sync_result = result
            return result

    def _sync_device_status(self) -> tuple[int, int]:
        self._registry.purge_disconnected_devices()
        now = datetime.now()
        adb_serials = self._detector.connectable_serials()
        updated = 0
        removed = 0

        for addr in adb_serials:
            serial, conn_addr = self._detector.resolve_serial(addr)
            if not serial:
                Device.objects.filter(serial=addr).delete()
                continue
            dev, created = Device.objects.get_or_create(
                serial=serial,
                defaults={
                    "status": DeviceStatus.ONLINE,
                    "connection_type": ConnectionType.WIFI
                    if self._detector.is_wireless(addr)
                    else ConnectionType.USB,
                    "connection_addr": conn_addr,
                },
            )
            if dev.connected_at is None:
                dev.connected_at = now if created else (dev.created_at or now)
                dev.save(update_fields=["connected_at"])
            if created or not dev.model or not dev.screen_w:
                self._registry.collect_device_info(dev, addr)
            if serial != addr:
                Device.objects.filter(serial=addr).delete()

        for dev in list(Device.objects.all()):
            visible = dev.serial in adb_serials or (
                dev.connection_addr and dev.connection_addr in adb_serials
            )
            if visible:
                if dev.connection_type != ConnectionType.WIFI and (dev.locked_by or dev.locked_at):
                    dev.locked_by = ""
                    dev.locked_at = None
                    dev.save(update_fields=["locked_by", "locked_at"])
                if dev.status == DeviceStatus.BUSY:
                    active_lock = (
                        DeviceLock.objects.filter(
                            device=dev, lock_type="process", status=LockStatus.ACTIVE
                        )
                        .order_by("-locked_at")
                        .first()
                    )
                    if active_lock and active_lock.is_expired:
                        self.release_internal(dev, reason=LockReleaseReason.TIMEOUT)
                        updated += 1
                    elif active_lock:
                        dev.last_seen = now
                        dev.save(update_fields=["last_seen"])
            else:
                if dev.status == DeviceStatus.BUSY:
                    active_lock = (
                        DeviceLock.objects.filter(
                            device=dev, lock_type="process", status=LockStatus.ACTIVE
                        )
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
        if dev.connection_type != ConnectionType.WIFI:
            raise DeviceError("USB 设备不支持锁定", status_code=400)

        now = datetime.now()
        if locked:
            if dev.locked_by and dev.locked_by != user_id:
                raise DeviceError(f"设备已被 {dev.locked_by} 锁定", status_code=409)
            dev.locked_by = user_id
            dev.locked_at = now
            dev.save(update_fields=["locked_by", "locked_at"])
            DeviceLock.objects.create(
                device=dev, user_id=user_id, lock_type="user", status=LockStatus.ACTIVE
            )
        else:
            dev.locked_by = ""
            dev.locked_at = None
            dev.save(update_fields=["locked_by", "locked_at"])
            DeviceLock.objects.filter(
                device=dev, lock_type="user", status=LockStatus.ACTIVE
            ).update(
                status=LockStatus.RELEASED, released_at=now, release_reason=LockReleaseReason.MANUAL
            )
        return {"serial": dev.serial, "locked": locked}

    def claim_wireless_device(self, dev: Device, user_id: str) -> None:
        if dev.connection_type != ConnectionType.WIFI or not user_id:
            return
        if not dev.locked_by:
            self.set_device_lock(dev, True, user_id)
        if not dev.added_by:
            dev.added_by = user_id
            dev.save(update_fields=["added_by"])

    def release_internal(
        self, dev: Device, reason: str = LockReleaseReason.MANUAL, clear_lock: bool = False
    ) -> None:
        now = datetime.now()

        DeviceLock.objects.filter(device=dev, status=LockStatus.ACTIVE).update(
            status=LockStatus.RELEASED,
            released_at=now,
            release_reason=reason,
        )

        dev.occupied_by = ""
        dev.occupied_at = None
        update_fields = ["occupied_by", "occupied_at"]
        if dev.status == DeviceStatus.BUSY:
            dev.status = DeviceStatus.ONLINE
            update_fields.append("status")
        if clear_lock:
            dev.locked_by = ""
            dev.locked_at = None
            update_fields.extend(["locked_by", "locked_at"])
        dev.save(update_fields=update_fields)

        backend_log.info("设备 %s 已释放占用 (reason=%s)", dev.serial, reason)

    def release_occupy(self, dev: Device) -> dict:
        occupied_by = dev.occupied_by or ""
        if occupied_by.startswith(RUNNER_OCCUPIED_PREFIXES):
            raise DeviceError("设备正在执行用例，无法解除占用", status_code=409)
        if not occupied_by:
            raise DeviceError("设备未被占用，无需操作", status_code=400)

        self.release_internal(dev, reason=LockReleaseReason.MANUAL)
        return {"serial": dev.serial, "released": True}

    def occupy_observe(self, dev: Device, user_id: str) -> None:
        dev.status = DeviceStatus.BUSY
        dev.occupied_by = user_id or "observe"
        dev.occupied_at = datetime.now()
        dev.save(update_fields=["status", "occupied_by", "occupied_at"])
        DeviceLock.objects.create(
            device=dev,
            user_id=user_id or "observe",
            lock_type="observe",
            timeout_seconds=OBSERVE_LOCK_TTL,
            status=LockStatus.ACTIVE,
        )

    def release_observe(self, dev: Device) -> None:
        occupied = dev.occupied_by or ""
        if occupied.startswith(RUNNER_OCCUPIED_PREFIXES):
            return
        self.release_internal(dev, reason=LockReleaseReason.DISCONNECT)

    def heartbeat_sync(self) -> dict:
        updated, removed = self.update_device_status()
        DeviceLock.objects.filter(status=LockStatus.ACTIVE).update(last_heartbeat=timezone.now())

        for lock in DeviceLock.objects.filter(lock_type="observe", status=LockStatus.ACTIVE):
            if lock.is_expired:
                try:
                    self.release_observe(lock.device)
                except Exception:
                    backend_log.warning("过期 observe 锁回收失败: device=%s", lock.device_id)

        online = Device.objects.filter(status=DeviceStatus.ONLINE).count()
        busy = Device.objects.filter(status=DeviceStatus.BUSY).count()

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
    def resolve_admin_ids(self, admin_users: set[str]) -> set[str]:
        ids = {u for u in admin_users if u.isdigit()}
        names = {u for u in admin_users if not u.isdigit()}
        if names:
            ids.update(
                str(uid)
                for uid in User.objects.filter(username__in=names).values_list("id", flat=True)
            )
        return ids

    def is_device_visible(self, dev: Device, user_id: str, admin_ids: set[str]) -> bool:
        if user_id in admin_ids:
            return True
        if dev.connection_type != ConnectionType.WIFI:
            return True
        if not dev.locked_by:
            return True
        return dev.locked_by == user_id or dev.added_by == user_id

    def usernames_by_ids(self, user_ids: set[str]) -> dict[str, str]:
        ids = {u for u in user_ids if u and u.isdigit()}
        if not ids:
            return {}
        return {str(u.id): u.username for u in User.objects.filter(id__in=ids)}

    def device_to_dict(
        self, dev: Device, current_serial: str, id_to_name: dict[str, str] | None = None
    ) -> dict:
        name_of = id_to_name or {}
        result = {
            "id": dev.id,
            "serial": dev.serial,
            "name": dev.name,
            "model": dev.model,
            "brand": dev.brand,
            "screen": f"{dev.screen_w}x{dev.screen_h}" if dev.screen_w else "",
            "status": dev.status,
            "connection_type": dev.connection_type
            or (ConnectionType.WIFI if ":" in dev.serial else ConnectionType.USB),
            "connection_addr": dev.connection_addr,
            "locked": bool(dev.locked_by) and dev.connection_type == ConnectionType.WIFI,
            "locked_by": name_of.get(dev.locked_by, dev.locked_by)
            if dev.connection_type == ConnectionType.WIFI
            else "",
            "locked_at": dev.locked_at.isoformat() if dev.locked_at else None,
            "occupied_by": name_of.get(dev.occupied_by, dev.occupied_by),
            "occupied_at": dev.occupied_at.isoformat() if dev.occupied_at else None,
            "connected_at": dev.connected_at.isoformat() if dev.connected_at else None,
            "added_by": name_of.get(dev.added_by, dev.added_by),
            "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
            "is_current": dev.serial == current_serial,
        }

        if dev.status == DeviceStatus.BUSY and dev.occupied_by:
            active_lock = (
                DeviceLock.objects.filter(device=dev, status=LockStatus.ACTIVE)
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


detector = DeviceDetector()
registry = DeviceRegistry(detector)
state_machine = DeviceStateMachine(detector, registry)
serializer = DeviceSerializer()
