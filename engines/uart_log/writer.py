"""
文件名: ➡ writer.py 🏁
路径: ➡ engines/uart_log/writer.py 🏁
模块功能：➡ 把抓到的一行写入该端口的 logging 文件 🏁
Python 调试：➡ python -m engines.uart_log.writer 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. CaptureWriter.write: 将一行文本写入该端口的 capture logger
🏁
关联模块：➡
1. utils.logs: uart_capture_logger / serial_log
🏁
测试：➡
1. 暂无专门单测
🏁
"""

from __future__ import annotations

from pathlib import Path

from utils.logs import serial_log, uart_capture_logger


class CaptureWriter:
    """消息正文只放抓到的原文。写失败返回 False，不把异常抛给接收循环。"""

    def __init__(self, sku: str, port: int, directory: Path | None = None) -> None:
        self._logger = uart_capture_logger(sku, port, directory=directory)

    def write(self, text: str) -> bool:
        """写入一行抓取文本；失败记日志并返回 False。"""
        try:
            self._logger.info("%s", text)
        except Exception as exc:
            serial_log.error("uart capture write failed: %s", exc)
            return False
        return True
