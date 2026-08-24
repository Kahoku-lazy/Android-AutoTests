"""L2 设备交互中台 — DeviceSession 租用式会话协议（L2 详档 §2.3 权威实现）。

协议层职责：租用编排、per-serial 操作锁、引擎工厂消费、错误语义转换。
数据主权：无自有表；租用状态仅存进程内；业务锁表 dp_ 归本 App api/service。

依赖方向：L3 业务 App → 本协议 → engines/（get_device_engine）。
"""

import threading

from enum import Enum

from django.conf import settings

from engines.android.airtest_u2 import EngineConnectError
from engines.registry import DEFAULT_ENGINE, get_device_engine


class LeaseMode(str, Enum):
    TRANSIENT = "transient"  # 检查器短租
    EXCLUSIVE = "exclusive"  # 执行器独占


class LeaseError(RuntimeError):
    """租用/连接业务语义错误（上层转 4xx 用户文案）。"""


class LeaseConflict(RuntimeError):
    """同 serial 租用冲突（上层转 409「设备正被占用」）。"""


_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _per_serial_lock(serial: str) -> threading.Lock:
    """进程级 per-serial 锁：同 serial 操作串行，跨 serial 并行。"""
    with _locks_guard:
        return _locks.setdefault(serial, threading.Lock())


class DeviceSession:
    """租用式会话——同一 serial 同一时刻至多一个持有者。"""

    _lease_holders: dict[str, "DeviceSession"] = {}
    _lease_guard = threading.Lock()

    def __init__(
        self, serial: str, addr: str = "", engine=None, mode: LeaseMode = LeaseMode.TRANSIENT
    ):
        self.serial = serial
        self.addr = addr
        self.mode = mode
        self._engine = engine or get_device_engine(
            getattr(settings, "DEVICE_ENGINE", DEFAULT_ENGINE)
        )
        self._connected = False
        self._leased = False

    # ── 租用生命周期 ──

    @classmethod
    def lease(
        cls,
        serial: str,
        mode: LeaseMode,
        addr: str = "",
        engine=None,
    ) -> "DeviceSession":
        """租用会话。前置：EXCLUSIVE 需已持业务锁（acquire_device 已建 process 锁）。"""
        mode = LeaseMode(mode)
        with cls._lease_guard:
            holder = cls._lease_holders.get(serial)
            if holder is not None:
                raise LeaseConflict(f"设备 {serial} 已被租用（{holder.mode.value}）")
            if mode is LeaseMode.EXCLUSIVE:
                from .models import DeviceLock

                has_lock = DeviceLock.objects.filter(
                    device__serial=serial, lock_type="process", status="active"
                ).exists()
                if not has_lock:
                    raise LeaseConflict(
                        f"设备 {serial} 未持有业务锁（EXCLUSIVE 租用需先 acquire_device）"
                    )
            session = cls(serial, addr, engine=engine, mode=mode)
            session._leased = True
            cls._lease_holders[serial] = session
            return session

    def release(self) -> None:
        """归还会话；空闲连接回收策略由引擎决定（协议层不强制断开）。"""
        with self._lease_guard:
            if self._lease_holders.get(self.serial) is self:
                self._lease_holders.pop(self.serial, None)
        self._leased = False

    # ── 内部 ──

    def _ensure_connected(self) -> None:
        """惰性连接（保持 pool 既有语义）：首次操作才建立双栈连接，幂等。"""
        if self._connected:
            return
        try:
            self._engine.connect(self.serial, self.addr)
            self._connected = True
        except EngineConnectError as e:
            raise LeaseError(f"设备连接失败: {e}") from e

    @property
    def engine(self):
        """引擎原始句柄（过渡期：pool.u2d/ad 兼容、单步调试）。"""
        self._ensure_connected()
        return self._engine

    # ── 感知（返回标准化数据；dump 为 Node 列表）──

    def info(self) -> dict:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.device_info

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.screenshot_b64(quality=quality, max_width=max_width)

    def screenshot_file(self, path: str) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.screenshot_file(path)

    def dump_hierarchy(self) -> list:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.dump_hierarchy()

    def app_current(self) -> dict:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.app_current()

    # ── 操作（UI 操作原语）──

    def click(self, x: int, y: int) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.click(x, y)

    def long_click(self, x: int, y: int, duration: float = 0.8) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.long_click(x, y, duration)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.swipe(x1, y1, x2, y2, duration)

    def input_text(self, text: str, clear_first: bool = True) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.input_text(text, clear_first=clear_first)

    def press_key(self, key: str) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.press_key(key)

    def shell(self, cmd: str) -> str:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.shell(cmd)

    def start_app(self, pkg: str) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.start_app(pkg)

    def stop_app(self, pkg: str) -> None:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            self._engine.stop_app(pkg)

    # ── 查询 / 生命周期 ──

    def is_alive(self) -> bool:
        if not self._connected:
            return False
        return self._engine.is_alive()

    def reconnect(self) -> bool:
        with _per_serial_lock(self.serial):
            try:
                ok = self._engine.reconnect()
                self._connected = ok
                return ok
            except EngineConnectError as e:
                raise LeaseError(f"设备重连失败: {e}") from e

    def wait_toast(self, expected_text: str, timeout: float = 15) -> bool:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.wait_toast(expected_text, timeout)

    def exists(self, xpath: str, timeout: float = 0) -> bool:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.exists(xpath, timeout)

    def get_text(self, xpath: str) -> str:
        with _per_serial_lock(self.serial):
            self._ensure_connected()
            return self._engine.get_text(xpath)
