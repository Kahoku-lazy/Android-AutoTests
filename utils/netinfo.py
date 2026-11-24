"""
模块功能：➡️ 本机网络信息：探测出站局域网 IP（UDP connect，不发包） 🏁
Python 调试：➡️ python -m utils.netinfo 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/serial_log/unit/test_netinfo.py: 局域网 IP 探测与主机名回退
🏁
"""

from __future__ import annotations

import socket

__all__ = ["local_lan_ip"]

# 仅用于让内核选出出站网卡，UDP connect 不发送任何报文。
_PROBE_TARGET = ("8.8.8.8", 80)


def local_lan_ip() -> str:
    """取本机出站局域网 IP；探测不到时返回空串。

    Returns:
        IPv4 地址字符串；探测失败或只得到回环地址时返回空串，
        由调用方给出可读空态说明，不抛错。
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(_PROBE_TARGET)
            ip = str(probe.getsockname()[0])
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        return ""
    return "" if not ip or ip.startswith("127.") else ip
