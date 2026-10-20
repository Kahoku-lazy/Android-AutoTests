"""
python -m 调试路径: utils.logs

本模块的业务功能如下：
1. build_logger: 用 logging 建一个记录器，文件 10MB 轮转、保留 3 个备份，警告及以上同时打到控制台。
2. logging_now_stamp: 用 time 取本地当前时间，格式与 logging 的 asctime 一致。
3. backend_log / agent_event_log / device_log / serial_log: 四个已经建好的记录器。
4. uart_capture_logger: 按 SKU 与端口把抓到的串口日志写入 logs/serial_logs/{SKU}_{端口}.log。
"""

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
    """本地当前时间，格式与 logging 的 asctime 相同：`YYYY-MM-DD HH:MM:SS,mmm`。"""
    now = time.time()
    text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    millis = int((now - int(now)) * 1000)
    return f"{text},{millis:03d}"


def build_logger(name: str, path: Path) -> logging.Logger:
    """创建一个记录器：DEBUG 写入文件，WARNING 及以上同时打到控制台。

    Args:
        name: 记录器名称，出现在每一行里。
        path: 日志文件路径。
    """
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
    """SKU 写入文件名和记录器名之前去掉路径字符。"""
    text = str(value or "").strip() or "unknown"
    return re.sub(r"[^0-9A-Za-z_.-]", "_", text)


def capture_file_name(sku: str, port: int) -> str:
    """抓取日志文件名：`{SKU}_{端口}.log`。"""
    return f"{safe_sku(sku)}_{int(port)}.log"


def capture_file_path(sku: str, port: int, directory: Path | None = None) -> Path:
    """抓取日志路径。缺省目录是 `logs/serial_logs/`。"""
    root = _LOG_DIR / "serial_logs" if directory is None else Path(directory)
    return root / capture_file_name(sku, port)


def uart_capture_logger(sku: str, port: int, *, directory: Path | None = None) -> logging.Logger:
    """按 SKU 与端口取得抓取记录器。名称 `uart.{SKU}.{端口}`，格式与轮转跟 `build_logger` 相同。

    同一个名称如果已经绑了别的路径，先卸掉再按这次的路径重建，避免测试和换目录后仍写进旧文件。
    """
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
agent_event_log = build_logger("agent_event", _LOG_DIR / "agents" / "agent_events.log")
device_log = build_logger("device", _LOG_DIR / "device.log")
serial_log = build_logger("serial", _LOG_DIR / "serial.log")
