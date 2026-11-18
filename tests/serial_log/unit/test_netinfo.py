"""utils.netinfo 本机 IP 探测三态：出站探测成功 / 回退主机名解析 / 全失败空串。

零真实网络：socket 全部用替身。
"""

from __future__ import annotations

import socket

import pytest

from utils import netinfo

pytestmark = [pytest.mark.unit]


class _FakeUdpSocket:
    """UDP 替身：connect 不发包，getsockname 返回预设地址。"""

    def __init__(self, result: str | None):
        self._result = result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def connect(self, target):
        if self._result is None:
            raise OSError("probe failed")

    def getsockname(self):
        return (self._result, 54321)


def test_probe_success(monkeypatch):
    monkeypatch.setattr(netinfo.socket, "socket", lambda *a, **k: _FakeUdpSocket("192.168.35.100"))
    assert netinfo.local_lan_ip() == "192.168.35.100"


def test_fallback_to_hostname(monkeypatch):
    monkeypatch.setattr(netinfo.socket, "socket", lambda *a, **k: _FakeUdpSocket(None))
    monkeypatch.setattr(netinfo.socket, "gethostname", lambda: "test-host")
    monkeypatch.setattr(netinfo.socket, "gethostbyname", lambda name: "192.168.35.7")
    assert netinfo.local_lan_ip() == "192.168.35.7"


def test_all_failed_returns_empty(monkeypatch):
    monkeypatch.setattr(netinfo.socket, "socket", lambda *a, **k: _FakeUdpSocket(None))
    monkeypatch.setattr(netinfo.socket, "gethostname", lambda: "test-host")

    def _raise(name):
        raise socket.gaierror("no resolve")

    monkeypatch.setattr(netinfo.socket, "gethostbyname", _raise)
    assert netinfo.local_lan_ip() == ""


def test_loopback_is_not_lan_ip(monkeypatch):
    monkeypatch.setattr(netinfo.socket, "socket", lambda *a, **k: _FakeUdpSocket("127.0.0.1"))
    monkeypatch.setattr(netinfo.socket, "gethostname", lambda: "test-host")
    monkeypatch.setattr(netinfo.socket, "gethostbyname", lambda name: "127.0.1.1")
    assert netinfo.local_lan_ip() == ""
