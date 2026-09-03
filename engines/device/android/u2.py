"""U2Engine — uiautomator2 单栈引擎（L1c 实现，契约见 engines/device/base.py）。

uiautomator2（u2.Device）负责全部设备能力：screenshot/click/swipe/app 生命周期/shell/
文本输入/dump_hierarchy/XPath/toast。
能力声明：xpath_locate=True / toast_wait=True / ocr=False。

错误语义：连接类失败抛 EngineConnectError（技术语义，由上层转业务文案）。

⚠️ 契约出入：本模块 import `algorithms.hierarchy`（纯解析函数，零 apps 依赖），
总纲 §三 字面禁令为"engines ❌ algorithms.*"——按"纯函数复用优于内联"执行，待评审裁决。
"""

import base64
import io
import logging
import subprocess
import time

import uiautomator2 as u2

from algorithms.hierarchy import parse_hierarchy_xml
from engines.device.base import EngineCapabilities, EngineConnectError
from models.ui_nodes import Node

logger = logging.getLogger(__name__)

# u2 单操作 HTTP 超时上限（秒）。u2 默认 HTTP_TIMEOUT=300，设备冻结会永久阻塞。
U2_OP_TIMEOUT = 20

_CONNECTED_KEYWORDS = ("connected", "already", "已连接", "已经连接", "成功")


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


class U2Engine:
    """uiautomator2 单栈引擎 — 实现 engines/device/base.py::UiEngine 协议。"""

    capabilities = EngineCapabilities(xpath_locate=True, toast_wait=True, ocr=False)

    def __init__(self):
        self._u2 = None
        self._serial = ""
        self._addr = ""
        self._info: dict = {}

    # ── 原始句柄（过渡期：DeviceConnection 兼容壳与 pool 属性经此取值）──

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
        """u2 info 验证连接，失败抛 EngineConnectError（ATX 消息映射）。"""
        try:
            info = dict(self._u2.info)
        except Exception as e:
            msg = str(e)
            if "atx-agent" in msg.lower() or "offline" in msg.lower():
                raise EngineConnectError(
                    "ATX Agent not running. Start uiautomator2 service on device."
                ) from e
            raise EngineConnectError(f"Device verification failed: {e}") from e
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
        log("  ③ Establish uiautomator2 connection…")
        self._u2 = self._connect_u2(target)
        log("  ✓ u2 session established")
        self._tune_u2_http_timeout()
        log("  ④ Verify u2 connection (info)…")
        self._info = self._verify_display(log)
        self._serial = serial
        self._addr = target
        return self

    def disconnect(self) -> None:
        self._u2 = None
        self._info = {}

    def is_alive(self) -> bool:
        """快速探测双栈响应（recovery 语义）。"""
        if self._u2 is None:
            return False
        try:
            _ = self._u2.info
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
        """u2 截图（PIL RGB Image）→ JPEG bytes。"""
        img = self._u2.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=55, optimize=True)
        return buf.getvalue()

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        img = self._u2.screenshot()
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_h = max(1, int(img.height * ratio))
            img = img.resize((max_width, new_h))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def screenshot_file(self, path: str) -> None:
        self._u2.screenshot().save(path)

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

    # ── 操作原语（u2）──

    def click(self, x: int, y: int) -> None:
        self._u2.click(x, y)

    def long_click(self, x: int, y: int, duration: float = 0.8) -> None:
        self._u2.long_click(x, y, duration=duration)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self._u2.swipe(x1, y1, x2, y2, duration=duration)

    def swipe_direction(self, direction: str = "up", distance: int = 500) -> None:
        """按方向滑动（方向→起终点坐标换算在引擎内完成）。"""
        w, h = self.get_resolution()
        cx, cy = w // 2, h // 2
        dirs = {
            "up": (cx, h * 3 // 4, cx, h * 3 // 4 - distance),
            "down": (cx, h // 4, cx, h // 4 + distance),
            "left": (w * 3 // 4, cy, w * 3 // 4 - distance, cy),
            "right": (w // 4, cy, w // 4 + distance, cy),
        }
        x1, y1, x2, y2 = dirs.get(direction, (cx, h * 3 // 4, cx, h // 4))
        self.swipe(x1, y1, x2, y2)

    def click_ratio(self, nx: float, ny: float) -> None:
        """按归一化坐标点击（0~1 → 像素坐标换算在引擎内）。"""
        w, h = self.get_resolution()
        x = int(float(nx) * w)
        y = int(float(ny) * h)
        self.click(x, y)

    def drag_ratio(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        """按归一化坐标拖动（0~1 → 像素坐标换算在引擎内）。"""
        w, h = self.get_resolution()
        x1 = int(float(nx1) * w)
        y1 = int(float(ny1) * h)
        x2 = int(float(nx2) * w)
        y2 = int(float(ny2) * h)
        self.swipe(x1, y1, x2, y2, duration=0.5)

    def input_text(self, text: str, clear_first: bool = True) -> None:
        if clear_first:
            try:
                self._u2.shell("input keyevent KEYCODE_MOVE_END")
                self._u2.shell("input keyevent KEYCODE_CLEAR")
                time.sleep(0.1)
            except Exception:
                logger.debug("Shell keyevent failed, continuing")
        try:
            self._u2.send_keys(text)
        except Exception:
            safe = text.replace(" ", "%s").replace("'", "\\'")
            self._u2.shell(f"input text '{safe}'")

    def press_key(self, key: str) -> None:
        self._u2.shell(f"input keyevent {key}")

    def shell(self, cmd: str) -> str:
        return self._u2.shell(cmd)

    def start_app(self, pkg: str) -> None:
        self._u2.app_start(pkg)

    def stop_app(self, pkg: str) -> None:
        self._u2.app_stop(pkg)

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

    def click_xpath(self, xpath: str, index: int = 0) -> bool:
        try:
            elements = self._u2.xpath(xpath).all()
            if len(elements) > index:
                elements[index].click()
                return True
            return False
        except Exception:
            return False

    def long_click_xpath(self, xpath: str, index: int = 0, duration: float = 0.8) -> bool:
        try:
            elements = self._u2.xpath(xpath).all()
            if len(elements) > index:
                elements[index].long_click(duration=duration)
                return True
            return False
        except Exception:
            return False

    def get_toast_message(self) -> str:
        try:
            msg = self._u2.toast.get_message(0)
            return str(msg) if msg else ""
        except Exception:
            return ""

    def reset_toast(self) -> None:
        try:
            self._u2.toast.reset()
        except Exception:
            logger.debug("Toast reset failed, continuing")

    def get_resolution(self) -> tuple[int, int]:
        info = self._u2.info
        w = int(info.get("displayWidth", 0) or 0)
        h = int(info.get("displayHeight", 0) or 0)
        return w, h

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
