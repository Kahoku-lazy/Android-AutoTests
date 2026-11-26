from __future__ import annotations

from pathlib import Path

from utils.logs import serial_log, uart_capture_logger


class CaptureWriter:
    def __init__(self, sku: str, port: int, directory: Path | None = None) -> None:
        self._logger = uart_capture_logger(sku, port, directory=directory)

    def write(self, text: str) -> bool:
        try:
            self._logger.info("%s", text)
        except Exception as exc:
            serial_log.error("uart capture write failed: %s", exc)
            return False
        return True
