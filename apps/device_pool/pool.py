"""DevicePool — thread-safe Airtest + uiautomator2 device manager singleton.

Airtest (airtest.core.android.Android) handles all low-level device operations:
screenshot, click, swipe, app lifecycle, shell, text input.

uiautomator2 (u2.Device) is kept ONLY for dump_hierarchy() and XPath queries.
"""

import base64
import io
import logging
import threading
import time

import uiautomator2 as u2

from airtest.core.android.android import Android
from PIL import Image

logger = logging.getLogger(__name__)


class DevicePool:
    """Thread-safe singleton managing dual device connections.

    Airtest Android for device operations, uiautomator2 for UI hierarchy/XPath.
    """

    _u2_instances: dict = {}  # serial → u2.Device (XPath + hierarchy only)
    _airtest_instances: dict = {}  # serial → airtest Android (everything else)
    _lock = threading.Lock()
    _op_lock = threading.Lock()  # serializes all device operations (was _u2_lock)
    _connection_types: dict = {}
    current_serial = ""

    # ── Device Accessors ──

    @property
    def u2d(self) -> u2.Device:
        """Thin u2 connection for dump_hierarchy() and xpath operations only."""
        serial = self.current_serial
        if serial not in DevicePool._u2_instances:
            with DevicePool._lock:
                if serial not in DevicePool._u2_instances:
                    DevicePool._u2_instances[serial] = u2.connect(serial)
        return DevicePool._u2_instances[serial]

    @property
    def ad(self):
        """Airtest Android device for screenshots, actions, shell commands."""
        serial = self.current_serial
        if serial not in DevicePool._airtest_instances:
            with DevicePool._lock:
                if serial not in DevicePool._airtest_instances:
                    DevicePool._airtest_instances[serial] = Android(serialno=serial)
        return DevicePool._airtest_instances[serial]

    @property
    def d(self):
        """Backward-compat: returns u2 device (used by external code for xpath/dump).

        Prefer using .u2d or .ad explicitly in new code.
        """
        return self.u2d

    def switch_to(self, serial: str, connection_type: str = None):
        self.current_serial = serial
        if connection_type:
            DevicePool._connection_types[serial] = connection_type
        elif serial not in DevicePool._connection_types:
            DevicePool._connection_types[serial] = "WIFI" if ":" in serial else "USB"

    def get_connection_type(self, serial: str = None) -> str:
        """Return the connection type for a device (USB or WIFI)."""
        s = serial or self.current_serial
        return DevicePool._connection_types.get(s, "WIFI" if ":" in s else "USB")

    def remove_device(self, serial: str):
        """Clean up a disconnected device from all caches."""
        DevicePool._u2_instances.pop(serial, None)
        DevicePool._airtest_instances.pop(serial, None)
        DevicePool._connection_types.pop(serial, None)
        if self.current_serial == serial:
            self.current_serial = ""

    # ── Info ──

    def info(self) -> dict:
        """Get device display info via Airtest (cached 2s to avoid redundant ADB calls)."""
        now = time.monotonic()
        cache = getattr(self, "_info_cache", None)
        if cache and (now - cache["ts"]) < 2.0:
            return cache["data"]
        with DevicePool._op_lock:
            try:
                result = dict(self.ad.display_info)
                result["connection_type"] = self.get_connection_type()
                self._info_cache = {"ts": now, "data": result}
                return result
            except Exception:
                fallback = {"connection_type": self.get_connection_type()}
                self._info_cache = {"ts": now, "data": fallback}
                return fallback

    # ── Screenshot ──

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        """Capture screen as base64 JPEG (compact for WebSocket streaming).

        Airtest snapshot() returns a BGR numpy array; convert to PIL Image.
        """
        with DevicePool._op_lock:
            arr = self.ad.snapshot(quality=quality)
            # Airtest returns BGR numpy array → convert to RGB PIL Image
            img = Image.fromarray(arr[..., ::-1])
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_h = max(1, int(img.height * ratio))
                img = img.resize((max_width, new_h))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            return base64.b64encode(buf.getvalue()).decode("ascii")

    def screenshot_file(self, path: str):
        """Save screenshot directly to file path (replaces device.d.screenshot(path))."""
        arr = self.ad.snapshot()
        Image.fromarray(arr[..., ::-1]).save(path)

    # ── UI Hierarchy (KEEP u2 — no Airtest equivalent) ──

    def dump_hierarchy(self) -> list[dict]:
        """Dump UI hierarchy via uiautomator2 XML dump + XPath generation.

        Uses 3-layer fallback: default → compressed=False → pretty=True.
        Detects XML truncation and attempts repair.
        """
        import xml.etree.ElementTree as ET

        raw = None
        last_error = None

        try:
            raw = self.u2d.dump_hierarchy()
        except Exception as e:
            last_error = e

        if raw is None:
            try:
                raw = self.u2d.dump_hierarchy(compressed=False)
            except Exception as e:
                last_error = last_error or e

        if raw is None:
            try:
                raw = self.u2d.dump_hierarchy(compressed=False, pretty=True)
            except Exception as e:
                last_error = last_error or e

        if raw is None:
            raise RuntimeError(f"dump_hierarchy all strategies failed: {last_error}")

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        raw_len = len(raw)
        logger.debug("[dump] XML length: %s chars", raw_len)

        if not raw.lstrip().startswith("<?"):
            raw = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw

        stripped = raw.rstrip()
        if not stripped.endswith(">") or stripped.endswith("/>"):
            logger.warning("[dump] XML may be truncated, last 100 chars: ...%s", stripped[-100:])

        try:
            root = ET.fromstring(raw.encode("utf-8") if isinstance(raw, str) else raw)
        except ET.ParseError as pe:
            logger.warning("[dump] XML parse failed: %s, trying truncation repair...", pe)
            last_complete = raw.rfind(">")
            if last_complete > 0:
                fixed = raw[: last_complete + 1]
                try:
                    root = ET.fromstring(fixed.encode("utf-8"))
                    logger.info("[dump] Repair succeeded, truncated %s chars", raw_len - len(fixed))
                except ET.ParseError:
                    raise RuntimeError(f"XML parse failed and cannot repair: {pe}")
            else:
                raise RuntimeError(f"XML parse failed: {pe}")

        nodes = []

        def walk(el, depth=0):
            bounds_str = el.attrib.get("bounds", "[0,0][0,0]")
            parts = bounds_str.replace("][", ",").strip("[]").split(",")
            try:
                l, t, r, b = map(int, parts)
            except Exception:
                l, t, r, b = 0, 0, 0, 0

            nodes.append(
                {
                    "depth": depth,
                    "class_name": el.attrib.get("class", ""),
                    "text": el.attrib.get("text", ""),
                    "content_desc": el.attrib.get("content-desc", ""),
                    "resource_id": el.attrib.get("resource-id", ""),
                    "package": el.attrib.get("package", ""),
                    "index": el.attrib.get("index", ""),
                    "bounds": f"[{l},{t}][{r},{b}]",
                    "x": l,
                    "y": t,
                    "width": r - l,
                    "height": b - t,
                    "clickable": el.attrib.get("clickable", "false") == "true",
                    "enabled": el.attrib.get("enabled", "false") == "true",
                    "scrollable": el.attrib.get("scrollable", "false") == "true",
                    "checkable": el.attrib.get("checkable", "false") == "true",
                    "checked": el.attrib.get("checked", "false") == "true",
                    "focusable": el.attrib.get("focusable", "false") == "true",
                    "long_clickable": el.attrib.get("long-clickable", "false") == "true",
                }
            )
            for child in el:
                walk(child, depth + 1)

        walk(root)
        return nodes

    # ── App Info (u2 — no Airtest equivalent) ──

    def app_current(self) -> dict:
        """Get current foreground app info (uses u2 — no Airtest equivalent)."""
        return self.u2d.app_current()

    # ── Actions (migrated to Airtest) ──

    def action_click(self, x: int, y: int):
        self.ad.touch((x, y))

    def action_longclick(self, x: int, y: int, duration: float = 0.8):
        self.ad.touch((x, y), duration=duration)

    def action_swipe(self, direction: str, distance: int = 500):
        """Swipe screen in direction by distance pixels."""
        w, h = self.ad.get_current_resolution()
        cx, cy = w // 2, h // 2
        dirs = {
            "up": (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
            "down": (cx, h // 4, cx, h // 4 + distance),
            "left": (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
            "right": (w // 4, cy, w // 4 + distance, cy),
        }
        x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
        self.ad.swipe((x1, y1), (x2, y2))

    def action_drag(self, x: int, y: int, direction: str, distance: int = 300):
        """Long-press and drag from (x,y) in direction by distance."""
        dirs = {
            "up": (x, y, x, y - distance),
            "down": (x, y, x, y + distance),
            "left": (x, y, x - distance, y),
            "right": (x, y, x + distance, y),
        }
        x1, y1, x2, y2 = dirs.get(direction, (x, y, x, y - distance))
        self.ad.swipe((x1, y1), (x2, y2), duration=0.5)

    def action_input(self, text: str, x: int = None, y: int = None, clear_first: bool = True):
        """Input text using Yosemite IME (Airtest built-in), with ADB shell fallback."""
        if x is not None and y is not None:
            self.ad.touch((x, y))
            time.sleep(0.25)
        if clear_first:
            try:
                self.ad.shell("input keyevent KEYCODE_MOVE_END")
                self.ad.shell("input keyevent KEYCODE_CLEAR")
                time.sleep(0.1)
            except Exception:
                logger.debug("Shell keyevent failed, continuing")
        try:
            # Use Yosemite IME for reliable text input (Airtest built-in)
            self.ad.text(text)
        except Exception:
            # Fallback: ADB shell input text
            safe = text.replace(" ", "%s").replace("'", "\\'")
            self.ad.shell(f"input text '{safe}'")


device = DevicePool()
