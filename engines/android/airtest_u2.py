"""AirtestU2Engine — 组合双栈引擎（L1c 实现，契约见 engines/base.py）。

Airtest（airtest.core.android.Android）负责操作：screenshot/click/swipe/app 生命周期/shell/文本输入。
uiautomator2（u2.Device）只负责 dump_hierarchy 与 XPath 查询。
能力声明：xpath_locate=True / toast_wait=True / ocr=False。

错误语义：连接类失败抛 EngineConnectError（技术语义，由上层转业务文案）。

⚠️ 契约出入（consolidate-airtest-u2-engine 登记）：本模块 import `algorithms.hierarchy`
（纯解析函数，零 apps 依赖），总纲 §三 字面禁令为"engines ❌ algorithms.*"——
此处按"纯函数复用优于内联"执行，Step 4 评审一并裁决。
"""

import base64
import io
import logging
import subprocess
import time

import uiautomator2 as u2

from airtest.core.android.android import Android
from PIL import Image

from algorithms.hierarchy import parse_hierarchy_xml
from engines.base import EngineCapabilities
from models.ui_nodes import Node

logger = logging.getLogger(__name__)

# u2 单操作 HTTP 超时上限（秒）。u2 默认 HTTP_TIMEOUT=300，设备冻结会永久阻塞。
U2_OP_TIMEOUT = 20

_CONNECTED_KEYWORDS = ("connected", "already", "已连接", "已经连接", "成功")


class EngineConnectError(RuntimeError):
    """引擎连接失败（技术语义）。"""


def _to_node(d: dict) -> Node:
    """algorithms.hierarchy 的 dict 节点 → models.ui_nodes.Node。"""
    return Node(
        depth=d["depth"],
        class_name=d["class_name"],
        text=d["text"],
        content_desc=d["content_desc"],
        resource_id=d["resource_id"],
        package=d["package"],
        index=d["index"],
        bounds=d["bounds"],
        x=d["x"],
        y=d["y"],
        width=d["width"],
        height=d["height"],
        clickable=d["clickable"],
        enabled=d["enabled"],
        scrollable=d["scrollable"],
        checkable=d["checkable"],
        checked=d["checked"],
        focusable=d["focusable"],
        long_clickable=d["long_clickable"],
    )


