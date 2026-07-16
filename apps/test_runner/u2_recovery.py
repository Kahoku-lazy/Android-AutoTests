"""uiautomator2 崩溃检测、重连与健康检查。"""

import time

# 单条用例（每轮迭代）u2 崩溃后最多重试次数
U2_CASE_RETRY_MAX = 3
# 重连间隔（秒）
U2_RECONNECT_INTERVAL = 2


def is_u2_crash(exc: BaseException) -> bool:
    """判断异常是否由 u2/ADB 连接崩溃或超时引起。"""
    if isinstance(exc, ConnectionError):
        return True
    # u2 3.x 的 HTTPTimeoutError/DeviceError 等按类型名兜底识别(不依赖 str 匹配)
    if type(exc).__name__ in (
        "HTTPTimeoutError",
        "HTTPError",
        "ConnectError",
        "DeviceError",
        "SessionBrokenError",
    ):
        return True
    msg = str(exc).lower()
    keywords = (
        "quit",
        "broken",
        "disconnect",
        "connection",
        "uiautomator",
        "adb",
        "socket",
        "remote end closed",
        "device offline",
        "cannot connect",
        "timeout",
        "timed out",
        "http request",
    )
    return any(k in msg for k in keywords)


def check_u2_alive(device) -> bool:
    """快速探测 u2 服务是否可用。"""
    if device is None:
        return False
    try:
        device.info
        return True
    except Exception:
        return False


def reconnect_u2(serial: str):
    """重新建立 u2 连接。失败则抛出异常。"""
    import uiautomator2 as u2

    return u2.connect(serial)


def wait_and_reconnect(serial: str, wait_seconds: float = U2_RECONNECT_INTERVAL):
    """等待后重连，给 ATX agent 恢复时间。"""
    time.sleep(wait_seconds)
    return reconnect_u2(serial)
