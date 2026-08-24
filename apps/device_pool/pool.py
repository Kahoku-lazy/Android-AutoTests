"""DevicePool — 设备交互中台的协议消费壳（L2 收敛，introduce-device-session）。

设备连接/感知/操作的物理实现已全部下沉 engines/；本类保留设备管理链路的
状态管理（switch_to/_addr/连接类型/清理）并委托 DeviceSession 完成取数与操作。
第三方引擎 import 清零（红线：仅 engines/ 可触碰 u2/Airtest）。
"""

import logging
import threading
import time

from dataclasses import asdict

from .session import DeviceSession, LeaseMode

logger = logging.getLogger(__name__)


class DevicePool:
    """Thread-safe device manager — 状态管理 + DeviceSession 委托。"""

    _connection_types: dict = {}
    _addresses: dict = {}  # serial → 连接地址（无线为 IP:port / mDNS，USB 为空）
    _sessions: dict = {}  # serial → DeviceSession（TRANSIENT，惰性）
    _sessions_lock = threading.Lock()
    current_serial = ""

    # ── 会话获取 ──

    def _session(self) -> DeviceSession:
        """取当前 serial 的会话（惰性租用 TRANSIENT）。"""
        serial = self.current_serial
        if not serial:
            raise RuntimeError("no current device: switch_to(serial) first")
        with DevicePool._sessions_lock:
            session = DevicePool._sessions.get(serial)
            if session is None:
                session = DeviceSession.lease(serial, LeaseMode.TRANSIENT, addr=self._addr(serial))
                DevicePool._sessions[serial] = session
            return session

    # ── Device Accessors（兼容：单步调试 task_views 用 .ad/.u2d）──

    @property
    def u2d(self):
        """u2 原始句柄（XPath + dump），经会话引擎。"""
        return self._session().engine.u2

    @property
    def ad(self):
        """Airtest 原始句柄（操作），经会话引擎。"""
        return self._session().engine.airtest

    @property
    def d(self):
        """Backward-compat: returns u2 device (used by external code for xpath/dump).

        Prefer using .u2d or .ad explicitly in new code.
        """
        return self.u2d

    def switch_to(self, serial: str, connection_type: str | None = None, addr: str | None = None):
        """切换当前设备。addr 为无线设备连接地址（IP:port / mDNS），USB 传空。

        无线设备的 DB 序列号是真实串号，ADB 需要传输地址才能连上，故连接层
        按「地址优先于序列号」解析（见 _addr）。
        """
        self.current_serial = serial
        if connection_type:
            DevicePool._connection_types[serial] = connection_type
        elif serial not in DevicePool._connection_types:
            DevicePool._connection_types[serial] = "WIFI" if ":" in serial else "USB"
        if addr:
            DevicePool._addresses[serial] = addr

    def _addr(self, serial: str) -> str:
        """解析连接地址：无线设备返回连接地址，USB 返回序列号本身。"""
        return DevicePool._addresses.get(serial) or serial

    def get_connection_type(self, serial: str | None = None) -> str:
        """Return the connection type for a device (USB or WIFI)."""
        s = serial or self.current_serial
        return DevicePool._connection_types.get(s, "WIFI" if ":" in s else "USB")

    def remove_device(self, serial: str):
        """Clean up a disconnected device from all caches（含会话释放）。"""
        with DevicePool._sessions_lock:
            session = DevicePool._sessions.pop(serial, None)
        if session is not None:
            session.release()
        DevicePool._connection_types.pop(serial, None)
        DevicePool._addresses.pop(serial, None)
        if self.current_serial == serial:
            self.current_serial = ""

    # ── Info ──

    def info(self) -> dict:
        """Get device display info via engine（cached 2s to avoid redundant calls）。"""
        now = time.monotonic()
        cache = getattr(self, "_info_cache", None)
        if cache and (now - cache["ts"]) < 2.0:
            return cache["data"]
        try:
            result = dict(self._session().info())
            result["connection_type"] = self.get_connection_type()
            self._info_cache = {"ts": now, "data": result}
            return result
        except Exception:
            fallback = {"connection_type": self.get_connection_type()}
            self._info_cache = {"ts": now, "data": fallback}
            return fallback

    # ── Screenshot ──

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        """Capture screen as base64 JPEG (compact for WebSocket streaming)."""
        return self._session().screenshot_b64(quality=quality, max_width=max_width)

    def screenshot_file(self, path: str):
        """Save screenshot directly to file path (replaces device.d.screenshot(path))."""
        self._session().screenshot_file(path)

    # ── UI Hierarchy（会话返回 Node，此处转 dict 兼容 inspector 契约）──

    def dump_hierarchy(self) -> list[dict]:
        """Dump UI hierarchy via session engine（3 层 fallback 在引擎内）。

        Node → dict 兼容转换（丢弃 xpaths 空列表，保持 inspector 既有契约：
        xpaths 由 capture_dump_payload 按需生成）。
        """
        nodes = []
        for n in self._session().dump_hierarchy():
            d = asdict(n)
            d.pop("xpaths", None)
            nodes.append(d)
        return nodes

    # ── App Info ──

    def app_current(self) -> dict:
        """Get current foreground app info."""
        return self._session().app_current()

    # ── Actions（计算坐标 → 会话操作原语）──

    def action_click(self, x: int, y: int):
        self._session().click(x, y)

    def action_longclick(self, x: int, y: int, duration: float = 0.8):
        self._session().long_click(x, y, duration)

    def action_swipe(self, direction: str, distance: int = 500):
        """Swipe screen in direction by distance pixels."""
        info = self.info()
        w = info.get("displayWidth", 0) or 0
        h = info.get("displayHeight", 0) or 0
        cx, cy = w // 2, h // 2
        dirs = {
            "up": (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
            "down": (cx, h // 4, cx, h // 4 + distance),
            "left": (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
            "right": (w // 4, cy, w // 4 + distance, cy),
        }
        x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
        self._session().swipe(x1, y1, x2, y2)

    def action_drag(self, x: int, y: int, direction: str, distance: int = 300):
        """Long-press and drag from (x,y) in direction by distance."""
        dirs = {
            "up": (x, y, x, y - distance),
            "down": (x, y, x, y + distance),
            "left": (x, y, x - distance, y),
            "right": (x, y, x + distance, y),
        }
        x1, y1, x2, y2 = dirs.get(direction, (x, y, x, y - distance))
        self._session().swipe(x1, y1, x2, y2, duration=0.5)

    def action_input(
        self, text: str, x: int | None = None, y: int | None = None, clear_first: bool = True
    ):
        """Input text (clear first optional); optional tap before input."""
        if x is not None and y is not None:
            self._session().click(x, y)
            time.sleep(0.25)
        self._session().input_text(text, clear_first=clear_first)


device = DevicePool()