class AirtestU2Engine:
    """组合双栈引擎 — 实现 engines/base.py::UiEngine 协议。"""

    capabilities = EngineCapabilities(xpath_locate=True, toast_wait=True, ocr=False)

    def __init__(self):
        self._airtest = None
        self._u2 = None
        self._serial = ""
        self._addr = ""
        self._info: dict = {}

    # ── 原始句柄（过渡期：DeviceConnection 兼容壳与 pool 属性经此取值）──

    @property
    def airtest(self):
        return self._airtest

    @property
    def u2(self):
        return self._u2

    @property
    def device_info(self) -> dict:
        return dict(self._info)

    # ── 连接生命周期 ──

    def _adb_connect(self, target: str, log=None):
        """无线设备 adb connect（关键词判定）；USB 跳过。失败抛 EngineConnectError。"""
        if log:
            log(f"  ② Wireless ADB: adb connect {target}")
        try:
            result = subprocess.run(
                ["adb", "connect", target], capture_output=True, text=True, timeout=10
            )
            output = (result.stdout + result.stderr).strip()
            if output and log:
                log(f"  → {output}")
            output_lower = output.lower()
            if not any(kw in output_lower for kw in _CONNECTED_KEYWORDS):
                raise EngineConnectError("ADB connect failed. Check WiFi network and device port.")
        except subprocess.TimeoutExpired:
            raise EngineConnectError("ADB connect timed out (10s). Check network.") from None
        if log:
            log("  ✓ ADB ready")

    def _connect_u2(self, target: str):
        try:
            return u2.connect(target)
        except Exception as e:
            raise EngineConnectError(f"u2.connect failed: {e}") from e

    def _tune_u2_http_timeout(self) -> None:
        """降低 u2 HTTP 超时，防止设备冻结时永久阻塞。"""
        try:
            import uiautomator2.base as _u2base

            _u2base.HTTP_TIMEOUT = U2_OP_TIMEOUT
        except Exception:
            logger.debug("u2 HTTP timeout tuning failed, continuing")
        try:
            self._u2.settings["wait_timeout"] = U2_OP_TIMEOUT
        except Exception:
            logger.debug("u2 HTTP timeout tuning failed, continuing")

    def _verify_display(self, log=None) -> dict:
        """经 Airtest display_info 验证连接，失败抛 EngineConnectError（ATX 消息映射）。"""
        try:
            info = dict(self._airtest.display_info)
        except Exception as e:
            msg = str(e)
            if "atx-agent" in msg.lower() or "offline" in msg.lower():
                raise EngineConnectError(
                    "ATX Agent not running. Start uiautomator2 service on device."
                ) from e
            raise EngineConnectError(f"Device verification failed: {e}") from e
        try:
            u2_info = self._u2.info
            for k in ("productName", "brand", "sdkInt", "displayWidth", "displayHeight"):
                if k not in info and k in u2_info:
                    info[k] = u2_info[k]
        except Exception:
            logger.debug("Failed to read extra device info via u2")
        if log:
            w = info.get("displayWidth", "?")
            h = info.get("displayHeight", "?")
            extra = f" · {info.get('productName', '')}" if info.get("productName") else ""
            log(f"  ✓ Connection verified · {w}x{h}{extra}")
        return info

    def connect(self, serial: str, addr: str = "", on_log=None):
        """建立双栈连接并验证。target = addr（无线连接地址）或 serial（USB）。

        on_log: 可选进度回调（仅字符串收集，不阻塞事件循环）。
        """

        def log(msg: str):
            if on_log:
                on_log(msg)

        target = addr or serial
        if ":" in target:
            self._adb_connect(target, log)
        else:
            log("  ② USB device, skip adb connect")
        log("  ③ Establish Airtest connection…")
        try:
            self._airtest = Android(serialno=target)
        except Exception as e:
            raise EngineConnectError(f"Airtest connection failed: {e}") from e
        log("  ✓ Airtest session established")
        log("  ④ Establish uiautomator2 connection (XPath)…")
        self._u2 = self._connect_u2(target)
        log("  ✓ u2 session established")
        self._tune_u2_http_timeout()
        log("  ⑤ Verify Airtest connection (display_info)…")
        self._info = self._verify_display(log)
        self._serial = serial
        self._addr = target
        return self

    def disconnect(self) -> None:
        self._airtest = None
        self._u2 = None
        self._info = {}

    def is_alive(self) -> bool:
        """快速探测双栈响应（recovery 语义）。"""
        if self._u2 is None or self._airtest is None:
            return False
        try:
            _ = self._u2.info
        except Exception:
            return False
        try:
            _ = self._airtest.display_info
        except Exception:
            return False
        return True

    def reconnect(self) -> bool:
        """重建双栈连接（recovery 语义）。失败抛 EngineConnectError。"""
        if not self._addr:
            return False
        try:
            self.connect(self._serial, self._addr)
            return True
        except EngineConnectError:
            raise

    # ── 感知（标准化输出）──

    def screenshot(self) -> bytes:
        """Airtest snapshot（BGR numpy）→ JPEG bytes。"""
        arr = self._airtest.snapshot()
        img = Image.fromarray(arr[..., ::-1])
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=55, optimize=True)
        return buf.getvalue()

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        arr = self._airtest.snapshot(quality=quality)
        img = Image.fromarray(arr[..., ::-1])
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_h = max(1, int(img.height * ratio))
            img = img.resize((max_width, new_h))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def screenshot_file(self, path: str) -> None:
        arr = self._airtest.snapshot()
        Image.fromarray(arr[..., ::-1]).save(path)

    def dump_hierarchy(self) -> list[Node]:
        """u2 XML dump（3 层 fallback）→ algorithms.hierarchy 解析 → Node 列表。"""
        raw = None
        last_error = None
        try:
            raw = self._u2.dump_hierarchy()
        except Exception as e:
            last_error = e
        if raw is None:
            try:
                raw = self._u2.dump_hierarchy(compressed=False)
            except Exception as e:
                last_error = last_error or e
        if raw is None:
            try:
                raw = self._u2.dump_hierarchy(compressed=False, pretty=True)
            except Exception as e:
                last_error = last_error or e
        if raw is None:
            raise RuntimeError(f"dump_hierarchy all strategies failed: {last_error}")
        return [_to_node(d) for d in parse_hierarchy_xml(raw)]

    def app_current(self) -> dict:
        return self._u2.app_current()

    # ── 操作原语（Airtest）──

    def click(self, x: int, y: int) -> None:
        self._airtest.touch((x, y))

    def long_click(self, x: int, y: int, duration: float = 0.8) -> None:
        self._airtest.touch((x, y), duration=duration)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self._airtest.swipe((x1, y1), (x2, y2), duration=duration)

    def input_text(self, text: str, clear_first: bool = True) -> None:
        if clear_first:
            try:
                self._airtest.shell("input keyevent KEYCODE_MOVE_END")
                self._airtest.shell("input keyevent KEYCODE_CLEAR")
                time.sleep(0.1)
            except Exception:
                logger.debug("Shell keyevent failed, continuing")
        try:
            self._airtest.text(text)
        except Exception:
            safe = text.replace(" ", "%s").replace("'", "\\'")
            self._airtest.shell(f"input text '{safe}'")

    def press_key(self, key: str) -> None:
        self._airtest.shell(f"input keyevent {key}")

    def shell(self, cmd: str) -> str:
        return self._airtest.shell(cmd)

    def start_app(self, pkg: str) -> None:
        self._airtest.start_app(pkg)

    def stop_app(self, pkg: str) -> None:
        self._airtest.stop_app(pkg)

    # ── XPath 能力（u2，capabilities.xpath_locate 门控）──

    def exists(self, xpath: str, timeout: float = 0) -> bool:
        try:
            if timeout > 0:
                return bool(self._u2.xpath(xpath).wait(timeout=timeout))
            return bool(self._u2.xpath(xpath).exists)
        except Exception:
            return False

    def get_text(self, xpath: str) -> str:
        try:
            el = self._u2.xpath(xpath).get()
            return el.attrib.get("text", "") if el is not None else ""
        except Exception:
            return ""

    def wait_toast(self, expected_text: str, timeout: float = 15) -> bool:
        """轮询 toast（u2 toast API + XPath 探测，移植自 adapter.wait_for_toast）。"""
        deadline = time.time() + timeout
        try:
            self._u2.toast.reset()
        except Exception:
            logger.debug("Toast reset failed, continuing")
        while time.time() < deadline:
            try:
                if self._u2.xpath(f'//*[@text="{expected_text}"]').exists:
                    return True
            except Exception:
                logger.debug("Toast xpath probe failed for %r, falling back", expected_text[:60])
            try:
                msg = self._u2.toast.get_message(0)
                if msg and expected_text in str(msg):
                    return True
            except Exception:
                logger.debug("Toast probe failed, continuing")
            time.sleep(0.3)
        return False

    # ── 静态辅助（设备管理链路复用）──

    @staticmethod
    def probe_u2(addr: str) -> None:
        """u2 连接 + info 验证（设备连接入口的轻量探活）。失败抛 EngineConnectError。"""
        try:
            d = u2.connect(addr)
            _ = d.info
        except Exception as e:
            raise EngineConnectError(str(e)) from e

    @staticmethod
    def fetch_device_info(addr: str) -> dict:
        """经 u2 采集设备元信息（productName/displayWidth/displayHeight/sdkInt…）。"""
        d = u2.connect(addr)
        return dict(d.info)
