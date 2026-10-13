"""Android 设备实现（uiautomator2 单栈）—— 三个类：设备连接 / 设备信息查询 / 设备控制。

方法名 MUST 与 `engines/device/action.py` 的三份方法名契约一致（例如图片点击一律 `click_img`），
别名一律不合法；三个类都继承对应契约，缺方法无法实例化。

层纯度：只依赖 uiautomator2 与 `engines.device.action` 的契约；不 import `apps.*` / `django` /
`algorithms.*`（层级只给原始 XML，解析归算法层）。

错误语义：连接类失败抛 EngineConnectError（技术语义，由上层转业务文案）。
"""

from __future__ import annotations

import base64
import io
import logging
import subprocess
import time

import uiautomator2 as u2

from engines.device.action import DeviceConnection, DeviceControl, DeviceInfo
from engines.device.base import EngineConnectError

logger = logging.getLogger(__name__)

# u2 单操作 HTTP 超时上限（秒）。u2 默认 HTTP_TIMEOUT=300，设备冻结会永久阻塞。
U2_OP_TIMEOUT = 20

_CONNECTED_KEYWORDS = ("connected", "already", "已连接", "已经连接", "成功")


class AndroidConnection(DeviceConnection):
    """设备连接类 —— 无线 / USB 双栈连接、存活探测与重连。"""

    def __init__(self) -> None:
        self.u2 = None
        self.serial = ""
        self.addr = ""
        self.device_info: dict = {}

    # ── 连接细节 ──

    def _adb_connect(self, target: str, log=None) -> None:
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
            if not any(kw in output.lower() for kw in _CONNECTED_KEYWORDS):
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
            self.u2.settings["wait_timeout"] = U2_OP_TIMEOUT
        except Exception:
            logger.debug("u2 HTTP timeout tuning failed, continuing")

    def _verify_display(self, log=None) -> dict:
        """u2 info 验证连接，失败抛 EngineConnectError（ATX 消息映射）。"""
        try:
            info = dict(self.u2.info)
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

    # ── 契约方法 ──

    def connect(self, serial: str, addr: str = "", on_log=None) -> None:
        """建立双栈连接并验证。target = addr（无线连接地址）或 serial（USB）。"""

        def log(msg: str):
            if on_log:
                on_log(msg)

        target = addr or serial
        if ":" in target:
            self._adb_connect(target, log)
        else:
            log("  ② USB device, skip adb connect")
        log("  ③ Establish uiautomator2 connection…")
        self.u2 = self._connect_u2(target)
        log("  ✓ u2 session established")
        self._tune_u2_http_timeout()
        log("  ④ Verify u2 connection (info)…")
        self.device_info = self._verify_display(log)
        self.serial = serial
        self.addr = target

    def disconnect(self) -> None:
        self.u2 = None
        self.device_info = {}

    def is_alive(self) -> bool:
        if self.u2 is None:
            return False
        try:
            _ = self.u2.info
        except Exception:
            return False
        return True

    def reconnect(self) -> bool:
        if not self.addr:
            return False
        self.connect(self.serial, self.addr)
        return True


