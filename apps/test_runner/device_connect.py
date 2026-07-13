"""执行前设备在线/连接检查 — 对齐设备池连接逻辑（含 WiFi adb connect）。"""

from __future__ import annotations

import asyncio
import subprocess
from typing import Callable, Optional

import uiautomator2 as u2

# adb connect(10s) + u2.connect(15s) + device.info 余量
DEVICE_CHECK_TIMEOUT = 30

# 单次 u2 HTTP 操作超时上界(秒)。u2 默认 HTTP_TIMEOUT=300,设备卡死时单次
# 操作会阻塞 5 分钟,导致执行线程无法到达 adapter.stopped() 检查点、停止按钮失效。
# 降到 20s 使卡死操作快速失败 → 触发已有的 u2 崩溃重连/停止检查。
U2_OP_TIMEOUT = 20


class DeviceCheckError(Exception):
    """设备检查未通过。"""


def check_and_connect(serial: str, on_log: Optional[Callable[[str], None]] = None) -> u2.Device:
    """同步：检查设备池状态 → ADB（WiFi）→ u2 → device.info。

    注意：此函数在线程池中运行，on_log 不得阻塞事件循环（仅收集字符串）。

    Args:
        serial: 设备 serial（USB 或 host:port）
        on_log: 可选日志回调，用于记录检查过程

    Returns:
        已验证的 uiautomator2 Device

    Raises:
        DeviceCheckError: 任一步骤失败
    """
    from apps.device_pool.models import Device as PoolDevice

    def log(msg: str):
        if on_log:
            on_log(msg)

    log(f"🔍 执行前检查设备: {serial}")

    log("  ① 查询设备池状态…")
    try:
        dev = PoolDevice.objects.get(serial=serial)
    except PoolDevice.DoesNotExist:
        raise DeviceCheckError(f"设备 {serial} 未在设备池中注册，请先在设备管理中添加") from None

    if dev.status in ("OFFLINE", "DISCONNECTED"):
        raise DeviceCheckError(
            f"设备状态为 {dev.status}，请先在设备管理中连接并确认在线"
        )

    conn = dev.connection_type or ("WIFI" if ":" in serial else "USB")
    name = dev.name or dev.model or serial
    log(f"  ✓ 设备池: {dev.status} · {conn} · {name}")

    if ":" in serial:
        log(f"  ② 无线 ADB 连接: adb connect {serial}")
        try:
            result = subprocess.run(
                ["adb", "connect", serial],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                log(f"  → {output}")
            if "connected" not in output.lower() and "already" not in output.lower():
                raise DeviceCheckError("ADB 连接失败，请检查 WiFi 网络与设备端口")
        except subprocess.TimeoutExpired:
            raise DeviceCheckError("ADB connect 超时 (10s)，请检查网络") from None
        log("  ✓ ADB 已就绪")
    else:
        log("  ② USB 设备，跳过 adb connect")

    log("  ③ 建立 uiautomator2 连接…")
    try:
        device = u2.connect(serial)
    except Exception as e:
        raise DeviceCheckError(f"u2.connect 失败: {e}") from e
    log("  ✓ u2 会话已建立")

    # 限制单次 u2 操作超时,避免设备卡死时永久阻塞(默认 HTTP_TIMEOUT=300s)。
    # base.py 的 jsonrpc 包装器每次调用读取该模块全局,降它即对后续所有操作生效。
    try:
        import uiautomator2.base as _u2base

        _u2base.HTTP_TIMEOUT = U2_OP_TIMEOUT
    except Exception:
        pass
    try:
        device.settings["wait_timeout"] = U2_OP_TIMEOUT
    except Exception:
        pass

    log("  ④ 验证 ATX 服务 (device.info)…")
    try:
        info = device.info
        w = info.get("displayWidth", "?")
        h = info.get("displayHeight", "?")
        product = info.get("productName") or info.get("model", "")
        extra = f" · {product}" if product else ""
        log(f"  ✓ 连接验证通过 · 分辨率 {w}x{h}{extra}")
    except Exception as e:
        msg = str(e)
        if "atx-agent" in msg.lower() or "offline" in msg.lower():
            raise DeviceCheckError(
                "ATX Agent 未运行，请在设备端启动 uiautomator2 服务"
            ) from e
        raise DeviceCheckError(f"device.info 验证失败: {e}") from e

    log("✅ 设备检查通过，开始执行测试")
    return device


async def _flush_check_logs(run_id: str, callbacks, messages: list[str]):
    """检查完成后批量推送日志，避免线程池内同步 await 导致事件循环死锁。"""
    for msg in messages:
        await callbacks.on_log(run_id, msg)


async def check_and_connect_async(
    serial: str,
    run_id: str,
    callbacks,
    executor,
    timeout: float = DEVICE_CHECK_TIMEOUT,
) -> u2.Device:
    """异步包装：在线程池中执行检查，完成后将日志批量推送到 WebSocket。"""
    loop = asyncio.get_event_loop()
    collected: list[str] = []

    def do_check():
        return check_and_connect(serial, on_log=collected.append)

    err: Optional[BaseException] = None
    device = None
    try:
        device = await asyncio.wait_for(
            loop.run_in_executor(executor, do_check),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        err = DeviceCheckError(f"设备检查超时 ({int(timeout)}s)，请确认 ADB/u2 可用")
    except DeviceCheckError as e:
        err = e
    except Exception as e:
        err = DeviceCheckError(str(e))

    await _flush_check_logs(run_id, callbacks, collected)

    if err is not None:
        raise err
    return device
