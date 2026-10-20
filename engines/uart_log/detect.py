"""检测端口能否监听。只探测，不留下监听套接字。"""

from __future__ import annotations

import socket

from utils.logs import serial_log

from .params import PortParams


class PortDetector:
    """绑定前检查端口。失败时记可读错误，调用方不得把该端口标成正在监听。"""

    def available(self, params: PortParams) -> bool:
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
