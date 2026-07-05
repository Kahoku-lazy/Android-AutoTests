"""DevicePool — thread-safe uiautomator2 device manager singleton."""

import io
import time
import base64
import threading
import uiautomator2 as u2
from django.conf import settings


class DevicePool:
    """Thread-safe singleton managing uiautomator2 device connections.

    Supports multi-device switching, screenshot capture,
    UI hierarchy dump with XML truncation repair, and click/input actions.
    """

    _instances: dict = {}
    _lock = threading.Lock()
    _u2_lock = threading.Lock()
    _connection_types: dict = {}
    current_serial = ""

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
        DevicePool._instances.pop(serial, None)
        DevicePool._connection_types.pop(serial, None)
        if self.current_serial == serial:
            self.current_serial = ""  # fallback default — set via env DEVICE_SERIAL

    @property
    def d(self) -> u2.Device:
        serial = self.current_serial
        if serial not in DevicePool._instances:
            with DevicePool._lock:
                if serial not in DevicePool._instances:
                    DevicePool._instances[serial] = u2.connect(serial)
        return DevicePool._instances[serial]

    def info(self) -> dict:
        with DevicePool._u2_lock:
            try:
                result = dict(self.d.info)
                result["connection_type"] = self.get_connection_type()
                return result
            except Exception:
                return {"connection_type": self.get_connection_type()}

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        """Capture screen as base64 JPEG (compact for WebSocket streaming)."""
        with DevicePool._u2_lock:
            img = self.d.screenshot().convert("RGB")
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_h = max(1, int(img.height * ratio))
                img = img.resize((max_width, new_h))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            return base64.b64encode(buf.getvalue()).decode("ascii")

    def dump_hierarchy(self) -> list[dict]:
        import xml.etree.ElementTree as ET

        raw = None
        last_error = None

        try:
            raw = self.d.dump_hierarchy()
        except Exception as e:
            last_error = e

        if raw is None:
            try:
                raw = self.d.dump_hierarchy(compressed=False)
            except Exception as e:
                last_error = last_error or e

        if raw is None:
            try:
                raw = self.d.dump_hierarchy(compressed=False, pretty=True)
            except Exception as e:
                last_error = last_error or e

        if raw is None:
            raise RuntimeError(f"dump_hierarchy all strategies failed: {last_error}")

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        raw_len = len(raw)
        print(f"[dump] XML length: {raw_len} chars")

        if not raw.lstrip().startswith("<?"):
            raw = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw

        stripped = raw.rstrip()
        if not stripped.endswith(">") or stripped.endswith("/>"):
            print(f"[dump] ⚠ XML may be truncated, last 100 chars: ...{stripped[-100:]}")

        try:
            root = ET.fromstring(raw.encode("utf-8") if isinstance(raw, str) else raw)
        except ET.ParseError as pe:
            print(f"[dump] XML parse failed: {pe}, trying truncation repair...")
            last_complete = raw.rfind(">")
            if last_complete > 0:
                fixed = raw[: last_complete + 1]
                try:
                    root = ET.fromstring(fixed.encode("utf-8"))
                    print(f"[dump] Repair succeeded, truncated {raw_len - len(fixed)} chars")
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

    def action_click(self, x: int, y: int):
        self.d.click(x, y)

    def action_longclick(self, x: int, y: int, duration: float = 0.8):
        self.d.long_click(x, y, duration=duration)

    def action_swipe(self, direction: str, distance: int = 500):
        """Swipe screen in direction by distance pixels."""
        w, h = self.d.window_size()
        cx, cy = w // 2, h // 2
        dirs = {
            "up": (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
            "down": (cx, h // 4, cx, h // 4 + distance),
            "left": (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
            "right": (w // 4, cy, w // 4 + distance, cy),
        }
        x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
        self.d.swipe(x1, y1, x2, y2)

    def action_drag(self, x: int, y: int, direction: str, distance: int = 300):
        """Long-press and drag from (x,y) in direction by distance."""
        dirs = {
            "up": (x, y, x, y - distance),
            "down": (x, y, x, y + distance),
            "left": (x, y, x - distance, y),
            "right": (x, y, x + distance, y),
        }
        x1, y1, x2, y2 = dirs.get(direction, (x, y, x, y - distance))
        self.d.swipe(x1, y1, x2, y2, duration=0.5)

    def action_input(self, text: str, x: int = None, y: int = None, clear_first: bool = True):
        if x is not None and y is not None:
            self.d.click(x, y)
            time.sleep(0.25)
        if clear_first:
            try:
                self.d.clear_text()
                time.sleep(0.1)
            except Exception:
                pass
        try:
            old_ime = self.d.shell("settings get secure default_input_method").output.strip()
            self.d.set_fastinput_ime(True)
            self.d.send_keys(text)
            self.d.shell(f"settings put secure default_input_method {old_ime}")
        except Exception:
            safe = text.replace(" ", "%s").replace("'", "\\'")
            self.d.shell(f"input text '{safe}'")


device = DevicePool()