class AndroidInfo(DeviceInfo):
    """设备信息查询类 —— 分辨率 / 前台应用 / 包名 / 已连接设备 / 层级 XML / shell 取数。"""

    def __init__(self, connection: AndroidConnection) -> None:
        self._connection = connection

    @property
    def _u2(self):
        return self._connection.u2

    def screen_size(self) -> tuple[int, int]:
        info = self._u2.info
        w = int(info.get("displayWidth", 0) or 0)
        h = int(info.get("displayHeight", 0) or 0)
        return w, h

    def current_app(self) -> dict:
        return self._u2.app_current()

    def packages(self, query: str = "") -> list[str]:
        raw = self.shell("pm list packages")
        result: list[str] = []
        for line in (raw or "").splitlines():
            item = line.strip()
            if not item.startswith("package:"):
                continue
            pkg = item[len("package:") :].strip()
            if pkg and (not query or query.lower() in pkg.lower()):
                result.append(pkg)
        return result

    def connected_devices(self) -> list[str]:
        """当前已连接的设备序列号列表（主机侧 adb 枚举，不依赖任何一台已接连接）。"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
        except Exception:
            logger.debug("adb devices failed, returning empty list")
            return []
        serials: list[str] = []
        for line in (result.stdout or "").splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                serials.append(parts[0])
        return serials

    def hierarchy_xml(self) -> str:
        """层级原始 XML 文本（3 层 fallback：默认 / 不压缩 / 不压缩且美化）。"""
        last_error = None
        for kwargs in ({}, {"compressed": False}, {"compressed": False, "pretty": True}):
            try:
                raw = self._u2.dump_hierarchy(**kwargs)
            except Exception as e:
                last_error = e
                continue
            if not raw:
                continue
            return raw.decode("utf-8") if isinstance(raw, bytes) else raw
        raise RuntimeError(f"dump_hierarchy all strategies failed: {last_error}")

    def shell(self, cmd: str) -> str:
        """命令标准输出（取 u2 原生响应的 output，不泄漏原生对象）。"""
        return self._u2.shell(cmd).output


class AndroidControl(DeviceControl):
    """设备控制类 —— 点击 / 长按 / 滑动 / 拖动 / 输入 / 按键 / 截图 / 应用启停（+ XPath 与 Toast 辅助）。"""

    def __init__(self, connection: AndroidConnection) -> None:
        self._connection = connection

    @property
    def _u2(self):
        return self._connection.u2

    # ── 点击 ──

    def click_coord(self, x: int, y: int) -> None:
        self._u2.click(int(x), int(y))

    def click_element(self, by: str, value: str, index: int = 0) -> bool:
        xpath = self._xpath_of(by, value)
        if not xpath:
            return False
        return self.click_xpath(xpath, index=int(index))

    def click_img(self, nx: float, ny: float) -> None:
        """按图像定位点击（归一化坐标 → 像素坐标换算在实现内完成）。"""
        w, h = self.screen_size()
        self._u2.click(int(float(nx) * w), int(float(ny) * h))

    # ── 长按 ──

    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        self._u2.long_click(int(x), int(y), duration=float(duration))

    def long_click_element(
        self, by: str, value: str, index: int = 0, duration: float = 0.8
    ) -> bool:
        xpath = self._xpath_of(by, value)
        if not xpath:
            return False
        return self.long_click_xpath(xpath, index=int(index), duration=float(duration))

    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> None:
        w, h = self.screen_size()
        self._u2.long_click(int(float(nx) * w), int(float(ny) * h), duration=float(duration))

    # ── 滑动 / 拖动 ──

    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        w, h = self.screen_size()
        cx, cy = w // 2, h // 2
        span = int(distance or 500)
        dirs = {
            "up": (cx, h * 3 // 4, cx, h * 3 // 4 - span),
            "down": (cx, h // 4, cx, h // 4 + span),
            "left": (w * 3 // 4, cy, w * 3 // 4 - span, cy),
            "right": (w // 4, cy, w // 4 + span, cy),
        }
        x1, y1, x2, y2 = dirs.get(str(direction or "up"), (cx, h * 3 // 4, cx, h // 4))
        self.swipe_coord(x1, y1, x2, y2)

    def swipe_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self._u2.swipe(int(x1), int(y1), int(x2), int(y2), duration=float(duration))

    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        w, h = self.screen_size()
        self.swipe_coord(
            int(float(nx1) * w),
            int(float(ny1) * h),
            int(float(nx2) * w),
            int(float(ny2) * h),
        )

    # ── 输入 / 按键 ──

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

    def press_key(self, key: str = "back") -> None:
        self._u2.shell(f"input keyevent {str(key or 'back').upper()}")

    # ── 截图 ──

    def screenshot(self) -> bytes:
        img = self._u2.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=55, optimize=True)
        return buf.getvalue()

    def screenshot_raw(self) -> bytes:
        """取原始帧（无损 PNG 字节）。"""
        img = self._u2.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def screenshot_b64(self, quality: int = 55, max_width: int = 0) -> str:
        img = self._u2.screenshot()
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, max(1, int(img.height * ratio))))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def screenshot_file(self, path: str) -> None:
        self._u2.screenshot().save(path)

    # ── 应用 ──

    def app_start(self, package: str) -> None:
        self._u2.app_start(str(package))

    def app_stop(self, package: str) -> None:
        self._u2.app_stop(str(package))

    # ── 元素定位辅助（XPath / 文本，供契约的 click_element / long_click_element 使用）──

    @staticmethod
    def _xpath_of(by: str, value: str) -> str:
        """定位方式 → xpath：xpath 原样、id → resource-id、text → text。"""
        kind = str(by or "xpath").strip().lower()
        text = str(value or "")
        if not text:
            return ""
        if kind == "xpath":
            return text
        if kind == "id":
            return f'//*[@resource-id="{text}"]'
        if kind == "text":
            return f'//*[@text="{text}"]'
        return ""

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

    def get_text_matches(self, xpath: str, index: int = 0) -> dict:
        """列出 xpath 命中的全部元素。index 是点击时用的下标，text 取该下标的文本。"""
        hits: list[dict] = []
        try:
            elements = self._u2.xpath(xpath).all()
        except Exception:
            elements = []
        for nth, el in enumerate(elements or []):
            attrib = getattr(el, "attrib", None) or {}
            hits.append(
                {
                    "index": nth,
                    "text": str(attrib.get("text") or ""),
                    "bounds": str(attrib.get("bounds") or ""),
                }
            )
        chosen = int(index or 0)
        text = hits[chosen]["text"] if 0 <= chosen < len(hits) else ""
        return {"text": text, "index": chosen, "count": len(hits), "items": hits}

    def click_xpath(self, xpath: str, index: int = 0) -> bool:
        try:
            elements = self._u2.xpath(xpath).all()
            if len(elements) > int(index):
                elements[int(index)].click()
                return True
            return False
        except Exception:
            return False

    def long_click_xpath(self, xpath: str, index: int = 0, duration: float = 0.8) -> bool:
        try:
            elements = self._u2.xpath(xpath).all()
            if len(elements) > int(index):
                elements[int(index)].long_click(duration=float(duration))
                return True
            return False
        except Exception:
            return False

    def count_element(self, by: str, value: str) -> int:
        """元素命中数量（0 = 未命中）。"""
        xpath = self._xpath_of(by, value)
        if not xpath:
            return 0
        try:
            return len(self._u2.xpath(xpath).all())
        except Exception:
            return 0

    # ── Toast 辅助 ──

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

    def wait_toast(self, expected_text: str, timeout: float = 15) -> bool:
        deadline = time.time() + float(timeout)
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

    def screen_size(self) -> tuple[int, int]:
        info = self._u2.info
        return int(info.get("displayWidth", 0) or 0), int(info.get("displayHeight", 0) or 0)
