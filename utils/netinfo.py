from __future__ import annotations

import socket

__all__ = ["local_lan_ip"]

_PROBE_TARGET = ("8.8.8.8", 80)


def local_lan_ip() -> str:
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
