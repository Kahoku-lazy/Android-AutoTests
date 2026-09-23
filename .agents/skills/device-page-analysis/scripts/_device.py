"""独立设备取数 —— 不依赖平台代码（无 Django / 无 engines / 无 apps）。

设备发现走 adb，连接与取数走 uiautomator2 自身 API；本模块只产出「原始 XML 文本 + 截图文件」，
不解析、不落库、不碰平台任何模块。
"""

import subprocess

# u2 单操作 HTTP 超时上限（秒）：设备冻结时避免永久阻塞
U2_OP_TIMEOUT = 20


def list_devices() -> list:
    """adb devices -l → [{serial, state, wireless}]。"""
    try:
        out = subprocess.run(
            ["adb", "devices", "-l"], capture_output=True, text=True, timeout=10
        ).stdout
    except FileNotFoundError:
        raise SystemExit("找不到 adb：请确认已安装 Android platform-tools 并在 PATH 中")
    except subprocess.TimeoutExpired:
        raise SystemExit("adb devices 超时（10s）：请检查 adb server 与设备连接")

    devs = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        devs.append({"serial": serial, "state": state, "wireless": ":" in serial})
    return devs


def pick_serial(explicit: str = "") -> str:
    """选设备：显式指定优先；否则要求「恰好一台在线」，多于一台直接报错不猜。"""
    if explicit:
        return explicit
    online = [d for d in list_devices() if d["state"] == "device"]
    if not online:
        raise SystemExit("没有可用设备（adb devices 无 device 状态条目）；请先连接设备或显式指定 --serial")
    if len(online) > 1:
        raise SystemExit(
            "检测到多台在线设备，请用 --serial 指定其一：" + ", ".join(d["serial"] for d in online)
        )
    return online[0]["serial"]


def connect(serial: str):
    """建立 uiautomator2 连接并收紧 HTTP 超时。"""
    import uiautomator2 as u2

    try:
        import uiautomator2.base as _u2base

        _u2base.HTTP_TIMEOUT = U2_OP_TIMEOUT
    except Exception:
        pass
    try:
        d = u2.connect(serial)
    except Exception as e:
        raise SystemExit("uiautomator2 连接失败：%s" % e)
    try:
        d.settings["wait_timeout"] = U2_OP_TIMEOUT
    except Exception:
        pass
    return d


def resolution(d):
    """(width, height)；取不到返回 (0, 0)。"""
    try:
        info = d.info
        return int(info.get("displayWidth", 0) or 0), int(info.get("displayHeight", 0) or 0)
    except Exception:
        return 0, 0


def app_current(d) -> dict:
    try:
        return d.app_current() or {}
    except Exception:
        return {}


def screenshot_image(d):
    """取截图图像对象（PIL Image）；先截图后取层级，保证两者尽量同源。"""
    return d.screenshot()


def screenshot_file(d, path) -> None:
    screenshot_image(d).save(str(path))


def dump_raw_xml(d, pretty: bool = True) -> str:
    """层级原始 XML 文本（三层 fallback：不压缩且美化 / 不压缩 / 默认）。

    美化变体便于人工阅读与留证；失败时逐级退让，全部失败抛错，不返回假数据。
    """
    attempts = []
    if pretty:
        attempts.append({"compressed": False, "pretty": True})
    attempts.append({"compressed": False})
    attempts.append({})

    last = None
    for kw in attempts:
        try:
            raw = d.dump_hierarchy(**kw)
        except Exception as e:
            last = e
            continue
        if not raw:
            continue
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return raw
    raise RuntimeError("层级取数全部策略失败：%s" % last)
