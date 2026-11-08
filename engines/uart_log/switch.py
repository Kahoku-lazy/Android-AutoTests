"""
文件名: ➡ switch.py 🏁
路径: ➡ engines/uart_log/switch.py 🏁
模块功能：➡ 按端口开关监听（同时打开最多 10 个） 🏁
Python 调试：➡ python -m engines.uart_log.switch 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. PortSwitch: open/close/close_all 与 listening/reserved 查询
2. get_port_switch / reset_port_switch: 进程内单例取用与重置
🏁
关联模块：➡
1. engines.uart_log.params: PortParams
2. engines.uart_log.receiver: PortReceiver
3. utils.logs: serial_log
🏁
测试：➡
1. 暂无专门单测
🏁
"""

from __future__ import annotations

import threading

from utils.logs import serial_log

from .params import PortParams
from .receiver import PortReceiver

MAX_PORTS = 10

_SWITCH: PortSwitch | None = None
_SWITCH_LOCK = threading.Lock()


class PortSwitch:
    """持有每个端口的接收线程。重复打开同一端口不会再起一份监听。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ports: dict[int, PortReceiver] = {}

    def open(self, params: PortParams) -> bool:
        """打开并监听指定端口；已在监听则直接成功。同时打开上限 10。"""
        port = int(params.port)
        with self._lock:
            self._drop_dead()
            current = self._ports.get(port)
            if current is not None and current.is_alive():
                return True
            if len(self._ports) >= MAX_PORTS:
                serial_log.error(
                    "uart listen cap %s reached; port %s refused",
                    MAX_PORTS,
                    port,
                )
                return False
            receiver = PortReceiver(params)
            self._ports[port] = receiver
            receiver.start()
            return True

    def close(self, port: int) -> bool:
        """关闭指定端口的接收线程。"""
        with self._lock:
            receiver = self._ports.pop(int(port), None)
        if receiver is None:
            return False
        receiver.stop()
        return True

    def close_all(self) -> None:
        """关闭全部已登记端口。"""
        for port in list(self._ports):
            self.close(port)

    def is_listening(self, port: int) -> bool:
        """端口是否正在监听。"""
        with self._lock:
            receiver = self._ports.get(int(port))
            return receiver is not None and receiver.listening

    def is_reserved(self, port: int) -> bool:
        """端口是否仍被接收线程占用（含未完成清理）。"""
        with self._lock:
            self._drop_dead()
            receiver = self._ports.get(int(port))
            return receiver is not None and receiver.is_alive()

    def listening_ports(self) -> list[int]:
        """当前正在监听的端口列表（排序）。"""
        with self._lock:
            return sorted(port for port, receiver in self._ports.items() if receiver.listening)

    def reserved_count(self) -> int:
        """当前登记中的端口数量。"""
        with self._lock:
            self._drop_dead()
            return len(self._ports)

    def _drop_dead(self) -> None:
        dead = [
            port
            for port, receiver in self._ports.items()
            if not receiver.is_alive() and not receiver.listening
        ]
        for port in dead:
            self._ports.pop(port, None)


def get_port_switch() -> PortSwitch:
    """进程内一份开关。"""
    global _SWITCH
    with _SWITCH_LOCK:
        if _SWITCH is None:
            _SWITCH = PortSwitch()
        return _SWITCH


def reset_port_switch() -> None:
    """关掉全部分监听并丢掉单例。测试和总开关关闭时使用。"""
    global _SWITCH
    with _SWITCH_LOCK:
        if _SWITCH is not None:
            _SWITCH.close_all()
            _SWITCH = None
