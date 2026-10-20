"""把抓到的一行写入该端口的 logging 文件。"""

from __future__ import annotations

from pathlib import Path

from utils.logs import serial_log, uart_capture_logger


class CaptureWriter:
    """消息正文只放抓到的原文。写失败返回 False，不把异常抛给接收循环。"""

    def __init__(self, sku: str, port: int, directory: Path | None = None) -> None:
        self._logger = uart_capture_logger(sku, port, directory=directory)

    def write(self, text: str) -> bool:
        try:
            self._logger.info("%s", text)
        except Exception as exc:
            serial_log.error("uart capture write failed: %s", exc)
            return False
        return True
