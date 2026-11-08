"""
文件名: ➡ detect.py 🏁
路径: ➡ engines/uart_log/detect.py 🏁
模块功能：➡ 检测端口能否监听（只探测，不留下监听套接字） 🏁
Python 调试：➡ python -m engines.uart_log.detect 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. PortDetector.available: 判断端口是否可监听；已被占用则返回 False
🏁
关联模块：➡
1. engines.uart_log.params: PortParams
2. utils.logs: serial_log
🏁
测试：➡
1. 暂无专门单测
🏁
"""

from __future__ import annotations

import socket

from utils.logs import serial_log

from .params import PortParams


class PortDetector:
    """绑定前检查端口。失败时记可读错误，调用方不得把该端口标成正在监听。"""

    def available(self, params: PortParams) -> bool:
        """探测端口是否可监听；已被占用则记日志并返回 False。"""
        if _port_in_use(params.host, int(params.port)):
            serial_log.error(
                "uart port %s already in use; not listening",
                int(params.port),
            )
            return False
        try:
            self._try_bind(params)
        except OSError as exc:
            serial_log.error(
                "uart port %s bind failed: %s",
                int(params.port),
                exc,
            )
            return False
        return True

    def _try_bind(self, params: PortParams) -> None:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind((params.host, int(params.port)))
        finally:
            probe.close()


def _port_in_use(host: str, port: int) -> bool:
    probe_host = "127.0.0.1" if host in ("", "0.0.0.0") else host
    try:
        with socket.create_connection((probe_host, port), timeout=0.5):
            return True
    except OSError:
        return False
