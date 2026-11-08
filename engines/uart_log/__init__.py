"""
文件名: ➡ __init__.py 🏁
路径: ➡ engines/uart_log/__init__.py 🏁
模块功能：➡ 设备端口日志：检测、接收、写入、开关 🏁
Python 调试：➡ python -m engines.uart_log 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. detect / params / receiver / writer / switch: 端口探测、参数、接收线程、落盘与开关
2. 对上由设备日志与任务侧按需打开端口监听
🏁
关联模块：➡
1. engines.uart_log.detect / params / receiver / writer / switch: 子模块
🏁
测试：➡
1. 暂无专门单测；见 AGENTS / 设备日志相关集成
🏁
"""

from .detect import PortDetector
from .params import PortParams
from .receiver import PortReceiver
from .switch import MAX_PORTS, PortSwitch, get_port_switch, reset_port_switch
from .writer import CaptureWriter

__all__ = [
    "MAX_PORTS",
    "CaptureWriter",
    "PortDetector",
    "PortParams",
    "PortReceiver",
    "PortSwitch",
    "get_port_switch",
    "reset_port_switch",
]
