"""device_pool 链路测试共用 FakeEngine（全 mock，不真连设备）。

注入方式：monkeypatch `apps.device_pool.session.get_device_engine` 返回本类实例。
"""

import base64
import io

from types import SimpleNamespace

import numpy as np

from PIL import Image

from algorithms.hierarchy import parse_hierarchy_xml
from engines.android.airtest_u2 import EngineConnectError, _to_node

SAMPLE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?><hierarchy>'
    '<node class="android.widget.Button" text="确定" bounds="[1,2][11,22]" clickable="true"/>'
    "</hierarchy>"
)


class FakeEngine:
    """实现 DeviceSession 所依赖的引擎面（感知/操作/生命周期）。"""

    def __init__(self, dump_results=None):
        self._dump_results = list(dump_results or [SAMPLE_XML])
        self.connected: list = []
        self.calls: list = []
        self.connect_error = None
        self.u2 = SimpleNamespace(info={"productName": "Pixel"})
        self.airtest = SimpleNamespace(display_info={"displayWidth": 1080, "displayHeight": 2400})
        self._device_info = {
            "displayWidth": 1080,
            "displayHeight": 2400,
            "productName": "Pixel",
        }
        self.device_info_reads = 0
        self.alive = True

    @property
    def device_info(self):
        self.device_info_reads += 1
        return dict(self._device_info)

    def connect(self, serial, addr=""):
        self.connected.append((serial, addr))
        if self.connect_error:
            raise EngineConnectError(self.connect_error)

    def disconnect(self):
        self.alive = False

    def is_alive(self):
        return self.alive

    def reconnect(self):
        self.alive = True
        return True

    def info(self):
        self.calls.append("info")
        return self.device_info

    def screenshot_b64(self, quality=55, max_width=0):
        self.calls.append(("screenshot_b64", quality, max_width))
        arr = np.full((20, 10, 3), (255, 0, 0), dtype=np.uint8)  # BGR 红
        img = Image.fromarray(arr[..., ::-1])
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, max(1, int(img.height * ratio))))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def screenshot_file(self, path):
        self.calls.append(("screenshot_file", path))
        arr = np.full((20, 10, 3), (255, 0, 0), dtype=np.uint8)
        Image.fromarray(arr[..., ::-1]).save(path)

    def dump_hierarchy(self):
        self.calls.append("dump_hierarchy")
        last = None
        for r in self._dump_results:
            if isinstance(r, BaseException):
                last = r
                continue
            return [_to_node(d) for d in parse_hierarchy_xml(r)]
        if last is not None:
            raise RuntimeError(f"dump_hierarchy all strategies failed: {last}")
        raise RuntimeError("dump_hierarchy: no results configured")

    def app_current(self):
        self.calls.append("app_current")
        return {"package": "com.x", "activity": "Main"}

    def click(self, x, y):
        self.calls.append(("click", x, y))

    def long_click(self, x, y, duration=0.8):
        self.calls.append(("long_click", x, y, duration))

    def swipe(self, x1, y1, x2, y2, duration=0.5):
        self.calls.append(("swipe", x1, y1, x2, y2, duration))

    def input_text(self, text, clear_first=True):
        self.calls.append(("input_text", text, clear_first))

    def press_key(self, key):
        self.calls.append(("press_key", key))

    def shell(self, cmd):
        self.calls.append(("shell", cmd))
        return "out"

    def start_app(self, pkg):
        self.calls.append(("start_app", pkg))

    def stop_app(self, pkg):
        self.calls.append(("stop_app", pkg))

    def exists(self, xpath, timeout=0):
        return True

    def get_text(self, xpath):
        return "确定"

    def wait_toast(self, expected_text, timeout=15):
        return True


def install_fake_engine(monkeypatch, engine=None):
    """把 FakeEngine 注入 session 引擎工厂，返回引擎实例。"""
    engine = engine or FakeEngine()
    import apps.device_pool.session as session_module

    monkeypatch.setattr(session_module, "get_device_engine", lambda *a, **k: engine)
    return engine


def clear_sessions():
    """清理 pool 会话缓存与租用表（测试隔离）。"""
    from apps.device_pool.pool import DevicePool
    from apps.device_pool.session import DeviceSession

    DevicePool._sessions.clear()
    DeviceSession._lease_holders.clear()
