from __future__ import annotations

import logging
import re
import time

from logging.handlers import RotatingFileHandler
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOG_DIR = _REPO_ROOT / "logs"
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 3
_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def logging_now_stamp() -> str:
    now = time.time()
    text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    millis = int((now - int(now)) * 1000)
    return f"{text},{millis:03d}"


def build_logger(name: str, path: Path) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger

    path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_FORMAT)

    file_handler = RotatingFileHandler(
        path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def safe_sku(value: str) -> str:
    text = str(value or "").strip() or "unknown"
    return re.sub(r"[^0-9A-Za-z_.-]", "_", text)


def capture_file_name(sku: str, port: int) -> str:
    return f"{safe_sku(sku)}_{int(port)}.log"


def capture_file_path(sku: str, port: int, directory: Path | None = None) -> Path:
    root = _LOG_DIR / "serial_logs" if directory is None else Path(directory)
    return root / capture_file_name(sku, port)


def uart_capture_logger(sku: str, port: int, *, directory: Path | None = None) -> logging.Logger:
    safe = safe_sku(sku)
    name = f"uart.{safe}.{int(port)}"
    path = capture_file_path(sku, port, directory)
    logger = logging.getLogger(name)
    files = [item for item in logger.handlers if isinstance(item, RotatingFileHandler)]
    if files and Path(files[0].baseFilename) == path.resolve():
        return logger
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    return build_logger(name, path)


backend_log = build_logger("backend", _LOG_DIR / "backend.log")
AGENT_EVENT_LOG_PATH = _LOG_DIR / "agents" / "agent_events.log"
"""智能体事件日志路径：中间件折叠后的模型与工具事件都追加到这里。"""
agent_event_log = build_logger("agent_event", AGENT_EVENT_LOG_PATH)
device_log = build_logger("device", _LOG_DIR / "device.log")
serial_log = build_logger("serial", _LOG_DIR / "serial.log")
